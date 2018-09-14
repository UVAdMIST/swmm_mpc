import os
import subprocess
import matplotlib.pyplot as plt
from matplotlib import rc
from swmm_mpc.rpt_ele import rpt_ele
from swmm_mpc.update_process_model_input_file import update_controls_with_policy
import pandas as pd

def get_df(rpts, ele, variable, column_names=None):
    """
    get pandas dataframe of different versions of results for one element for
    one variable
    rpts: list of rpt_ele objects - rpt_objects to be combined
    ele: string - swmm model element to extract from rpt_ele objects 
         (e.g., "Node J3")
    variable: string - variable to extract data (e.g., "Depth")
    column_names: list of strings - column labels for different versions
                  (e.g., ["Passive", "Rules", "MPC"])
    """
    ser_list = []
    for rpt in rpts:
        ser_list.append(rpt.get_ele_df(ele)[variable])
    comb = pd.concat(ser_list, 1)
    if column_names:
        comb.columns=column_names
    return comb

def plot_versions_single(df, ylabel, title=None, colors=None):
    """
    make a plot of multiple versions of rpt_elements at one node for one 
    variable
    df: pandas dataframe - dataframe with values of one variable at one node 
        for different versions. The different versions are the columns
    ylabel: string - label for y-axis
    title: string - title for plot
    colors: list of strings - matplotlib colors corresponding to the different
            versions of the results
    """
    font_size = 12
    ax = df.plot(fontsize=font_size, lw=3)
    lines = ax.lines

    if not colors:
        colors = ["0.55", "royalblue", "yellowgreen"]

    for i in range(len(lines)):
        lines[i].set_color(colors[i])

    ax.legend()
    ax.set_xlabel("Time elapsed (hr)", fontsize=font_size)
    ax.set_ylabel(ylabel, fontsize=font_size)
    if title:
        ax.set_title(title)
    return ax

def plot_versions_together(node_id_vars, rpt_files, rpt_labels, units, fig_dir,
                           sfx):
    """
    plot variable results at different nodes in one figure
    node_id_vars: list of tuples - tuple has node_id as first element and 
                  variable to plot as second element 
                  (e.g., [("Node St1", "Depth"), ("Node J3", "Flooding")])
    rpts_files: list of strings - file paths of different versions that will be 
                in each sublot 
    rpt_labels: list of strings - labels for the different rpt versions
                (e.g., ["Passive", "Rules", "MPC"])
    units: string - units of variable to be plotted
    fig_dir: string - directory where file should be saved
    sfx: string - suffix to be put on the end of the file name
    """
    rpts = [rpt_ele(r) for r in rpt_files]

    nplots = len(rpts)
    nrows = round(nplots**0.5)
    fig, axs = plt.subplots(nrows=nrows, ncols=nrows, sharex=True, 
                            figsize=(5,5))

    if nplots > 0:
        axs_list = axs.ravel()
    else:
        axs_list = [axs]

    counter = 0
    for node_id, variable in node_id_vars:
        var_df = get_df(rpts, node_id, variable, rpt_labels)
        plot_title = "{} at {}".format(node_id, variable)
        axs_list[counter] = plot_versions_single(var_df, title=plot_title)
        counter += 1

    plt.tight_layout()
    fig = plt.gcf()
    fig.savefig("../../figures/{}_{}".format(title.replace(" ", "_"),
                                            sfx),  
            bbox_inches="tight")
    plt.show()

