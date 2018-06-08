import string
from scoop import futures
import os
from shutil import copyfile
from rpt_ele import rpt_ele
import subprocess
from update_process_model_input_file import update_controls_and_hotstart, read_hs_filename
from run_swmm_mpc import input_process_file_inp, input_process_file_base, control_time_step, \
        control_str_id, input_file_dir

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
    if not rpt.flooding_df.empty and self.node_flood_weight_dict:
        for nodeid, weight in self.node_flood_weight_dict.iteritems():
            # try/except used here in case there is no flooding for one or more of the nodes
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
    if self.target_depth_dict:
        for nodeid, data in self.target_depth_dict.iteritems():
            avg_dev_fr_tgt_st_lvl = abs(data['target'] - float(rpt.depth_df.loc[nodeid, 2]))
            weighted_deviation = avg_dev_fr_tgt_st_lvl*data['weight']
            node_deviation_costs.append(weighted_deviation)

    # convert the contents of the output file into a cost
    cost = sum(node_flood_costs) + sum(node_deviation_costs)
    os.remove(inp_tmp_process_inp)
    os.remove(inp_tmp_process_rpt)
    os.remove(tmp_hs_file)
    return cost,
