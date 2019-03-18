import os
import json
import random
import multiprocessing
from deap import base, creator, tools, algorithms
import numpy as np
import evaluate as ev
import swmm_mpc as sm


def run_ea(work_dir, config_file, ga_params):
    creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMin)

    pool = multiprocessing.Pool(ga_params['num_cores'])
    toolbox = base.Toolbox()
    toolbox.register('map', pool.map)
    toolbox.register('attr_binary', random.randint, 0, 1)
    toolbox.register('mate', tools.cxTwoPoint)
    toolbox.register('mutate', tools.mutFlipBit, indpb=0.20)
    toolbox.register('select', tools.selTournament, tournsize=6)
    toolbox.register('evaluate', ev.evaluate)

    policy_len = get_policy_length(sm.run.ctl_str_ids,
                                   sm.run.n_ctl_steps)
    toolbox.register('individual', tools.initRepeat, creator.Individual,
                     toolbox.attr_binary, policy_len)

    # read from the json file to initialize population if exists
    # (not first time)
    pop_file = os.path.join(work_dir, "population.json")
    if os.path.isfile(pop_file):
        toolbox.register("pop_guess", init_population, creator.Individual,
                         pop_file)
        pop = toolbox.pop_guess()
    else:
        toolbox.register('population', tools.initRepeat, list,
                         toolbox.individual)
        pop = toolbox.population(n=ga_params.get('nindividuals', 25))

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register('avg', np.mean)
    stats.register('min', np.min)
    stats.register('max', np.max)
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2,
                                       ngen=ga_params.get('ngen', 7),
                                       stats=stats,
                                       halloffame=hof, verbose=True)
    seed_next_population(hof[0], ga_params.get('nindividuals', 25),
                         sm.run.ctl_str_ids, pop_file, sm.run.n_ctl_steps)
    min_cost = min(logbook.select("min"))
    return hof[0], min_cost


def write_pop_to_file(population, pop_file):
    """
    write a population of individuals to json file
    """
    with open(pop_file, 'w') as myfile:
        json.dump(population, myfile)


# def evaluate_ea(individual):
    # cost = ev.evaluate(individual)
    # return cost,


def mutate_pop(best_policy, nindividuals, control_str_ids, n_steps):
    """
    mutate the best policy of the current time step
    """
    list_of_inds = []
    for i in range(nindividuals):
        # split because there may be more than one control
        split_lists = ev.split_gene_by_ctl_ts(best_policy, control_str_ids,
                                              n_steps)
        mutated_ind = []
        for seg_by_ctl in split_lists:
            setting_length = len(seg_by_ctl[0])
            # disregard the first control step since we need future policy
            seg_by_ctl = seg_by_ctl[1:]
            # set setting length to one in case there is only one setting
            # mutate the remaining settings
            mutated_ctl_segment = []
            for seg_by_ts in seg_by_ctl:
                tools.mutFlipBit(seg_by_ts, 0.2)
                mutated_ctl_segment.extend(seg_by_ts)
            # add a random setting for the last time step in the future policy
            rand_sttng = [random.randint(0, 1) for i in range(setting_length)]
            mutated_ctl_segment.extend(rand_sttng)
            # add the new policy for the control structure to the overall pol
            mutated_ind.extend(mutated_ctl_segment)
        # don't add the new indivi to the pop if identical indivi already there
        if mutated_ind not in list_of_inds:
            list_of_inds.append(mutated_ind)
    return list_of_inds


def seed_next_population(best_policy, nindividuals, control_str_ids, pop_file,
                         n_steps):
    """
    seed the population for the next time step using the best policy from the
    current time step as the basis.
    best_policy:    [list] binary string representing best policy of current ts
    nindividuals:   [int]  number of individuals per generation in GA
    control_str_ids:[list] list of control ids (e.g., ['ORIFICE r1', ...])
    pop_file:       [string] name of file where the next seed pop will be saved
    n_steps:        [int] number of control time steps
    return:         [list] mutated population

    """
    mutated_pop = mutate_pop(best_policy, nindividuals, control_str_ids,
                             n_steps)

    # in case there were duplicates after mutating,
    # fill the rest of the population with random individuals
    while len(mutated_pop) < nindividuals:
        rand_ind = []
        for i in range(len(best_policy)):
            rand_ind.append(random.randint(0, 1))
        if rand_ind not in mutated_pop:
            mutated_pop.append(rand_ind)
    write_pop_to_file(mutated_pop, pop_file)

    return mutated_pop


def init_population(ind_init, filename):
    """
    create initial population from json file
    ind_init:   [class] class that and individual will be assigned to
    filename:   [string] string of filename from which pop will be read
    returns:    [list] list of Individual objects
    """
    with open(filename, "r") as pop_file:
        contents = json.load(pop_file)
    return list(ind_init(c) for c in contents)


def get_policy_length(control_str_ids, n_control_steps):
    """
    get the length of the policy. ASSUMPTION - PUMP controls are binary 1 BIT,
    ORIFICE and WEIR are 3 BITS
    returns:    [int] the number of total control decisions in the policy
    """
    pol_len = 0
    for ctl_id in control_str_ids:
        ctl_type = ctl_id.split()[0]
        if ctl_type == 'ORIFICE' or ctl_type == 'WEIR':
            pol_len += 3*n_control_steps
        elif ctl_type == 'PUMP':
            pol_len += n_control_steps
    return pol_len
