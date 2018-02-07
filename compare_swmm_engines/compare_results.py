# coding: utf-8
import matplotlib.pyplot as plt
import pandas as pd

def get_relevant_cols(df):
    df["elapsed_hours"] = df["elapsed_hours"].round(4)
    df.set_index("elapsed_hours", inplace=True)
    return df[["J2", "C8"]]
df32 = pd.read_csv('results_j2_c8_32_bit.csv')
df64 = pd.read_csv('results_j2_c8_64_bit.csv')
dfgui = pd.read_csv('results_j2_c8_gui.csv')

dfgui.columns = [c.strip() for c in dfgui.columns]
dfgui_mins = dfgui["Hours"].str.split(":", expand=True)[1]
dfgui_hr = dfgui["Hours"].str.split(":", expand=True)[0]
dfgui["elapsed_hours"] = dfgui_hr.astype(int) + dfgui_mins.astype(int)/60.
dfgui_rel = get_relevant_cols(dfgui)
df32_rel = get_relevant_cols(df32)
df64_rel = get_relevant_cols(df64)
df_comb = df64_rel.join(df32_rel, rsuffix="_32")
df_comb = df_comb.join(dfgui_rel, rsuffix="_gui")
