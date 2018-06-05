import string
import numpy as np
import random
import subprocess
import time
import os
import datetime
from deap import base, creator, tools, algorithms
from scoop import futures
from rpt_ele import rpt_ele
from update_process_model_input_file import update_controls_and_hotstart, read_hs_filename, \
    update_process_model_file
import pyswmm
from pyswmm import Simulation, Nodes, Links
from shutil import copyfile
import pandas as pd


class swmm_mpc(object):
    def __init__(self, inp_file_path, control_horizon, control_time_step, control_str_ids, results_dir):
        '''
        inp_file_path:
        control_horizon: [number] control horizon in hours
        control_time_step: [number] control time step in seconds
        control_str_ids:
        results_dir:
        '''
        # full file path
        self.inp_file_path = os.path.abspath(inp_file_path)
        # the input directory and the file name
        self.inp_file_dir, self.inp_file_name = os.path.split(self.inp_file_path)
        # the process file name with no extension
        self.inp_process_file_base = self.inp_file_name.replace('.inp', '_process')
        # the process .inp file name 
        self.inp_process_file_inp = self.inp_process_file_base + '.inp'
        # copy input file to process file name
        copyfile(self.inp_file_path, os.path.join(self.inp_file_dir, self.inp_process_file_inp))

        pyswmm.lib.use('libswmm5_hs.so')

        self.control_horizon = float(control_horizon) # hr
        self.control_time_step = float(control_time_step) # sec
        self.n_control_steps = int(control_horizon*3600/control_time_step)
        self.control_str_ids = control_str_ids
        self.results_dir = results_dir

        creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
        creator.create('Individual', list, fitness=creator.FitnessMin)

        toolbox = base.Toolbox()
        toolbox.register('map', futures.map)
        toolbox.register('attr_int', random.randint, 0, 10)
        toolbox.register('evaluate', self.evaluate)
        toolbox.register('mate', tools.cxTwoPoint)
        toolbox.register('mutate', tools.mutUniformInt, low=0, up=10, indpb=0.10)
        toolbox.register('select', tools.selTournament, tournsize=6)

    def run_swmm_mpc(self):
        beg_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')
        start = time.time()
        best_policy_ts = []
        with Simulation(self.inp_file_path) as sim:
            sim.step_advance(self.control_time_step)
            for step in sim:
                # get most current system states
                current_date_time = sim.current_time

                dt_hs_file = '{}.hsf'.format(current_date_time.strftime('%Y%m%d%H%M'))
                print current_date_time
                dt_hs_path = os.path.join(self.inp_file_dir, dt_hs_file)
                sim.save_hotstart(dt_hs_path)

                link_obj = Links(sim)

                # update the process model with the current states
                update_process_model_file(self.inp_process_file_inp, current_date_time, dt_hs_file)

                # get num control steps remaining
                # nsteps = get_nsteps_remaining(sim)
                nsteps = self.n_control_steps

                # if nsteps > 1:
                    # # run prediction to get best policy 
                best_policy = self.run_ea(self.n_control_steps)
                best_policy_per = best_policy[0]/10.
                best_policy_ts.append({'setting_{}'.format(self.control_str_ids):best_policy_per, 
                    'datetime':current_date_time})

                # implement best policy

                end = time.time()
                print ('elapsed time: {}'.format(end-start))

        control_settings_df = pd.DataFrame(best_policy_ts)
        control_settings_df.to_csv('{}control_results_{}.csv'.format(beg_time, self.results_dir))

    def evaluate(self, individual):
        FNULL = open(os.devnull, 'w')
        # make process model tmp file
        rand_string = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(9))
        inp_tmp_process_file_base = self.inp_process_file_base + '_tmp' + rand_string
        inp_tmp_process_inp = os.path.join(self.inp_file_dir, inp_tmp_process_file_base + '.inp')
        inp_tmp_process_rpt = os.path.join(self.inp_file_dir, inp_tmp_process_file_base + '.rpt')
        copyfile(self.inp_process_file_inp, inp_tmp_process_inp)

        # make copy of hs file
        hs_filename = read_hs_filename(self.inp_process_file_inp)
        tmp_hs_file_name = hs_filename.replace('.hsf', '_tmp_{}.hsf'.format(rand_string))
        tmp_hs_file = os.path.join(self.inp_file_dir, tmp_hs_file_name)
        copyfile(os.path.join(self.inp_file_dir, hs_filename), tmp_hs_file)

        # convert individual to percentages
        indivi_percentage = [setting/10. for setting in individual]
        policies = {self.control_str_ids: indivi_percentage}

        # update controls
        update_controls_and_hotstart(inp_tmp_process_inp, self.control_time_step, policies, 
                tmp_hs_file)

        # run the swmm model
        cmd = 'swmm5 {0}.inp {0}.rpt'.format(inp_tmp_process_file_base)
        subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

        # read the output file
        rpt = rpt_ele('{}.rpt'.format(inp_tmp_process_file_base))
        node_weights = {'St1': 100, 'J3': 10}
        node_flood_costs = []

        if not rpt.flooding_df.empty:
            for nodeid, weight in node_weights.iteritems():
                try:
                    node_flood_volume = float(rpt.flooding_df.loc[nodeid, 5])
                    node_flood_cost = (weight*node_flood_volume)
                    node_flood_costs.append(node_flood_cost)
                except:
                    pass

        target_storage_level = 1.
        avg_dev_fr_tgt_st_lvl = target_storage_level - float(rpt.depth_df.loc['St1', 2])
        if avg_dev_fr_tgt_st_lvl < 0:
            avg_dev_fr_tgt_st_lvl = 0

        deviation_cost = avg_dev_fr_tgt_st_lvl/10.

        # convert the contents of the output file into a cost
        cost = sum(node_flood_costs) + deviation_cost
        os.remove(inp_tmp_process_inp)
        os.remove(inp_tmp_process_rpt)
        os.remove(tmp_hs_file)
        return cost,


    def run_ea(self, nsteps):
        # initialize ea things

        toolbox.register('individual', tools.initRepeat, creator.Individual, toolbox.attr_int, nsteps)
        toolbox.register('population', tools.initRepeat, list, toolbox.individual)

        ngen = 7
        nindividuals = 100
        pop = toolbox.population(n=nindividuals)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register('avg', np.mean)
        stats.register('min', np.min)
        stats.register('max', np.max)
        beg_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')
        pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=ngen, stats=stats,
                                           halloffame=hof, verbose=True)

        return hof[0]

