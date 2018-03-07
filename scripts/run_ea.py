from deap import base, creator, tools, algorithms
from swmmio import swmmio
import random
import os
from shutil import copyfile
import subprocess
from update_process_model_input_file import update_controls
from run_swmm_mpc import input_process_file_inp, input_process_file_base, control_time_step, \
        control_str_id

FNULL = open(os.devnull, 'w')

def evaluate(individual):
    # make process model tmp file
    input_tmp_process_file_base = input_process_file_base + "_tmpi"
    input_tmp_process_inp = input_tmp_process_file_base + ".inp"
    copyfile(input_process_file_inp, input_tmp_process_inp)

    # convert individual to percentages
    indivi_percentage = [setting/10. for setting in individual]
    policies = {control_str_id: indivi_percentage}

    # update controls
    update_controls(input_tmp_process_inp, control_time_step, policies)

    # run the swmm model
    cmd = "swmm5.exe {0}.inp {0}.rpt".format(input_tmp_process_file_base)
    subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

    # read the output file
    mymodel = swmmio.Model(input_tmp_process_inp)
    nodes = mymodel.nodes()
    nodes.fillna(0, inplace=True)
    storage_flood_volume = nodes.loc['St1']['TotalFloodVol']
    node_flood_volume = nodes.loc['J2']['TotalFloodVol']
    target_storage_level = 1.
    avg_dev_fr_tgt_st_lvl = nodes.loc['St1', 'AvgDepth'] - target_storage_level

    # convert the contents of the output file into a cost
    cost = 2 * storage_flood_volume**3 + node_flood_volume*2 + avg_dev_fr_tgt_st_lvl 
    # os.remove(input_tmp_process_inp)
    # os.remove(input_tmp_process_file_base + ".rpt")
    return cost

creator.create('FitnessMin', base.Fitness, weights=(-1.0,))
creator.create('Individual', list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("attr_int", random.randint, 0, 10)
toolbox.register("individual", tools.initRepeat, creator.Individual,
                 toolbox.attr_int, 24)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
toolbox.register('evaluate', evaluate)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.10)
toolbox.register("select", tools.selTournament, tournsize=6)
