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
    def __init__(self, inp_file_path, control_horizon, control_time_step, control_str_ids, 
            results_dir, target_depth_dict=None, node_flood_weight_dict=None):
        '''
        inp_file_path: [string] path to .inp file 
        control_horizon: [number] control horizon in hours
        control_time_step: [number] control time step in seconds
        control_str_ids: [list of strings] ids of control structures for which controls policies 
                         will be found. e.g., [ORIFICE R1, ORIFICE R2]
        results_dir: [string] directory where the results will be written
        target_depth_dict: [dict] dictionary where the keys are the nodeids and the values are a 
                           dictionary. The inner dictionary has two keys, 'target', and 'weight'. 
                           These values specify the target depth for the nodeid and the weight given 
                           to that in the cost function. e.g., {'St1': {'target': 1, 'weight': 0.1}} 
        node_flood_weight_dict: [dict] dictionary where the keys are the node ids and the values are 
                                the relative weights for weighting the amount of flooding for a 
                                particular node. e.g., {'st1': 10, 'J3': 1}
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

        self.toolbox = base.Toolbox()
        self.toolbox.register('map', futures.map)
        self.toolbox.register('attr_int', random.randint, 0, 10)
        self.toolbox.register('evaluate', self.evaluate)
        self.toolbox.register('mate', tools.cxTwoPoint)
        self.toolbox.register('mutate', tools.mutUniformInt, low=0, up=10, indpb=0.10)
        self.toolbox.register('select', tools.selTournament, tournsize=6)

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
                nsteps = self.n_control_steps * len(self.control_str_ids)

                best_policy = self.run_ea(self.n_control_steps)
                best_policy_fmt = self.fmt_control_policies(best_policy_per)
                for control_id, policy in best_policy_fmt.iteritems():
                    best_policy_per = policy[0]/10.
                    best_policy_ts.append({'setting_{}'.format(control_id):best_policy_per, 
                    'datetime':current_date_time}) 
                    
                    # implement best policy
                    # from for example "ORIFICE R1" to "R1"
                    control_id_short = control_id.split()[-1]
                    link_obj[control_id_short].target_setting = best_bolicy_per

                end = time.time()
                print ('elapsed time: {}'.format(end-start))

        control_settings_df = pd.DataFrame(best_policy_ts)
        control_settings_df.to_csv('{}control_results_{}.csv'.format(beg_time, self.results_dir))

    def fmt_control_policies(self, control_array):
        policies = dict()
        for i, control_id in enumerate(self.control_str_ids):
            policies[control_id] = control_array[i*self.n_control_steps: (i+1)*self.n_control_steps]
        return policies

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
        policies = self.fmt_control_policies(indivi_percentage)

        # update controls
        update_controls_and_hotstart(inp_tmp_process_inp, self.control_time_step, policies, 
                tmp_hs_file)

        # run the swmm model
        cmd = 'swmm5 {0}.inp {0}.rpt'.format(inp_tmp_process_file_base)
        subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

        # read the output file
        rpt = rpt_ele('{}.rpt'.format(inp_tmp_process_file_base))
        node_flood_costs = []

        # get flooding costs
        if not rpt.flooding_df.empty:
            for nodeid, weight in self.node_flood_weight_dict.iteritems():
                # try/except used here in case there is no flooding for one or more of the nodes
                try:
                    # flood volume is in column, 5
                    node_flood_volume = float(rpt.flooding_df.loc[nodeid, 5])
                    node_flood_cost = (weight*node_flood_volume)
                    node_flood_costs.append(node_flood_cost)
                except:
                    pass

        # get deviation costs
        node_deviation_costs = []
        if self.target_depth_dict:
            for nodeid, data in self.target_depth_dict:
                avg_dev_fr_tgt_st_lvl = abs(data['target'] - float(rpt.depth_df.loc[nodeid, 2]))
                weighted_deviation = avg_dev_fr_tgt_st_lvl*data['weight']
                node_deviation_costs.append(weighted_deviation)

        # convert the contents of the output file into a cost
        cost = sum(node_flood_costs) + sum(node_deviation_costs)
        os.remove(inp_tmp_process_inp)
        os.remove(inp_tmp_process_rpt)
        os.remove(tmp_hs_file)
        return cost,


    def run_ea(self, nsteps):
        # initialize ea things

        self.toolbox.register('individual', tools.initRepeat, creator.Individual, 
                self.toolbox.attr_int, nsteps)
        self.toolbox.register('population', tools.initRepeat, list, self.toolbox.individual)

        ngen = 7
        nindividuals = 100
        pop = self.toolbox.population(n=nindividuals)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register('avg', np.mean)
        stats.register('min', np.min)
        stats.register('max', np.max)
        beg_time = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M')
        pop, logbook = algorithms.eaSimple(pop, self.toolbox, cxpb=0.5, mutpb=0.2, ngen=ngen, 
                                           stats=stats, halloffame=hof, verbose=True)

        return hof[0]

