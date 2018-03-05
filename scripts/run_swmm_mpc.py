import os
import subprocess
import pyswmm
from pyswmm import Simulation, Nodes, Links
from swmm5.swmm5tools import SWMM5Simulation
from shutil import copyfile
import time
pyswmm.lib.use("swmm5_conda.dll")

input_file = "../simple_model/simple_smart.inp"
input_file_tmp_base = input_file.replace(".inp", "_tmp")
input_file_tmp_inp = input_file_tmp_base + ".inp"
copyfile(input_file, input_file_tmp_inp)

start = time.time()
counter = 0 
with Simulation(input_file) as sim:
    sim.step_advance(600)
    for step in sim:
        counter += 1
        # print sim.current_time
        cmd = "swmm5.exe {0}.inp {0}.rpt {0}.out".format(input_file_tmp_base)
        subprocess.call(cmd, shell=True)
end = time.time()
print counter
print (end - start)
