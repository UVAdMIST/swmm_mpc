from pyswmm import Simulation
import pyswmm
import sys

pyswmm.lib.use("/home/jeff/Documents/research/Sadler4th_paper/_build/lib/libswmm5.so")

inp_file = sys.argv[1]
with Simulation(inp_file) as sim:
    saved_hsf = False
    for step in sim:
        cur_time_str = sim.current_time.strftime("%H:%M")
        if cur_time_str == "05:59" and not saved_hsf:
            sim._model.save_hotstart("{}.hsf".format("pyswmm"))
            saved_hsf = True

