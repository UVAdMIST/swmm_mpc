import time
import os
import datetime
from shutil import copyfile
import pandas as pd
import pyswmm
from pyswmm import Simulation, Links
import update_process_model_input_file as up
import run_ea as ra


def run_swmm_mpc(inp_file_path, control_horizon, control_time_step,
                 control_str_ids, work_dir, results_dir,
		 target_depth_dict=None, node_flood_weight_dict=None, ngen=7,
		 nindividuals=100, verbose_results=False):
    '''
    inp_file_path: [string] path to .inp file
    control_horizon: [number] control horizon in hours
    control_time_step: [number] control time step in seconds
    control_str_ids: [list of strings] ids of control structures for which
                     controls policies will be found.
                     e.g., [ORIFICE R1, ORIFICE R2]
    work_dir: [string] directory where the temporary files will be created
    results_dir: [string] directory where the results will be written
    target_depth_dict: [dict] dictionary where the keys are the nodeids and
                       the values are a dictionary. The inner dictionary has
                       two keys, 'target', and 'weight'. These values specify
                       the target depth for the nodeid and the weight given
                       to that in the cost function.
                       e.g., {'St1': {'target': 1, 'weight': 0.1}}
    node_flood_weight_dict: [dict] dictionary where the keys are the node ids
                            and the values are the relative weights for
                            weighting the amount of flooding for a given node.
                            e.g., {'st1': 10, 'J3': 1}
    ngen: [int] number of generations for GA
    nindividuals: [int] number of individuals for initial generation in GA
    verbose_results: [bool] whether or not verbose results should be saved
    '''
    # full file path
    # inp_file_path = os.path.abspath(inp_file_path)
    # the input directory and the file name
    inp_file_dir, inp_file_name = os.path.split(inp_file_path)
    # the process file name with no extension
    inp_process_file_base = inp_file_name.replace('.inp', '_process')
    # the process .inp file name
    inp_process_file_inp = inp_process_file_base + '.inp'
    inp_process_file_path = os.path.join(work_dir, inp_process_file_inp)
    # copy input file to process file name
    copyfile(inp_file_path, inp_process_file_path)

    pyswmm.lib.use('libswmm5_hs.so')

    n_control_steps = int(control_horizon*3600/control_time_step)

    # run simulation
    beg_time = datetime.datetime.now()
    beg_time_str = beg_time.strftime('%Y.%m.%d.%H.%M')
    print "Simulation start: {}".format(beg_time_str)
    best_policy_ts = []
    with Simulation(inp_file_path) as sim:
        sim.step_advance(control_time_step)
        for step in sim:
            # get most current system states
            current_dt = sim.current_time

            dt_hs_file = 'tmp_hsf.hsf'
            print(current_dt)
            dt_hs_path = os.path.join(inp_file_dir, dt_hs_file)
            sim.save_hotstart(dt_hs_path)

            link_obj = Links(sim)

            # update the process model with the current states
            up.update_process_model_file(inp_process_file_path,
                                         current_dt, dt_hs_path)

            # get num control steps remaining
            # nsteps = get_nsteps_remaining(sim)
            nsteps = n_control_steps * len(control_str_ids)

            best_policy = ra.run_ea(nsteps,
                                    ngen,
                                    nindividuals,
                                    verbose_results,
                                    results_dir,
                                    dt_hs_path,
                                    inp_process_file_path,
                                    control_time_step,
                                    n_control_steps,
                                    control_str_ids,
                                    target_depth_dict,
                                    node_flood_weight_dict)

            best_policy_fmt = fmt_control_policies(best_policy,
                                                   control_str_ids,
                                                   n_control_steps)
            for control_id, policy in best_policy_fmt.iteritems():
                best_policy_per = policy[0]/10.
                best_policy_ts.append({'setting_{}'.format(control_id):
                                       best_policy_per,
                                       'datetime': current_dt})

                # implement best policy
                # from for example "ORIFICE R1" to "R1"
                control_id_short = control_id.split()[-1]
                link_obj[control_id_short].target_setting = best_policy_per

    end_time = datetime.datetime.now()
    print('simulation end: {}'.format(end_time.strftime('%Y.%m.%d.%H.%M')))
    elapsed_time = end_time - beg_time
    print('elapsed time: {}'.format(elapsed_time.seconds))

    control_settings_df = pd.DataFrame(best_policy_ts)
    control_settings_df = control_settings_df.pivot_table(index='datetime')
    control_settings_df.to_csv('{}control_results_{}.csv'.format(results_dir,
                                                                 beg_time_str))


def fmt_control_policies(control_array, control_str_ids, n_control_steps):
    policies = dict()
    for i, control_id in enumerate(control_str_ids):
        policies[control_id] = control_array[i*n_control_steps:
                                             (i+1)*n_control_steps]
    return policies
