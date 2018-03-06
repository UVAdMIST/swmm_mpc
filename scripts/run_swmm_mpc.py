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

def update_tmp_file(new_time, new_depths, new_flows):
    with open(input_file_tmp_inp, 'r') as tmp_file:
        lines = tmp_file.readlines()

    for i,l in enumerate(lines):
        if l.startswith("START_TIME"):
            lines[i] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time, l)

    with open(input_file_tmp_inp, 'w') as tmp_file:
        tmp_file.writelines(lines)

start = time.time()
with Simulation(input_file) as sim:
    sim.step_advance(600)
    for step in sim:
        node_obj = Nodes(sim)
        link_obj = Links(sim)
        current_time = sim.current_time
        current_time = current_time.strftime("%H:%M:%S")
        update_tmp_file(current_time, "", "")
        # cmd = "swmm5.exe {0}.inp {0}.rpt {0}.out".format(input_file_tmp_base)
        # subprocess.call(cmd, shell=True)
end = time.time()
print (end - start)
