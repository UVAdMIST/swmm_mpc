import GPyOpt
import swmm_mpc as sm
import evaluate as ev
import numpy as np
from GPyOpt.methods import BayesianOptimization as BayOpt


def get_bounds(ctl_str_ids, nsteps):
    bounds = []
    for ctl in ctl_str_ids:
        var_num = 0
        for j in range(nsteps):
            ctl_type = ctl.split()[0]
            ctl_bounds = {}

            if ctl_type == 'WEIR' or ctl_type == 'ORIFICE':
                var_type = 'continuous'
            elif ctl_type == 'PUMP':
                var_type = 'discrete'

            ctl_bounds['name'] = 'var_{}'.format(var_num)
            ctl_bounds['type'] = var_type
            ctl_bounds['domain'] = (0, 1)
            var_num += 1
            bounds.append(ctl_bounds)
    return bounds


def run_baeopt(opt_params):
    # set up opt params
    bounds = get_bounds(sm.run.ctl_str_ids, sm.run.n_ctl_steps)
    max_iter = opt_params.get('max_iter', 15)
    max_time = opt_params.get('max_time', 120)
    initial_guess = opt_params.get('initial_guess', [])
    if len(initial_guess) == 0:
        initial_guess = None
    else:
        initial_guess = np.array([initial_guess])

    eps = opt_params.get('eps', 0.01)
    model_type = opt_params.get('model_type', 'GP')
    acquisition_type = opt_params.get('acquisition_type', 'EI')

    # instantiate object
    bae_opt = BayOpt(ev.evaluate,
                     domain=bounds,
                     model_type=model_type,
                     acquisition_type='EI',
                     X=initial_guess,
                     evaluator_type='local_penalization',
                     num_cores=opt_params['num_cores'],
                     batch_size=opt_params['num_cores'],
                     )
    bae_opt.run_optimization(max_iter, max_time, eps)
    return bae_opt.x_opt, bae_opt.fx_opt

