from pyswmm import Simulation
import pyswmm

pyswmm.lib.use("/home/jeff/Documents/research/Sadler4th_paper/_build/lib/libswmm5.so")

inp_file = "../simple_model/simple_smart_blank.inp"
sim = Simulation(inp_file)
