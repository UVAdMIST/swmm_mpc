import string
import random
import os
from shutil import copyfile
import subprocess
from rpt_ele import rpt_ele
import update_process_model_input_file as up
import swmm_mpc as sm


def evaluate(individual):
    FNULL = open(os.devnull, 'w')
    # make process model tmp file
    rand_string = ''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(9))
    inp_tmp_process_file_base = sm.inp_process_file_base_g + '_tmp' +\
        rand_string
    inp_tmp_process_inp = os.path.join(sm.inp_file_dir_g,
                                       inp_tmp_process_file_base + '.inp')
    inp_tmp_process_rpt = os.path.join(sm.inp_file_dir_g,
                                       inp_tmp_process_file_base + '.rpt')
    copyfile(sm.inp_process_file_inp_g, inp_tmp_process_inp)

    # make copy of hs file
    hs_filename = up.read_hs_filename(sm.inp_process_file_inp_g)
    tmp_hs_file_name = hs_filename.replace('.hsf',
                                           '_tmp_{}.hsf'.format(rand_string))
    tmp_hs_file = os.path.join(sm.inp_file_dir_g, tmp_hs_file_name)
    copyfile(os.path.join(sm.inp_file_dir_g, hs_filename), tmp_hs_file)

    # convert individual to percentages
    indivi_percentage = [setting/10. for setting in individual]
    policies = sm.fmt_control_policies(indivi_percentage, sm.control_str_ids_g,
                                       sm.n_control_steps_g)

    # update controls
    up.update_controls_and_hotstart(inp_tmp_process_inp,
                                    sm.control_time_step_g,
                                    policies,
                                    tmp_hs_file)

    # run the swmm model
    cmd = 'swmm5 {0}.inp {0}.rpt'.format(inp_tmp_process_file_base)
    subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

    # read the output file
    rpt = rpt_ele('{}.rpt'.format(inp_tmp_process_file_base))
    node_flood_costs = []

    # get flooding costs
    if not rpt.flooding_df.empty and sm.node_flood_weight_dict_g:
        for nodeid, weight in sm.node_flood_weight_dict_g.iteritems():
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
    if sm.target_depth_dict_g:
        for nodeid, data in sm.target_depth_dict_g.iteritems():
            avg_dev = abs(data['target'] - float(rpt.depth_df.loc[nodeid, 2]))
            weighted_deviation = avg_dev*data['weight']
            node_deviation_costs.append(weighted_deviation)

    # convert the contents of the output file into a cost
    cost = sum(node_flood_costs) + sum(node_deviation_costs)
    os.remove(inp_tmp_process_inp)
    os.remove(inp_tmp_process_rpt)
    os.remove(tmp_hs_file)
    return cost,
