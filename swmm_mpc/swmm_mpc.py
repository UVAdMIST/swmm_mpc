import pyswmm
import datetime
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
import pandas as pd
import update_process_model_input_file as up
import run_ea
import time
import os


class swmm_mpc(object):
    def __init__(inp_file_path, pyswmm_lib, control_horizon, control_time_step, control_str_ids, 
            results_dir)
    """
    input_file_path:
    pyswmm_lib:
    control_horizon:
    control_time_step:
    control_str_ids:
    results_dir:
    """
    self.inp_file_path = os.path.abspath(inp_file_path)
    self.inp_file_dir, self.inp_file_name = os.path.split(self.inp_file_path)[0]
    self.input_process_file_base = input_file.replace(".inp", "_process")
    self.input_process_file_inp = input_process_file_base + ".inp"
    copyfile(input_file, os.path.join(input_file_dir, input_process_file_inp))

    pyswmm.lib.use("/home/jeff/Documents/research/Sadler4th_paper/_build/lib/libswmm5.so")

    self.control_horizon = float(control_horizon) # hr
    self.control_time_step = float(control_time_step) # sec
    self.n_control_steps = int(control_horizon*3600/control_time_step)
    self.control_str_name = control_str_name
    self.control_str_id = control_str_name.split()

    def run_swmm_mpc(self):
        beg_time = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
        start = time.time()
        depth_ts = []
        best_policy_ts = []
        with Simulation(input_file) as sim:
            sim.step_advance(control_time_step)
            for step in sim:
                # get most current system states
                current_date_time = sim.current_time

                dt_hs_file = "{}.hsf".format(current_date_time.strftime("%Y%m%d%H%M"))
                print current_date_time
                dt_hs_path = os.path.join(input_file_dir, dt_hs_file)
                sim.save_hotstart(dt_hs_path)

                link_obj = Links(sim)
                orifice = link_obj["R1"]

                # update the process model with the current states
                up.update_process_model_file(input_process_file_inp, current_date_time, dt_hs_file)

                # get num control steps remaining
                nsteps = get_nsteps_remaining(sim)

                # if nsteps > 1:
                    # # run prediction to get best policy 
                best_policy = run_ea.run_ea(n_control_steps)
                best_policy_per = best_policy[0]/10.
                best_policy_ts.append({"setting_{}".format(control_str_id):best_policy_per, 
                    "datetime":current_date_time})

                # implement best policy
                orifice.target_setting = best_policy_per

                end = time.time()
                print ("elapsed time: {}".format(end-start))
        self.depths_df = pd.DataFrame(depth_ts)
        self.depths_df.to_csv("{}depth_results_{}.csv".format(beg_time, results_dir))

        self.control_settings_df = pd.DataFrame(best_policy_ts)
        self.control_settings_df.to_csv("{}control_results_{}.csv".format(beg_time, results_dir))
