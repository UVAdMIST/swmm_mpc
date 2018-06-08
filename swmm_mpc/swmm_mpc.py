import time
import os
import datetime
import pyswmm
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
import pandas as pd


def run_swmm_mpc(inp_file_path, control_horizon, control_time_step, control_str_ids, results_dir, 
        target_depth_dict=None, node_flood_weight_dict=None, ngen=7, nindividuals=100):
    '''
    inp_file_path: [string] path to .inp file 
    control_horizon: [number] control horizon in hours
    control_time_step: [number] control time step in seconds
    control_str_ids: [list of strings] ids of control structures for which controls policies 
                     will be found. e.g., [ORIFICE R1, ORIFICE R2]
    results_dir: [string] directory where the results will be written
    target_depth_dict: [dict] dictionary where the keys are the nodeids and the values are a 
                       dictionary. The inner dictionary has two keys, 'target', and 'weight'. 
                       These values specify the target depth for the nodeid and the weight given 
                       to that in the cost function. e.g., {'St1': {'target': 1, 'weight': 0.1}} 
    node_flood_weight_dict: [dict] dictionary where the keys are the node ids and the values are 
                            the relative weights for weighting the amount of flooding for a 
                            particular node. e.g., {'st1': 10, 'J3': 1}
    ngen: [int] number of generations for GA
    nindividuals: [int] number of individuals for initial generation in GA
    '''
    # full file path
    inp_file_path = os.path.abspath(inp_file_path)
    # the input directory and the file name
    inp_file_dir, inp_file_name = os.path.split(inp_file_path)
    # the process file name with no extension
    inp_process_file_base = inp_file_name.replace('.inp', '_process')
    # the process .inp file name 
    inp_process_file_inp = inp_process_file_base + '.inp'
    # copy input file to process file name
    copyfile(inp_file_path, os.path.join(inp_file_dir, inp_process_file_inp))

    pyswmm.lib.use('libswmm5_hs.so')

    n_control_steps = int(control_horizon*3600/control_time_step)

    beg_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')
    start = time.time()
    best_policy_ts = []
    with Simulation(inp_file_path) as sim:
        sim.step_advance(control_time_step)
        for step in sim:
            # get most current system states
            current_date_time = sim.current_time

            dt_hs_file = '{}.hsf'.format(current_date_time.strftime('%Y%m%d%H%M'))
            print current_date_time
            dt_hs_path = os.path.join(inp_file_dir, dt_hs_file)
            sim.save_hotstart(dt_hs_path)

            link_obj = Links(sim)

            # update the process model with the current states
            update_process_model_file(inp_process_file_inp, current_date_time, dt_hs_file)

            # get num control steps remaining
            # nsteps = get_nsteps_remaining(sim)
            nsteps = n_control_steps * len(control_str_ids)

            best_policy = run_ea(nsteps)
            best_policy_fmt = fmt_control_policies(best_policy)
            for control_id, policy in best_policy_fmt.iteritems():
                best_policy_per = policy[0]/10.
                best_policy_ts.append({'setting_{}'.format(control_id):best_policy_per, 
                'datetime':current_date_time}) 
                
                # implement best policy
                # from for example "ORIFICE R1" to "R1"
                control_id_short = control_id.split()[-1]
                link_obj[control_id_short].target_setting = best_policy_per

            end = time.time()
            print ('elapsed time: {}'.format(end-start))

    control_settings_df = pd.DataFrame(best_policy_ts)
    control_settings_df.to_csv('{}control_results_{}.csv'.format(beg_time, results_dir))

def fmt_control_policies(control_array, control_str_ids, n_control_steps):
    policies = dict()
    for i, control_id in enumerate(control_str_ids):
        policies[control_id] = control_array[i*n_control_steps: (i+1)*n_control_steps]
    return policies
