import GPyOpt
import swmm_mpc as sm
import evaluate as ev
from GPyOpt.methods import BayesianOptimization as BayOpt


def get_bounds(ctl_str_ids):
    bounds = []
    for i, ctl in enumerate(ctl_str_ids):
        ctl_type = ctl.split()[0]
        ctl_bounds = {}

        if ctl_type == 'WEIR' or ctl_type == 'ORIFICE':
            var_type = 'continuous'
        elif ctl_type == 'PUMP':
            var_type = 'discrete'

        ctl_bounds['name'] = 'var_{}'.format(i)
        ctl_bounds['type'] = var_type
        ctl_bounds['domain'] = (0, 1)
        bounds.append(ctl_bounds)
    return bounds


def run_baeopt(opt_params):
    # set up opt params
    bounds = get_bounds(sm.run.ctl_str_ids)
    max_iter = opt_params.get('max_iter', 15)
    max_time = opt_params.get('max_time', 120)
    eps = opt_params.get('eps', 10e-4)
    model_type = opt_params.get('model_type', 'GP')
    acquisition_type = opt_params.get('acquisition_type', 'EI')
    print opt_params['num_cores'], 'num cores!'

    # instantiate object
    bae_opt = BayOpt(ev.evaluate,
                     domain=bounds,
                     model_type=model_type,
                     acquisition_type='EI',
                     evaluator_type='local_penalization',
                     num_cores=opt_params['num_cores'],
                     )
    bae_opt.run_optimization(max_iter, max_time, eps)
    return bae_opt.x_opt, bae_opt.fx_opt

