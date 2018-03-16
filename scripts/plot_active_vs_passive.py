import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import pandas as pd
from run_swmm import swmm_results

# activate latex text rendering
rc('text', usetex=True)

res_dumb = swmm_results("../simple_model/simple_dumb.inp")
res_smrt = swmm_results("../simple_model/simple_smart.inp")
res_mpc = pd.read_csv("../data/depth_results_2018.03.15.15.16.csv")
res_mpc.index = res_mpc.index/4.
fig_suffix = "5gen_80indv_origcost"

# plot node depths at J3
col_names = [ r"DS Node Depth (ft)-\textit{Passive}", r"DS Node Flooding (cfs)-\textit{Passive}", 
        r"DS Node Depth (ft)-\textit{Rules}"]
node_id = "J3"
comb = pd.concat([res_dumb.node_depth_df[node_id], res_dumb.node_flood_df[node_id], 
    res_smrt.node_depth_df[node_id]], 1)
comb.columns = col_names 
font_size = 12
ax = comb.plot(fontsize=font_size, lw=3)
ax.plot(res_mpc.index, res_mpc[node_id], label = r"DS Node Depth (ft)-\textit{MPC}", lw=3)
lines = ax.lines
passive_color = "0.55"
rule_color = "royalblue"
mpc_color = "yellowgreen"
lines[0].set_color(passive_color)
lines[1].set_color(passive_color)
lines[1].set_linestyle("--")
lines[2].set_color(rule_color)
lines[3].set_color(mpc_color)
lgd = ax.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol=1, fontsize=font_size)
ax.set_xlabel("Time elapsed (hr)", fontsize=font_size)
fig = plt.gcf()
fig.savefig("../../figures/dumb_vs_smart_vs_mpc_node_depth_{}".format(fig_suffix),  
        bbox_inches="tight")

# plot storage depths at St1
storage_node = "St1"
col_names = [r"Storage Depth -\textit{Passive}", r"Storage Depth -\textit{Rules}"]
comb = pd.concat([res_dumb.node_depth_df[storage_node], res_smrt.node_depth_df[storage_node]], 1)
comb.columns = col_names
ax = comb.plot(lw=3)
ax.plot(res_mpc.index, res_mpc[storage_node], label = r"Storage Depth -\textit{MPC}", lw=3)
ax.set_xlabel("Time elapsed (hr)", fontsize=font_size)
ax.set_ylabel("ft", fontsize=font_size)
lines = ax.lines
lines[0].set_color(passive_color)
lines[1].set_color(rule_color)
lines[2].set_color(mpc_color)
lgd = ax.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol=1, fontsize=font_size)
fig = plt.gcf()
fig.savefig("../../figures/dumb_vs_smart_vs_mpc_storage_depth_{}".format(fig_suffix),
        bbox_inches="tight")

plt.show()
