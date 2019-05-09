import os
import datetime
import random
from shutil import copyfile
import shutil
import pandas as pd
import pyswmm
from pyswmm import Simulation, Links
import update_process_model_input_file as up
import evaluate as ev
import run_ea as ra
import json
import run_baeopt as bo

run = None

def get_global_run(config_file):
    global run
    run = swmm_mpc_run(config_file)


class swmm_mpc_run(object):
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        self.inp_file_path = os.path.abspath(config_dict['inp_file_path'])
        self.ctl_horizon = config_dict['ctl_horizon']
        self.ctl_time_step = config_dict['ctl_time_step']
        self.ctl_str_ids = config_dict['ctl_str_ids']
        self.work_dir = os.path.abspath(config_dict['work_dir'])
        self.results_dir = os.path.abspath(config_dict['results_dir'])
        self.opt_method = config_dict['opt_method']
        self.optimization_params = config_dict.get('optimization_params', {})
        if 'num_cores' in self.optimization_params:
            if type(self.optimization_params['num_cores']) != int:
                self.optimization_params['num_cores'] = 1
        else:
            self.optimization_params['num_cores'] = 1
        self.run_suffix = config_dict['run_suffix']
        self.target_depth_dict = config_dict.get('target_depth_dict', None)
        self.node_flood_weight_dict = config_dict.get('node_flood_weight_dict',
                                                      None)
        self.flood_weight = config_dict.get('flood_weight', 1)
        if self.target_depth_dict:
            self.dev_weight = config_dict.get('dev_weight', 1)
        else:
            self.dev_weight = config_dict.get('dev_weight', 0)
        self.log_file = os.path.join(self.results_dir,
                                     'log_{}'.format(self.run_suffix))

        # check ctl_str_ids
        validate_ctl_str_ids(self.ctl_str_ids)

        # the input directory and the file name
        self.inp_file_dir, inp_file_name = os.path.split(self.inp_file_path)
        # the process file name with no extension
        inp_process_file_base = inp_file_name.replace('.inp', '_process')
        # the process .inp file name
        inp_process_file_inp = inp_process_file_base + '.inp'
        self.inp_process_file_path = os.path.join(self.work_dir,
                                                  inp_process_file_inp)
        # copy input file to process file name
        copyfile(self.inp_file_path, self.inp_process_file_path)

        self.n_ctl_steps = int(self.ctl_horizon*3600/self.ctl_time_step)


def run_swmm_mpc(config_file):
    '''
    config_file: [string] path to config file. config file is a JSON file that
        contains the following key value pairs:
    inp_file_path: [string] path to .inp file relative to config file
    ctl_horizon: [number] ctl horizon in hours
    ctl_time_step: [number] control time step in seconds
    ctl_str_ids: [list of strings] ids of control structures for which
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
    flood_weight: [number] overall weight for the sum of all flooding relative
                  to the overall weight for the sum of the absolute deviations
                  from target depths (dev_weight). Default: 1
    dev_weight: [number] overall weight for the sum of the absolute deviations
                from target depths. This weight is relative to the flood_weight
                Default: 0
    target_depth_dict: [dict] dictionary where the keys are the nodeids and
                       the values are a dictionary. The inner dictionary has
                       two keys, 'target', and 'weight'. These values specify
                       the target depth for the nodeid and the weight given
                       to that in the cost function. Default: None
                       e.g., {'St1': {'target': 1, 'weight': 0.1}}
    node_flood_weight_dict: [dict] dictionary where the keys are the node ids
                            and the values are the relative weights for
                            weighting the amount of flooding for a given node.
                            e.g., {'st1': 10, 'J3': 1}. Default: None

    '''
    # save params to file
    get_global_run(config_file)
    print(vars(run))

    with open(run.log_file, 'w') as f:
        f.write(str(vars(run)))
        f.write('\n')

    pyswmm.lib.use('libswmm5_hs.so')

    # record when simulation begins
    beg_time = datetime.datetime.now()
    run_beg_time_str = beg_time.strftime('%Y.%m.%d.%H.%M')
    print("Simulation start: {}".format(run_beg_time_str))
    best_policy_ts = []

    # make sure there is no control rules in inp file
    up.remove_control_section(run.inp_file_path)

    # run simulation
    with Simulation(run.inp_file_path) as sim:
        sim.step_advance(run.ctl_time_step)
        sim_start_time = sim.start_time
        for step in sim:
            # get most current system states
            current_dt = sim.current_time

            dt_hs_file = 'tmp_hsf.hsf'
            print(current_dt)
            dt_hs_path = os.path.join(os.getcwd(), dt_hs_file)
            sim.save_hotstart(dt_hs_path)

            link_obj = Links(sim)

            # update the process model with the current states
            up.update_process_model_file(run.inp_process_file_path,
                                         current_dt, dt_hs_path)

            if run.opt_method == 'genetic_algorithm':
                best_policy, cost = ra.run_ea(run.work_dir, config_file,
                                              run.optimization_params)
            elif run.opt_method == 'bayesian_opt':
                best_policy, cost = bo.run_baeopt(run.optimization_params)
                initial_guess = get_initial_guess(best_policy, run.ctl_str_ids)
                run.optimization_params['initial_guess'] = initial_guess
            else:
                raise ValueError(
                    '{} not valid opt method'.format(run.opt_method)
                    )
            print best_policy, cost

            best_policy_fmt = ev.format_policies(best_policy,
                                                 run.ctl_str_ids,
                                                 run.n_ctl_steps,
                                                 run.opt_method)
            best_policy_ts = update_policy_ts_list(best_policy_fmt,
                                                   current_dt,
                                                   run.ctl_time_step,
                                                   best_policy_ts,
                                                   cost)

            results_file = save_results_file(best_policy_ts, run.ctl_str_ids,
                                             run.results_dir, sim_start_time,
                                             run_beg_time_str, run.run_suffix)

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
    with open(run.log_file, 'a') as f:
        f.write(elapsed_time_str)

    # update original inp file with found control policy
    up.update_controls_with_policy(run.inp_file_path, results_file)

    # remove all files in 'work'
    delete_files_in_dir(run.work_dir)



