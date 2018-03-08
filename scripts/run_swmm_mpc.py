import pyswmm
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
import pandas as pd
import update_process_model_input_file as up
import run_ea
import time
pyswmm.lib.use("swmm5_conda.dll")

input_file = "../simple_model/simple_smart_blank.inp"
input_process_file_base = input_file.replace(".inp", "_process")
input_process_file_inp = input_process_file_base + ".inp"
copyfile(input_file, input_process_file_inp)

control_horizon = 6. # hr
control_time_step = 900. # sec
n_control_steps = control_time_step*3600/control_time_step
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
    steps = time_remaining/control_time_step
    if steps < n_control_steps:
        return steps
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
    start = time.time()
    depth_ts = []
    with Simulation(input_file) as sim:
        sim.step_advance(control_time_step)
        for step in sim:
            # get most current system states
            node_obj = Nodes(sim)
            depths = get_node_depths(node_obj)
            depth_ts.append(get_flat_depth_dict(depths))
            link_obj = Links(sim)
            orifice = link_obj["R1"]
            flows = get_link_flows(link_obj)
            current_date_time = sim.current_time

            # update the process model with the current states
            up.update_process_model_file(input_process_file_inp, current_date_time, depths, flows)

            # get num control steps remaining
            nsteps = get_nsteps_remaining(sim)

            # run prediction to get best policy 
            best_policy = run_ea.run_ea(nsteps)

            #implement best policy
            orifice.target_setting = best_policy[0]/10.

            end = time.time()
    print (end - start)
    df = pd.DataFrame(depth_ts)
    df.to_csv("../data/depth_results.csv")
    return df

if __name__ == "__main__":
    main()
