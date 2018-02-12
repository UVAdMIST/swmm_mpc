import pyswmm
from pyswmm import Simulation, Nodes, Links
import matplotlib.pyplot as plt
import pandas as pd

pyswmm.lib.use("swmm5_conda.dll")


class swmm_results(input_file):
    def __init__():

    link_flow = []
    nod_depth = []
    nod_flood = []
    target = []
    with Simulation("../example_smart.inp") as sim:
        node_obj = Nodes(sim)
        link_obj = Links(sim)
        ori = link_obj["C8"]
        for step in sim:
            nod_depth.extend(self.get_values("node", node_obj, sim, "depth"))
            nod_depth.extend(self.get_values("node", node_obj, sim, "flooding"))
            link_flow.extend(self.get_values("link", link_obj, sim, "flow"))

        sim.report()

    node_depth_df = make_df_from_dicts(nod_depth)
    node_flood_df = make_df_from_dicts(nod_depth)
    con_flow_df = make_df_from_dicts(link_flow)

    def condense_df_by_datetime(self, df):
        return df.groupby("datetime").mean()


    def make_elapsed_hours_col(self, df):
        counter = pd.Series(range(len(df)))
        counter.index = df.index
        df["elapsed_hours"] = counter/360   # 360 10 second time steps per hour 
        df.reset_index(inplace=True)
        dfi = df.set_index("elapsed_hours", drop=True)
        return dfi


    def make_df_from_dicts(self, data_dictionary):
        df = pd.DataFrame(data_dictionary)
        date_df = self.condense_df_by_datetime(df)
        df_hr = self.make_elapsed_hours_col(date_df)
        return df_hr


    def get_values(self, typ, obj, sim_obj, attr):
        id_name = "{}id".format(typ)
        l = []
        for o in obj:
            data_dict = {o.__getattribute__(id_name): o.__getattribute__(attr),
                         "datetime": sim_obj.current_time
                         }
            l.append(data_dict)
        return l


