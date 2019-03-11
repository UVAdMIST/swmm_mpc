import os
import datetime
from shutil import copyfile
import pandas as pd
import pyswmm
from pyswmm import Simulation, Links
import update_process_model_input_file as up
import evaluate as ev
import run_ea as ra


def run_swmm_mpc(inp_file_path, control_horizon, control_time_step,
                 control_str_ids, work_dir, results_dir,
                 target_depth_dict=None, node_flood_weight_dict=None,
                 flood_weight=1, dev_weight=1, ngen=7, nindividuals=100,
                 run_suffix=''):
    '''
    inp_file_path: [string] path to .inp file
    control_horizon: [number] control horizon in hours
    control_time_step: [number] control time step in seconds
    control_str_ids: [list of strings] ids of control structures for which
                     controls policies will be found. Each should start with
                     one of the key words ORIFICE, PUMP, or WEIR
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
    run_suffix: [string] will be added to the results filename
    '''
    print(locals())
    # save params to file
    log_file = os.path.join(results_dir, 'log_{}'.format(run_suffix))
    with open(log_file, 'w') as f:
        f.write(str(locals()))
        f.write('\n')

    # check control_str_ids
    validate_control_str_ids(control_str_ids)

    # make paths absolute
    inp_file_path = os.path.abspath(inp_file_path)
    work_dir = os.path.abspath(work_dir)
    results_dir = os.path.abspath(results_dir)

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

    # record when simulation begins
    beg_time = datetime.datetime.now()
    run_beg_time_str = beg_time.strftime('%Y.%m.%d.%H.%M')
    print("Simulation start: {}".format(run_beg_time_str))
    best_policy_ts = []

    # make sure there is no control rules in inp file
    up.remove_control_section(inp_file_path)

    # run simulation
    with Simulation(inp_file_path) as sim:
        sim.step_advance(control_time_step)
        sim_start_time = sim.start_time
        for step in sim:
            # get most current system states
            current_dt = sim.current_time
            current_dt_str = current_dt.strftime('%Y.%m.%d.%H.%M')

            dt_hs_file = 'tmp_hsf.hsf'
            print(current_dt)
            dt_hs_path = os.path.join(inp_file_dir, dt_hs_file)
            sim.save_hotstart(dt_hs_path)

            link_obj = Links(sim)

            # update the process model with the current states
            up.update_process_model_file(inp_process_file_path,
                                         current_dt, dt_hs_path)

            best_policy, cost = ra.run_ea(ngen,
                                          nindividuals,
                                          work_dir,
                                          dt_hs_path,
                                          inp_process_file_path,
                                          current_dt_str,
                                          control_time_step,
                                          n_control_steps,
                                          control_str_ids,
                                          target_depth_dict,
                                          node_flood_weight_dict,
                                          flood_weight,
                                          dev_weight)

            best_policy_fmt = ev.gene_to_policy_dict(best_policy,
                                                     control_str_ids,
                                                     n_control_steps)
            for control_id, policy in best_policy_fmt.iteritems():
                next_setting = policy[0]
                best_policy_ts.append({'setting_{}'.format(control_id):
                                       next_setting,
                                       'datetime': current_dt})

                # implement best policy
                # from for example "ORIFICE R1" to "R1"
                if next_setting == 'ON':
                    next_setting = 1
                elif next_setting =='OFF':
                    next_setting = 0

                control_id_short = control_id.split()[-1]
                link_obj[control_id_short].target_setting = next_setting

            # if we are getting a policy with no cost then it's perfect
            if cost == 0:
                break

    end_time = datetime.datetime.now()
    print('simulation end: {}'.format(end_time.strftime('%Y.%m.%d.%H.%M')))
    elapsed_time = end_time - beg_time
    elapsed_time_str = 'elapsed time: {}'.format(elapsed_time.seconds)
    print(elapsed_time_str)

    # write the elapsed time to the end of the log file
    with open(log_file, 'a') as f:
        f.write(elapsed_time_str)

    results_file = save_results_file(best_policy_ts, control_str_ids,
                                     results_dir, sim_start_time,
                                     run_beg_time_str, run_suffix)

    # update original inp file with found control policy
    up.update_controls_with_policy(inp_file_path, results_file)


def save_results_file(best_policy_ts, control_str_ids, results_dir,
                      sim_start_time, run_beg_time_str, run_suffix):
    """
    Convert policy time series to dataframe and save to csv

    Parameters
    ----------
    best_policy_ts : list of dicts
        list of dicts where the key/values are "setting_{control id}"/{setting}
        and "datetime"/{datetime}
    control_str_ids : list of str
        see documentation in "run_swmm_mpc"
    results_dir : str
        the directory where the csv will be saved
    sim_start_time : datetime object
        the datetime of the start time in the simulation
    run_beg_time_str : str
        the real time when the swmm_mpc run started
    run_suffix : str
        the run suffix that will be appended to the csv file name
    """
    # consolidate ctl settings and save to csv file
    print best_policy_ts
    ctl_settings_df = pd.DataFrame(best_policy_ts)
    ctl_settings_df = ctl_settings_df.groupby('datetime').first()
    ctl_settings_df.index = pd.DatetimeIndex(ctl_settings_df.index)
    # add a row at the beginning of the policy since controls start open
    sim_start_dt = pd.to_datetime(sim_start_time)
    print ctl_settings_df
    initial_states = get_initial_states(control_str_ids)
    ctl_settings_df.loc[sim_start_dt] = initial_states
    ctl_settings_df.sort_index(inplace=True)
    results_file = 'ctl_results_{}{}.csv'.format(run_beg_time_str, run_suffix)
    results_path = os.path.join(results_dir, results_file)
    ctl_settings_df.to_csv(results_path)
    return results_path


def get_initial_states(control_str_ids):
    """
    Get list of initial states. ASSUME initial states for ORIFICE/WEIR is 1
        (open) and for PUMPS is "OFF"
    """
    initial_states = []
    for ctl in control_str_ids:
        control_type = ctl.split()[0]
        if control_type == 'ORIFICE' or control_type == 'WEIR':
            initial_states.append(1)
        elif control_type == 'PUMP':
            initial_states.append('OFF')
    return initial_states


def validate_control_str_ids(control_str_ids):
    """
    make sure the ids are ORIFICE, PUMP, or WEIR
    """
    valid_structure_types = ['ORIFICE', 'PUMP', 'WEIR']
    for ctl_id in control_str_ids:
        ctl_type = ctl_id.split()[0]
        if ctl_type not in valid_structure_types:
            raise ValueError(
                    '{} not valid ctl type. should be one of {}'.format(
                     ctl_id, valid_structure_types))
