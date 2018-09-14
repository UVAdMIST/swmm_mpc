import matplotlib.pyplot as plt
from rpt_ele import rpt_ele
from update_process_model_input_file import update_controls_with_policy
import pandas as pd
import matplotlib.dates as mdates


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
        comb.columns = column_names
    return comb


def plot_versions_single(df, ylabel, title=None, colors=None, ax=None, 
                         lgd=False):
    """
    make a plot of multiple versions of rpt_elements at one node for one
    variable
    df: pandas dataframe - dataframe with values of one variable at one node
        for different versions. The different versions are the columns
    ylabel: string - label for y-axis
    title: string - title for plot
    colors: list of strings - matplotlib colors corresponding to the different
            versions of the results
    ax: matplotlib axes object - axes where the plot will be made
    lgd: boolean - whether to include legend or not
    """
    font_size = 12
    for col in df.columns:
        ax.plot(df.index, df[col], label=col)
    lines = ax.lines

    if not colors:
        colors = ["0.55", "royalblue", "yellowgreen"]

    for i in range(len(lines)):
        lines[i].set_color(colors[i])

    if lgd:
        ax.legend()
    ax.set_xlabel("Time elapsed (hr)", fontsize=font_size)
    ax.set_ylabel(ylabel, fontsize=font_size)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
    ax.set_xlim((df.index.min(), df.index.max()))
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
    units: list of string - units of variable to be plotted for each variable
           (e.g., [('ft'), ('cfs')]). Should have the same number of members as
           node_id_vars
    fig_dir: string - directory where file should be saved
    sfx: string - suffix to be put on the end of the file name
    """
    rpts = [rpt_ele(r) for r in rpt_files]

    nplots = len(node_id_vars)
    nrows = int(round(nplots**0.5))
    fig, axs = plt.subplots(nrows=nrows, ncols=nrows, sharex=True,
                            figsize=(10, 10))

    if nplots > 1:
        axs_list = axs.ravel()
    else:
        axs_list = [axs]

    counter = 0
    for node_id, variable in node_id_vars:
        var_df = get_df(rpts, node_id, variable, rpt_labels)
        plot_title = "{} at {}".format(variable, node_id)

        if counter + 1 == len(node_id_vars):
            lgd = True
        else:
            lgd = False

        plot_versions_single(var_df, units[counter], title=plot_title,
                             ax=axs_list[counter], lgd=lgd)
        counter += 1

    # plt.tight_layout()
    fig.autofmt_xdate()
    fig.savefig("{}/{}_{}".format(fig_dir, "combined", sfx),
                bbox_inches="tight")
    plt.show()
