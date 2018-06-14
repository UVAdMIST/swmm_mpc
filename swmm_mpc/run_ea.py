import datetime
import random
from deap import base, creator, tools, algorithms
import pandas as pd
import numpy as np
from scoop import futures
import evaluate as ev


creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
creator.create('Individual', list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register('map', futures.map)
toolbox.register('attr_int', random.randint, 0, 10)
toolbox.register('evaluate', ev.evaluate)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutUniformInt, low=0, up=10, indpb=0.10)
toolbox.register('select', tools.selTournament, tournsize=6)


def run_ea(nsteps, ngen, nindividuals, verbose_results, data_dir):
    toolbox.register('individual', tools.initRepeat, creator.Individual,
                     toolbox.attr_int, nsteps)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    pop = toolbox.population(n=nindividuals)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register('avg', np.mean)
    stats.register('min', np.min)
    stats.register('max', np.max)
    beg_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2,
                                       ngen=ngen, stats=stats, halloffame=hof,
                                       verbose=True)
    end_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')

    return hof[0]
