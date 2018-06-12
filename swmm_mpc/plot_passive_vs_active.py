import sys
import subprocess
import matplotlib.pyplot as plt
from rpt_ele import rpt_ele
from update_process_model_input_file import update_controls_with_policy,\
    remove_control_section

def plot(inp_file, policy_file, control_time_step, ele, variable, save_dir, 
         save_sfx='', show=True, figsize=(3.5, 2.8), fontsize=10): 
    # run swmm active
    policy_id = policy_file.split("/")[-1].split("_")[-1]

    update_controls_with_policy(inp_file, control_time_step, policy_file)

    rpt_file_act = inp_file.replace(".inp", "_acive.rpt") 
    cmd = "swmm5 {} {}".format(inp_file, rpt_file_act)
    subprocess.call(cmd, shell=True, stderr=subprocess.STDOUT)
    rpt_obj_act = rpt_ele(rpt_file_act)

    # run swmm passive
    remove_control_section(inp_file)

    rpt_file_pass = inp_file.replace(".inp", "_acive.rpt") 
    cmd = "swmm5 {} {}".format(inp_file, rpt_file_pass)
    subprocess.call(cmd, shell=True, stderr=subprocess.STDOUT)
    rpt_obj_pass = rpt_ele(rpt_file_pass)

    # plot
    ax = rpt_obj_act.get_ele_df(ele)[variable].plot(label='MPC', 
                                                    figsize=figsize,
                                                    fontsize=fontsize
                                                    )
    rpt_obj_pass.get_ele_df(ele)[variable].plot(label='passive', ax=ax)

    # formatting
    if variable == 'Depth':
        ylabel = 'Depth (ft)'
    elif variable == 'Flooding':
        ylabel = 'Flooding (million gallons)'

    ax.set_title("{} at {}".format(variable, ele), fontsize=fontsize)
    ax.set_ylabel(ylabel)
    ax.legend()
    plt.tight_layout()
    plt.savefig("{}/{}_{}{}".format(save_dir, variable, ele.replace(" ", "-"), 
                                    save_sfx), 
                dpi=300)
    if show:
        plt.show()
