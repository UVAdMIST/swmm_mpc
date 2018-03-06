import re
import os
import subprocess
import pyswmm
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
import time
pyswmm.lib.use("swmm5_conda.dll")

input_file = "../simple_model/simple_smart_blank.inp"
input_file_tmp_base = input_file.replace(".inp", "_tmp")
input_file_tmp_inp = input_file_tmp_base + ".inp"
copyfile(input_file, input_file_tmp_inp)

def update_depths_or_flows(lines, i, depths_or_flows, col_name):
    init_depth_loc = lines[i+1].find(col_name)
    for obj_id in depths_or_flows:
        for j, l in enumerate(lines[i:]):
            if l.startswith(obj_id):
                new_value_string = "{: <11.4f}".format(depths_or_flows[obj_id]) 
                new_string = l[:init_depth_loc] + new_value_string + l[init_depth_loc+11: ]
                lines[i+j] = new_string
                break 
    return lines

def update_simulation_date_time(lines, i, new_datetime):
    new_date = new_datetime.strftime("%m/%d/%Y")
    new_time = new_datetime.strftime("%H:%M:%S")
    lines[i] = re.sub(r'\d{2}\\\d{2}\\\d{2}', new_date, lines[i])
    lines[i+1] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time, lines[i+1])
    return lines
    

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


def update_tmp_file(new_date_time, node_obj, link_obj):
    depths = get_node_depths(node_obj)
    flows = get_link_flows(link_obj)
    with open(input_file_tmp_inp, 'r') as tmp_file:
        lines = tmp_file.readlines()

    for i,l in enumerate(lines):
        if l.startswith("START_DATE"):
            new_lines = update_simulation_date_time(lines, i, new_date_time)
        elif l.startswith("[JUNCTIONS]"):
            new_lines  = update_depths_or_flows(lines, i, depths['junctions'], "InitDepth")
        elif l.startswith("[STORAGE]"):
            new_lines = update_depths_or_flows(lines, i, depths['storage'], "InitDepth")
        elif l.startswith("[CONDUITS]"):
            new_lines = update_depths_or_flows(lines, i, flows, "InitFlow")


    with open(input_file_tmp_inp, 'w') as tmp_file:
        tmp_file.writelines(lines)

start = time.time()
with Simulation(input_file) as sim:
    sim.step_advance(600)
    for step in sim:
        node_obj = Nodes(sim)
        link_obj = Links(sim)
        current_date_time = sim.current_time
        update_tmp_file(current_date_time, node_obj, link_obj)
        cmd = "swmm5.exe {0}.inp {0}.rpt {0}.out".format(input_file_tmp_base)
        subprocess.call(cmd, shell=True)
end = time.time()
print (end - start)
