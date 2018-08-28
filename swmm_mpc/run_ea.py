import os
import json
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
           inp_process_file_path, control_time_step, n_control_steps,
           control_str_ids, node_flood_weight_dict, target_depth_dict,
           flood_weight, dev_weight):
    toolbox.register('evaluate',
                     ev.evaluate,
                     hs_file_path=hs_file_path,
                     process_file_path=inp_process_file_path,
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

    # read from the json file to initialize population if exists
    # (not first time)
    if os.path.isfile("population.json"):
        toolbox.register("pop_guess", init_population, list,
                         creator.Individual, "population.json")
        pop = toolbox.pop_guess()
    else:
        toolbox.register('population', tools.initRepeat, list,
                         toolbox.individual)
        pop = toolbox.population(n=nindividuals)

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register('avg', np.mean)
    stats.register('min', np.min)
    stats.register('max', np.max)
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2,
                                       ngen=ngen, stats=stats, halloffame=hof,
                                       verbose=True)
    seed_next_population(hof[0], nindividuals)
    return hof[0]


def write_pop_to_file(population):
    pop_filename = 'population.json'
    with open(pop_filename, 'w') as myfile:
        json.dump(population, myfile) 


def seed_next_population(best_policy, nindividuals):
    list_of_inds = []
    for i in range(nindividuals):
        b = list(best_policy)
        b = b[1:]
        tools.mutUniformInt(b, 0, 10, 0.2)
        b.append(random.randint(0, 10))
        if b not in list_of_inds:
            list_of_inds.append(b)

    while len(list_of_inds) < nindividuals:
        rand_ind = []
        for i in range(len(best_policy)):
            rand_ind.append(random.randint(0, 10))
        if rand_ind not in list_of_inds:
            list_of_inds.append(rand_ind)
    write_pop_to_file(list_of_inds)
    return list_of_inds



def init_population(pcls, ind_init, filename):
    with open(filename, "r") as pop_file:
        contents = json.load(pop_file)
    return pcls(ind_init(c) for c in contents)