def update_policy_ts_list(fmtd_policy, current_dt, ctl_time_step,
                          best_policy_ts, cost):
    # record the rest of the control policy
    for ctl_id, policy in fmtd_policy.iteritems():
        # first setting has already been recorded, so disregard
        for i, setting in enumerate(policy):
            # increase time step
            inc_seconds = i * ctl_time_step
            inc_time = datetime.timedelta(seconds=inc_seconds)
            setting_dt = current_dt + inc_time
            # append to list
            best_policy_ts.append({'setting_{}'.format(ctl_id):
                                   setting,
                                   'datetime': setting_dt})
            # if cost is not zero only do the first one
            # this should be the case for all but the last case
            if cost != 0:
                break
    return best_policy_ts


def implement_control_policy(link_obj, best_policy_fmt):
    for ctl_id, policy in best_policy_fmt.iteritems():
        next_setting = policy[0]

        # from for example "ORIFICE R1" to "R1"
        ctl_id_short = ctl_id.split()[-1]
        # implement best policy
        if next_setting == 'ON':
            next_setting = 1
        elif next_setting == 'OFF':
            next_setting = 0

        link_obj[ctl_id_short].target_setting = next_setting


def save_results_file(best_policy_ts, ctl_str_ids, results_dir,
                      sim_start_time, run_beg_time_str, run_suffix):
    """
    Convert policy time series to dataframe and save to csv

    Parameters
    ----------
    best_policy_ts : list of dicts
        list of dicts where the key/values are "setting_{ctl id}"/{setting}
        and "datetime"/{datetime}
    ctl_str_ids : list of str
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
    initial_states = get_initial_states(ctl_str_ids)
    ctl_settings_df.loc[sim_start_dt] = initial_states
    ctl_settings_df.sort_index(inplace=True)
    results_file = 'ctl_results_{}{}.csv'.format(run_beg_time_str, run_suffix)
    results_path = os.path.join(results_dir, results_file)
    ctl_settings_df.to_csv(results_path)
    return results_path


def get_initial_states(ctl_str_ids):
    """
    Get list of initial states. ASSUME initial states for ORIFICE/WEIR is 1
        (open) and for PUMPS is "OFF"
    """
    initial_states = []
    for ctl in ctl_str_ids:
        ctl_type = ctl.split()[0]
        if ctl_type == 'ORIFICE' or ctl_type == 'WEIR':
            initial_states.append(1)
        elif ctl_type == 'PUMP':
            initial_states.append('OFF')
    return initial_states


def validate_ctl_str_ids(ctl_str_ids):
    """
    make sure the ids are ORIFICE, PUMP, or WEIR
    """
    valid_structure_types = ['ORIFICE', 'PUMP', 'WEIR']
    for ctl_id in ctl_str_ids:
        ctl_type = ctl_id.split()[0]
        if ctl_type not in valid_structure_types:
            raise ValueError(
                '{} not valid ctl type. should be one of {}'.format(
                    ctl_id, valid_structure_types))


def get_initial_guess(best_pol, ctl_str_ids):
    best_pol = best_pol.tolist()
    split_by_ctl = ev.split_list(best_pol, len(ctl_str_ids))
    new_guess = []
    for pol in split_by_ctl:
        if len(pol) == 1:
            return best_pol
        else:
            # take out first setting
            new_pol = pol[1:]
            # add random setting at end
            new_pol.append(random.random())
            new_guess.extend(new_pol)
    return new_guess

def delete_files_in_dir(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)
