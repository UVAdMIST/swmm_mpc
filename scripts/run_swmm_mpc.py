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

def update_junction_depths(lines, i, depths):
    pass

def update_storage_depths(lines, i, depths):
    pass

def update_conduit_flows(lines, i, flows):
    pass

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
    depth_dict = {}
    for n in node_obj:
        depth_dict[n.nodeid] = n.depth
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
            new_lines  = update_junction_depths(lines, i, depths)
        elif l.startswith("[STORAGE]"):
            new_lines = update_storage_depths(lines, i, depths)
        elif l.startswith("[CONDUITS]"):
            new_lines = update_conduit_flows(lines, i, flows)


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
        # cmd = "swmm5.exe {0}.inp {0}.rpt {0}.out".format(input_file_tmp_base)
        # subprocess.call(cmd, shell=True)
end = time.time()
print (end - start)
