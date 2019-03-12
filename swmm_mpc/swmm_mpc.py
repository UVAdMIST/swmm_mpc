import os
import datetime
from shutil import copyfile
import pandas as pd
import pyswmm
from pyswmm import Simulation, Links
import update_process_model_input_file as up
import evaluate as ev
import run_ea as ra
# import run_baeopt as bo


class swmm_mpc_run(object):
    def __init__():
        glo_control_time_step = control_time_step
        glo_control_str_ids = control_str_ids
        glo_opt_method = opt_method
        glo_target_depth_dict = target_depth_dict
        glo_node_flood_weight_dict = node_flood_weight_dict
        glo_flood_weight = flood_weight
        glo_dev_weight = dev_weight
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
        glo_inp_process_file_path = inp_process_file_path
        # copy input file to process file name
        copyfile(inp_file_path, inp_process_file_path)
        n_control_steps = int(control_horizon*3600/control_time_step)
        glo_n_control_steps = n_control_steps


def run_swmm_mpc(config_file):
    '''
    config_file: [string] path to config file. config file is a JSON file that 
        contains the following key value pairs:
    inp_file_path: [string] path to .inp file relative to config file
    control_horizon: [number] control horizon in hours
    control_time_step: [number] control time step in seconds
    control_str_ids: [list of strings] ids of control structures for which
                     controls policies will be found. Each should start with
                     one of the key words ORIFICE, PUMP, or WEIR
                     e.g., [ORIFICE R1, ORIFICE R2]
    work_dir: [string] directory relative to config file where the temporary
    files will be created 
    results_dir: [string] directory relative to config file where the results
    will be written
    opt_method: [string] optimization method. Currently supported methods are
                         'genetic_algorithm', and 'bayesian_opt'
    optimization_params: [dict] dictionary with key values that will be passed
                         to the optimization function
                         for GA this includes
                            * ngen: [int] number of generations for GA
                            * nindividuals: [int] number of individuals for
                                                  initial generation in GA
    run_suffix: [string] will be added to the results filename
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
    '''
    print(locals())

    # save params to file
    run = swmm_mpc_run(config_file)

    pyswmm.lib.use('libswmm5_hs.so')


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

            print(ev.evaluate([0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1 ]))

            if opt_method == 'genetic_algorithm':
                best_policy, cost = ra.run_ea(work_dir, **optimization_params)
            elif opt_method == 'bayesian_opt':
                pass
                # best_policy, cost = bo.run_baeopt(optimization_params)
            else:
                raise ValueError('{} not valid opt method'.format(opt_method))

            best_policy_fmt = ev.gene_to_policy_dict(best_policy,
                                                     control_str_ids,
                                                     n_control_steps)
            best_policy_ts = update_policy_ts_list(best_policy_fmt,
                                                   current_dt,
                                                   control_time_step,
                                                   best_policy_ts,
                                                   cost)

            implement_control_policy(link_obj, best_policy_fmt)

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


def update_policy_ts_list(fmtd_policy, current_dt, control_time_step,
                          best_policy_ts, cost):
    # record the rest of the control policy
    for control_id, policy in fmtd_policy.iteritems():
        # first setting has already been recorded, so disregard
        for i, setting in enumerate(policy):
            # increase time step
            inc_seconds = i * control_time_step
            inc_time = datetime.timedelta(seconds=inc_seconds)
            setting_dt = current_dt + inc_time
            # append to list
            best_policy_ts.append({'setting_{}'.format(control_id):
                                   setting,
                                   'datetime': setting_dt})
            # if cost is zero only do the first one
            # this should be the case for all but the last case
            if cost == 0:
                return best_policy_ts
    return best_policy_ts


def implement_control_policy(link_obj, best_policy_fmt):
    for control_id, policy in best_policy_fmt.iteritems():
        next_setting = policy[0]

        # from for example "ORIFICE R1" to "R1"
        control_id_short = control_id.split()[-1]
        # implement best policy
        if next_setting == 'ON':
            next_setting = 1
        elif next_setting == 'OFF':
            next_setting = 0

        link_obj[control_id_short].target_setting = next_setting


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
    ctl_settings_df = pd.DataFrame(best_policy_ts)
    ctl_settings_df = ctl_settings_df.groupby('datetime').first()
    ctl_settings_df.index = pd.DatetimeIndex(ctl_settings_df.index)
    # add a row at the beginning of the policy since controls start open
    sim_start_dt = pd.to_datetime(sim_start_time)
    print(ctl_settings_df)
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
