import random
import multiprocessing
from deap import base, creator, tools, algorithms
import numpy as np
import evaluate as ev


creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
creator.create('Individual', list, fitness=creator.FitnessMin)

pool = multiprocessing.Pool(16)
toolbox = base.Toolbox()
toolbox.register('map', pool.map)
toolbox.register('attr_int', random.randint, 0, 10)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutUniformInt, low=0, up=10, indpb=0.10)
toolbox.register('select', tools.selTournament, tournsize=6)


def run_ea(nsteps, ngen, nindividuals, verbose_results, data_dir, hs_file_path,
           inp_process_file_path, sim_dt, control_time_step, n_control_steps,
           control_str_ids, target_depth_dict, node_flood_weight_dict,
           flood_weight, dev_weight):
    toolbox.register('evaluate',
                     ev.evaluate,
                     hs_file_path=hs_file_path,
                     process_file_path=inp_process_file_path,
		     sim_dt=sim_dt,
                     control_time_step=control_time_step,
                     n_control_steps=n_control_steps,
                     control_str_ids=control_str_ids,
                     node_flood_weight_dict=node_flood_weight_dict,
                     target_depth_dict=target_depth_dict,
                     flood_weight=flood_weight,
                     dev_weight=dev_weight
                     )
    toolbox.register('individual', tools.initRepeat, creator.Individual,
                     toolbox.attr_int, nsteps)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    pop = toolbox.population(n=nindividuals)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register('avg', np.mean)
    stats.register('min', np.min)
    stats.register('max', np.max)
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2,
                                       ngen=ngen, stats=stats, halloffame=hof,
                                       verbose=True)
    return hof[0]
