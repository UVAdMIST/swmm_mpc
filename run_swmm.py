import pyswmm
from pyswmm import Simulation, Nodes, Links
import matplotlib.pyplot as plt
import pandas as pd

pyswmm.lib.use("swmm5_conda.dll")


def condense_df_by_datetime(df):
    return df.groupby("datetime").mean()


def make_elapsed_hours_col(df):
    counter = pd.Series(range(len(df)))
    counter.index = df.index
    df["elapsed_hours"] = counter/360   # 360 10 second time steps per hour 
    df.reset_index(inplace=True)
    dfi = df.set_index("elapsed_hours", drop=True)
    return dfi


def make_df_from_dicts(data_dictionary):
    df = pd.DataFrame(data_dictionary)
    date_df = condense_df_by_datetime(df)
    df_hr = make_elapsed_hours_col(date_df)
    return df_hr


def get_values(typ, obj, sim_obj, attr):
    id_name = "{}id".format(typ)
    l = []
    for o in obj:
        data_dict = {o.__getattribute__(id_name): o.__getattribute__(attr),
                     "datetime": sim_obj.current_time
                     }
        l.append(data_dict)
    return l


link_flow = []
nod_depth = []
target = []
with Simulation("example_smart.inp") as sim:
    for step in sim:
        node_obj = Nodes(sim)
        link_obj = Links(sim)
        ori = link_obj["C8"]
        nod_depth.extend(get_values("node", node_obj, sim, "depth"))
        link_flow.extend(get_values("link", link_obj, sim, "flow"))
        target.append(ori.target_setting)

    sim.report()

node_df = make_df_from_dicts(nod_depth)
con_df = make_df_from_dicts(link_flow)
tar_df = make_elapsed_hours_col(pd.DataFrame(target))
new_df = pd.concat([node_df['J2'], con_df[['C8', 'datetime']]], axis=1)
new_df.plot(grid=True)
new_df.to_csv("results_j2_c8_32_bit.csv")
plt.show()
