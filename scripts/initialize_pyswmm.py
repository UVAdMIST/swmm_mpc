from pyswmm import Simulation
import pyswmm

pyswmm.lib.use("/home/jeff/Documents/research/Sadler4th_paper/_build/lib/libswmm5.so")

inp_file = "../simple_model/simple_smart_blank.inp"
# sim = Simulation(inp_file)
with Simulation(inp_file) as sim:
    i = 0
    for step in sim:
        print step
        i += 1
        if i == 5:
            sim._model.hotstart_open("{}.hsf".format(i))

