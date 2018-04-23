import pyswmm
import datetime
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
import pandas as pd
import update_process_model_input_file as up
import run_ea
import time
import os
pyswmm.lib.use("/home/jeff/Documents/research/Sadler4th_paper/_build/lib/libswmm5.so")

input_file_dir = os.path.abspath("../simple_model/")
input_file_name = "simple_smart_blank.inp"
input_file = os.path.join(input_file_dir, input_file_name)
input_process_file_base = input_file.replace(".inp", "_process")
input_process_file_inp = input_process_file_base + ".inp"
copyfile(input_file, os.path.join(input_file_dir, input_process_file_inp))

control_horizon = 6. # hr
control_time_step = 900. # sec
n_control_steps = int(control_horizon*3600/control_time_step)
control_str_id = "ORIFICE R1"

def get_flat_depth_dict(depths):
    no_outer = [depths[key] for key in depths]
    depths_flat = {k:v for d in no_outer for k,v in d.items()}
    return depths_flat

def get_link_flows(link_obj):
    flow_dict = {}
    for l in link_obj:
        flow_dict[l.linkid] = l.flow
    return flow_dict

def get_nsteps_remaining(sim):
    time_remaining = sim.end_time - sim.current_time 
    steps = time_remaining.seconds/control_time_step
    if steps < n_control_steps:
        return int(steps)
    elif steps < 3:
        return 2
    else:
        return n_control_steps

def get_node_depths(node_obj):
    junction_depth_dict = {}
    storage_depth_dict = {}
    outfall_depth_dict = {}
    for n in node_obj:
        if n.is_junction():
            junction_depth_dict[n.nodeid] = n.depth
        elif n.is_storage():
            storage_depth_dict[n.nodeid] = n.depth
        elif n.is_outfall():
            outfall_depth_dict[n.nodeid] = n.depth
    depth_dict = {'junctions': junction_depth_dict, 'storage': storage_depth_dict, 
            'outfalls': outfall_depth_dict }
    return depth_dict


def main():
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
            dt_hs_path = os.path.join(input_file_dir, dt_hs_file)
            sim.save_hotstart(dt_hs_path)

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
    print (end - start)
    depths_df = pd.DataFrame(depth_ts)
    depths_df.to_csv("../data/depth_results_{}.csv".format(beg_time))

    control_settings_df = pd.DataFrame(best_policy_ts)
    control_settings_df.to_csv("../data/control_results_{}.csv".format(beg_time))

if __name__ == "__main__":
    main()
