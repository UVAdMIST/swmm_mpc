import string
import random
import os
from shutil import copyfile
import subprocess
from scoop import shared
from scoop.fallbacks import NotStartedProperly
from rpt_ele import rpt_ele
import update_process_model_input_file as up
import swmm_mpc as sm


def evaluate(individual):
    FNULL = open(os.devnull, 'w')
    # make process model tmp file
    rand_string = ''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(9))

    # get global variables, from scoop if started by scoop
    try:
        inp_process_file_base = shared.getConst('inp_process_file_base')
        inp_process_file_path = shared.getConst('inp_process_file_path')
        inp_file_dir = shared.getConst('inp_file_dir')
        inp_process_file_inp = shared.getConst('inp_process_file_inp')
        control_time_step = shared.getConst('control_time_step')
        n_control_steps = shared.getConst('n_control_steps')
        control_str_ids = shared.getConst('control_str_ids')
        node_flood_weight_dict = shared.getConst('node_flood_weight_dict')
        target_depth_dict = shared.getConst('target_depth_dict')
    except NotStartedProperly:
        inp_process_file_base = sm.inp_process_file_base_g
        inp_process_file_path = sm.inp_process_file_path_g
        inp_file_dir = sm.inp_file_dir_g
        inp_process_file_inp = sm.inp_process_file_inp_g
        control_time_step = sm.control_time_step_g
        n_control_steps = sm.n_control_steps_g
        control_str_ids = sm.control_str_ids_g
        node_flood_weight_dict = sm.node_flood_weight_dict_g
        target_depth_dict = sm.target_depth_dict_g

    # make a copy of the process model input file
    inp_tmp_process_file_base = inp_process_file_base + '_tmp' +\
        rand_string
    inp_tmp_process_inp = os.path.join('/tmp/',
                                       inp_tmp_process_file_base + '.inp')
    inp_tmp_process_rpt = os.path.join('/tmp/',
                                       inp_tmp_process_file_base + '.rpt')
    copyfile(inp_process_file_path, inp_tmp_process_inp)

    # make copy of hs file
    hs_filename = up.read_hs_filename(inp_process_file_path)
    tmp_hs_file_name = hs_filename.replace('.hsf',
                                           '_tmp_{}.hsf'.format(rand_string))
    tmp_hs_file = os.path.join('/tmp/', tmp_hs_file_name)
    copyfile(os.path.join(inp_file_dir, hs_filename), tmp_hs_file)

    # convert individual to percentages
    indivi_percentage = [setting/10. for setting in individual]
    policies = sm.fmt_control_policies(indivi_percentage, control_str_ids,
                                       n_control_steps)

    # update controls
    up.update_controls_and_hotstart(inp_tmp_process_inp,
                                    control_time_step,
                                    policies,
                                    tmp_hs_file)

    # run the swmm model
    cmd = 'swmm5 {} {}'.format(inp_tmp_process_inp, inp_tmp_process_rpt)
    subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

    # read the output file
    rpt = rpt_ele('{}'.format(inp_tmp_process_rpt))
    node_flood_costs = []

    # get flooding costs
    if not rpt.flooding_df.empty and node_flood_weight_dict:
        for nodeid, weight in node_flood_weight_dict.iteritems():
            # try/except used here in case there is no flooding for one or
            # more of the nodes
            try:
                # flood volume is in column, 5
                node_flood_volume = float(rpt.flooding_df.loc[nodeid, 5])
                node_flood_cost = (weight*node_flood_volume)
                node_flood_costs.append(node_flood_cost)
            except:
                pass
    else:
        node_flood_costs.append(rpt.total_flooding)

    # get deviation costs
    node_deviation_costs = []
    if target_depth_dict:
        for nodeid, data in target_depth_dict.iteritems():
            avg_dev = abs(data['target'] - float(rpt.depth_df.loc[nodeid, 2]))
            weighted_deviation = avg_dev*data['weight']
            node_deviation_costs.append(weighted_deviation)

    # convert the contents of the output file into a cost
    cost = sum(node_flood_costs) + sum(node_deviation_costs)
    os.remove(inp_tmp_process_inp)
    os.remove(inp_tmp_process_rpt)
    os.remove(tmp_hs_file)
    return cost,
