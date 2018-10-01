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
    for i,rpt in enumerate(rpts):
        if variable == "Total Flooding":
            ser_list.append(pd.Series([rpt.total_flooding]))
        else:
            ser_list.append(rpt.get_ele_df(ele)[variable])
    comb = pd.concat(ser_list, 1)
    if column_names:
        comb.columns = column_names
    return comb


def plot_versions_single(df, variable, ylabel, fontsize, title=None, 
                         colors=None, ax=None, lgd=False):
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
    plt.rc('font', weight='bold', size=fontsize)
    if not colors:
        colors = ["0.55", "royalblue", "yellowgreen"]

    if variable == "Total Flooding":
        ax=df.plot.bar(ax=ax, color=colors)
        plt.tick_params(
                        axis='x',      # changes apply to the x-axis
                        which='both',  # both major and minor ticks are affected
                        bottom=False,  # ticks along the bottom edge are off
                        top=False,     # ticks along the top edge are off   
                        labelbottom=False  # label is off
                        )
    else:
        for col in df.columns:
            ax.plot(df.index, df[col], label=col, lw=4)
        lines = ax.lines

        for i in range(len(lines)):
            lines[i].set_color(colors[i])

        ax.set_xlabel('Time elapsed (hr)')
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
        ax.set_xlim((df.index.min(), df.index.max()))

    ax.set_ylabel(ylabel) 
    if lgd:
        ax.legend()
    if title:
        ax.set_title(title)
    ax.xaxis.set_tick_params()
    ax.yaxis.set_tick_params()
    return ax


def get_unit_label(units, variable):
    variable = variable.lower()
    if units == 'english':
        if variable == 'depth':
            return "ft"
        elif variable == 'flooding':
            return "cfs"
        elif variable == 'total flooding':
            return '10^6 cubic meters'
        else:
            return "unknown"
    elif units == 'metric':
        if variable == 'depth':
            return 'm'
        elif variable == 'flooding' :
            return 'cms'
        elif variable == 'total flooding':
            return '10^6 cubic meters'
        else:
            return 'unknown'
    else:
        return 'unknown'


def make_values_metric(df, variable):
    variable = variable.lower()
    if variable == "depth":
        factor = 0.3048  # meters/foot
    elif variable == 'flooding' or variable == 'total flooding':
        factor = 0.028316847000000252 # cubic meters/cubic foot
    return df*factor


def plot_versions_together(node_id_vars, rpt_files, rpt_labels, fig_dir, sfx, 
                           units="english", fontsize=12):
    """
    plot variable results at different nodes in one figure
    node_id_vars: list of tuples - tuple has node_id as first element and
                  variable to plot as second element
                  (e.g., [("Node St1", "Depth"), ("Node J3", "Flooding")])
    rpts_files: list of strings - file paths of different versions that will be
                in each sublot
    rpt_labels: list of strings - labels for the different rpt versions
                (e.g., ["Passive", "Rules", "MPC"])
    fig_dir: string - directory where file should be saved
    sfx: string - suffix to be put on the end of the file name
    units: string - "english" or "metric". If "metric" conversions from english
           units will be performed
    """
    rpts = [rpt_ele(r) for r in rpt_files]

    nplots = len(node_id_vars)
    nrows = int(round(nplots**0.5))
    fig, axs = plt.subplots(nrows=nrows, ncols=nrows, sharex=False,
                            figsize=(15, 10))

    if nplots > 1:
        axs_list = axs.ravel()
    else:
        axs_list = [axs]

    counter = 0
    for node_id, variable in node_id_vars:
        var_df = get_df(rpts, node_id, variable, rpt_labels)

        # correct for units
        if units == 'metric':
            var_df = make_values_metric(var_df, variable)
        elif units == 'english':
            pass
        else:
            raise ValueError('units variable needs to be "english" or "metric". you entered {}'.format(units))

        unit_label = get_unit_label(units, variable)

        if node_id != '':
            plot_title = "{} at {}".format(variable, node_id)
        else:
            plot_title = "{}".format(variable)

        if counter + 1 == len(node_id_vars):
            lgd = True
        else:
            lgd = False

        plot_versions_single(var_df, variable, unit_label, fontsize, 
                             title=plot_title, ax=axs_list[counter], lgd=lgd)
        counter += 1

    plt.tight_layout()
    fig.autofmt_xdate()
    fig.savefig("{}/{}_{}".format(fig_dir, "combined", sfx), dpi=300)
    plt.show()
