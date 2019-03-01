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
    if bit == 1:
        return "ON"
    elif bit == 0:
        return "OFF"


def split_list(a_list, n):
    """
    split one list into n lists of equal size. In this case, we are splitting
    the list that represents all of the policies so that each control structure 
    has its own list
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
    ASSUMPTION: 3 bits for ORIFICE or WEIR, 1 for PUMP
    """
    fmted_policies = dict()
    for control_id in control_str_ids:
        control_type = control_id.split()[0]
        if control_type == 'ORIFICE' or control_type == 'WEIR':
            bits_per_type = 3
            # get the number of control elements that are for the current ctl
            n_ctl_elements = bits_per_type*n_control_steps
            # take that number of elements from the overall gene string
            gene_seg = gene[:n_ctl_elements]
            # split that into lists, one for each ctl time step
            gene_seg_split = split_list(gene_seg, n_control_steps)
            # change the lists of bits into percent openings
            fmtd_seg = [bits_to_perc(seg) for seg in gene_seg_split]
        elif control_type == 'PUMP':
            bits_per_type = 1
            n_ctl_elements = bits_per_type*n_control_steps
            gene_seg = gene[:n_ctl_elements]
            fmtd_seg = [bit_to_on_off(bit) for bit in gene_seg]
        # move the beginning of the gene to the end of the current ctl segment
        gene = gene[n_ctl_elements:]
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
