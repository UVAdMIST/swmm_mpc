import string
import sys
import random
import os
from shutil import copyfile
import subprocess
from rpt_ele import rpt_ele
import update_process_model_input_file as up


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


def evaluate(individual, hs_file_path, process_file_path, sim_dt,
             control_time_step, n_control_steps, control_str_ids,
             node_flood_weight_dict, target_depth_dict, flood_weight,
             dev_weight):
    FNULL = open(os.devnull, 'w')
    # make process model tmp file
    rand_string = ''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(9))

    # make a copy of the process model input file
    process_file_dir, process_file_name = os.path.split(process_file_path)
    tmp_process_base = process_file_name.replace('.inp',
                                                 '_tmp_{}_{}'.format(
						 sim_dt,
						 rand_string
						 ))
    tmp_process_inp = os.path.join(process_file_dir,
                                   tmp_process_base + '.inp')
    tmp_process_rpt = os.path.join(process_file_dir,
                                   tmp_process_base + '.rpt')
    copyfile(process_file_path, tmp_process_inp)

    # make copy of hs file
    hs_file_name = os.path.split(hs_file_path)[1]
    tmp_hs_file_name = hs_file_name.replace('.hsf',
                                            '_{}.hsf'.format(rand_string))

    tmp_hs_file = os.path.join(process_file_dir, tmp_hs_file_name)
    copyfile(hs_file_path, tmp_hs_file)

    # convert individual to percentages
    fmted_policies = gene_to_policy_dict(individual, control_str_ids,
                                         n_control_steps)

    # update controls
    up.update_controls_and_hotstart(tmp_process_inp,
                                    control_time_step,
                                    fmted_policies,
                                    tmp_hs_file)

    # run the swmm model
    if os.name == 'nt':
        swmm_exe_cmd = 'swmm5.exe'
    elif sys.platform.startswith('linux'):
        swmm_exe_cmd = 'swmm5'
    cmd = '{} {} {}'.format(swmm_exe_cmd, tmp_process_inp,
                            tmp_process_rpt)
    subprocess.call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

    # read the output file
    rpt = rpt_ele('{}'.format(tmp_process_rpt))

    # get flooding costs
    node_flood_cost = get_flood_cost(rpt, node_flood_weight_dict)

    # get deviation costs
    deviation_cost = get_deviation_cost(rpt, target_depth_dict)

    # convert the contents of the output file into a cost
    cost = flood_weight*node_flood_cost + dev_weight*deviation_cost
    os.remove(tmp_process_inp)
    os.remove(tmp_process_rpt)
    os.remove(tmp_hs_file)
    return cost,
