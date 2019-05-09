import string
import numpy as np
import sys
import random
import os
from shutil import copyfile
import subprocess
from rpt_ele import rpt_ele
import update_process_model_input_file as up
import swmm_mpc as sm


def get_flood_cost_from_dict(rpt, node_flood_weight_dict):
    node_flood_costs = []
    for nodeid, weight in node_flood_weight_dict.iteritems():
        # if user put "Node J3" for nodeid instead of just "J3" make \
        # nodeid "J3"
        if len(nodeid.split()) > 0:
            nodeid = nodeid.split()[-1]
        # try/except used here in case there is no flooding for one or \
        # more of the nodes
        if nodeid not in rpt.node_ids:
            print("warning node {} is not in model".format(nodeid))
        try:
            # flood volume is in column, 5
            node_flood_volume = float(rpt.flooding_df.loc[nodeid, 5])
            node_flood_cost = (weight*node_flood_volume)
            node_flood_costs.append(node_flood_cost)
        except:
            pass
    return sum(node_flood_costs)


def get_flood_cost(rpt, node_flood_weight_dict):
    if rpt.total_flooding > 0 and node_flood_weight_dict:
        return get_flood_cost_from_dict(rpt, node_flood_weight_dict)
    else:
        return rpt.total_flooding


def get_deviation_cost(rpt, target_depth_dict):
    node_deviation_costs = []
    if target_depth_dict:
        for nodeid, data in target_depth_dict.iteritems():
            depth = rpt.get_ele_df(nodeid)['Depth']
            depth_dev = abs(depth - data['target'])
            avg_dev = depth_dev.sum()/len(depth_dev)
            weighted_deviation = avg_dev*data['weight']
            node_deviation_costs.append(weighted_deviation)

    return sum(node_deviation_costs)


def get_cost(rpt_file, node_flood_weight_dict, flood_weight, target_depth_dict,
             dev_weight):
    # read the output file
    rpt = rpt_ele('{}'.format(rpt_file))

    # get flooding costs
    node_fld_cost = get_flood_cost(rpt, node_flood_weight_dict)

    # get deviation costs
    deviation_cost = get_deviation_cost(rpt, target_depth_dict)

    # convert the contents of the output file into a cost
    cost = flood_weight*node_fld_cost + dev_weight*deviation_cost
    return cost


def bits_to_decimal(bits):
    bits_as_string = "".join(str(i) for i in bits)
    return float(int(bits_as_string, 2))


def bits_max_val(bit_len):
    bit_ones = [1 for i in range(bit_len)]
    return bits_to_decimal(bit_ones)


def bits_to_perc(bits):
    bit_dec = bits_to_decimal(bits)
    max_bits = bits_max_val(len(bits))
    return round(bit_dec/max_bits, 3)


def bit_to_on_off(bit):
    """
    convert single bit to "ON" or "OFF"
    bit:    [int] or [list]
    """
    if type(bit) == list:
        if len(bit) > 1:
            raise ValueError('you passed more than one bit to this fxn')
        else:
            bit = bit[0]
    if bit == 1:
        return "ON"
    elif bit == 0:
        return "OFF"
    else:
        raise ValueError('was expecting 1 or 0 and got {}'.format(bit))


def split_gene_by_ctl_ts(gene, control_str_ids, n_steps):
    """
    split a list of bits representing a gene into the bits that correspond with
    each control id according to the control type for each time step
    ASSUMPTION: 3 bits for ORIFICE or WEIR, 1 for PUMP
    gene:               [list] bits for a gene (e.g., [1, 0, 1, 1, 1, 0, 0, 1])
    control_str_ids:    [list] control ids (e.g., ['ORIFICE r1', 'PUMP p1'])
    n_steps:            [int] number of control steps (e.g., 2)
    returns:            [list of lists] [[[1, 0, 1], [1, 1, 0]], [[0], [1]]]
    """
    split_gene = []
    for control_id in control_str_ids:
        # get the control type (i.e. PUMP, WEIR, ORIFICE)
        control_type = control_id.split()[0]
        if control_type == 'ORIFICE' or control_type == 'WEIR':
            bits_per_type = 3
            # get the number of control elements that are for the current ctl
        elif control_type == 'PUMP':
            bits_per_type = 1
        # the number of bits per control structure
        n_bits = bits_per_type*n_steps
        # get the segment for the control
        gene_seg = gene[:n_bits]
        # split to get the different time steps
        gene_seg_per_ts = split_list(gene_seg, n_steps)
        # add the gene segment to the overall list
        split_gene.append(gene_seg_per_ts)
        # move the beginning of the gene to the end of the current ctl segment
        gene = gene[n_bits:]
    return split_gene


def split_list(a_list, n):
    """
    split one list into n lists of equal size. In this case, we are splitting
    the list that represents the policy of a single each control structure
    so that each time step is separate
    """
    portions = len(a_list)/n
    split_lists = []
    for i in range(n):
        split_lists.append(a_list[i*portions: (i+1)*portions])
    return split_lists


