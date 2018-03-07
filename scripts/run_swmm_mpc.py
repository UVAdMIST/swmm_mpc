import pyswmm
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
from update_process_model_input_file import update_process_model_file
import time
pyswmm.lib.use("swmm5_conda.dll")

input_file = "../simple_model/simple_smart_blank.inp"
input_file_tmp_base = input_file.replace(".inp", "_tmp")
input_file_tmp_inp = input_file_tmp_base + ".inp"
copyfile(input_file, input_file_tmp_inp)


def get_link_flows(link_obj):
    flow_dict = {}
    for l in link_obj:
        flow_dict[l.linkid] = l.flow
    return flow_dict

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

start = time.time()
with Simulation(input_file) as sim:
    sim.step_advance(600)
    for step in sim:
        node_obj = Nodes(sim)
        depths = get_node_depths(node_obj)
        link_obj = Links(sim)
        flows = get_link_flows(link_obj)
        current_date_time = sim.current_time
        update_process_model_file(input_file_tmp_inp, current_date_time, depths, flows)
end = time.time()
print (end - start)
