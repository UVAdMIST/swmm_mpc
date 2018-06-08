from deap import base, creator, tools, algorithms
import pandas as pd
import numpy as np
from evaluate import evaluate
from scoop import futures
import datetime
import random


creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
creator.create('Individual', list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register('map', futures.map)
toolbox.register('attr_int', random.randint, 0, 10)
toolbox.register('evaluate', evaluate)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutUniformInt, low=0, up=10, indpb=0.10)
toolbox.register('select', tools.selTournament, tournsize=6)


def run_ea(nsteps, ngen, nindividuals):
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
    f = open('../data/log.txt', 'a')
    f.write('run started: {}'.format(beg_time))
    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2,
                                       ngen=ngen, stats=stats, halloffame=hof,
                                       verbose=True)
    end_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')
    f.write('run ended: {}\n'.format(end_time))
    f.close()

    df = pd.DataFrame(logbook)
    df.to_csv('../data/results_{}csv'.format(end_time, index=False))

    f = open('../data/hof.txt', 'a')
    for h in hof:
        f.write('hof for {}:{}    fitness:{}\n'.format(end_time, h, h.fitness))
    f.close()
    return h

if __name__ == '__main__':
    run_ea()
