from pyswmm import Simulation, Links, Nodes

with Simulation('simple_smart_blank.inp') as sim:
    link_obj = Links(sim)

    ori = link_obj['R1']
    ori.target_setting = 0.0
    
    for step in sim:
        print step
    sim.report()