def gene_to_policy_dict(gene, control_str_ids, n_control_steps):
    """
    converts a gene to a policy dictionary that with the format specified in
    up.update_controls_and_hotstart
    format a policy given the control_str_ids and splitted_gene
    control_str_ids:    [list] control ids (e.g., ['ORIFICE r1', 'PUMP p1'])
    splitted_gene:      [list of lists] [[[1, 0, 1], [1, 1, 0]], [[0], [1]]]
    returns:            [dict] (e.g., {'ORIFICE r1'}
    """
    fmted_policies = dict()
    splitted_gene = split_gene_by_ctl_ts(gene, control_str_ids,
                                         n_control_steps)
    for i, control_id in enumerate(control_str_ids):
        control_type = control_id.split()[0]
        seg = splitted_gene[i]
        if control_type == 'ORIFICE' or control_type == 'WEIR':
            # change the lists of bits into percent openings
            fmtd_seg = [bits_to_perc(setting) for setting in seg]
        elif control_type == 'PUMP':
            # change the lists of bits into on/off
            fmtd_seg = [bit_to_on_off(bit[0]) for bit in seg]
        fmted_policies[control_id] = fmtd_seg
    return fmted_policies


def list_to_policy(policy, control_str_ids, n_control_steps):
    """
    ASSUMPTION: round decimal number to BOOLEAN
    """
    split_policies = split_list(policy, len(control_str_ids))
    fmted_policies = dict()
    for i, control_id in enumerate(control_str_ids):
        control_type = control_id.split()[0]
        if control_type == 'ORIFICE' or control_type == 'WEIR':
            fmted_policies[control_id] = split_policies[i]
        elif control_type == 'PUMP':
            on_off = [bit_to_on_off(round(p)) for p in split_policies[i]]
            fmted_policies[control_id] = on_off
    return fmted_policies


def format_policies(policy, control_str_ids, n_control_steps, opt_method):
    if opt_method == 'genetic_algorithm':
        return gene_to_policy_dict(policy, control_str_ids, n_control_steps)
    elif opt_method == 'bayesian_opt':
        return list_to_policy(policy, control_str_ids, n_control_steps)


def prep_tmp_files(proc_inp, work_dir):
    # make process model tmp file
    rand_string = ''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(9))

    # make a copy of the process model input file
    tmp_proc_base = proc_inp.replace('.inp',
                                     '_tmp_{}'.format(rand_string))
    tmp_proc_inp = tmp_proc_base + '.inp'
    tmp_proc_rpt = tmp_proc_base + '.rpt'
    copyfile(proc_inp, tmp_proc_inp)

    # make copy of hs file
    hs_file_path = up.read_hs_filename(proc_inp)
    hs_file_name = os.path.split(hs_file_path)[-1]
    tmp_hs_file_name = hs_file_name.replace('.hsf',
                                            '_{}.hsf'.format(rand_string))
    tmp_hs_file_path = os.path.join(sm.run.work_dir, tmp_hs_file_name)
    copyfile(hs_file_path, tmp_hs_file_path)
    return tmp_proc_inp, tmp_proc_rpt, tmp_hs_file_path


def evaluate(*individual):
    """
    evaluate the performance of an individual given the inp file of the process
    model, the individual, the control params (ctl_str_ids, horizon, step),
    and the cost function params (dev_weight/dict, flood weight/dict)
    """
    FNULL = open(os.devnull, 'w')
    # prep files
    tmp_inp, tmp_rpt, tmp_hs = prep_tmp_files(sm.run.inp_process_file_path,
                                              sm.run.work_dir)

    # format policies
    if sm.run.opt_method == 'genetic_algorithm':
        individual = individual[0]
    elif sm.run.opt_method == 'bayesian_opt':
        individual = np.squeeze(individual)

    fmted_policies = format_policies(individual, sm.run.ctl_str_ids,
                                     sm.run.n_ctl_steps, sm.run.opt_method)

    # update controls
    up.update_controls_and_hotstart(tmp_inp,
                                    sm.run.ctl_time_step,
                                    fmted_policies,
                                    tmp_hs)

    # run the swmm model
    if os.name == 'nt':
        swmm_exe_cmd = 'swmm5.exe'
    elif sys.platform.startswith('linux'):
        swmm_exe_cmd = 'swmm5'
    cmd = '{} {} {}'.format(swmm_exe_cmd, tmp_inp,
                            tmp_rpt)
    subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

    # get cost
    cost = get_cost(tmp_rpt,
                    sm.run.node_flood_weight_dict,
                    sm.run.flood_weight,
                    sm.run.target_depth_dict,
                    sm.run.dev_weight)

    os.remove(tmp_inp)
    os.remove(tmp_rpt)
    os.remove(tmp_hs)
    return cost
