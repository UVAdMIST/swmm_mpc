import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
from run_swmm import swmm_results

# activate latex text rendering
rc('text', usetex=True)

res_dumb = swmm_results("../simple_model/simple_dumb.inp")
res_smrt = swmm_results("../simple_model/simple_smart.inp")
col_names = [r"DS Node Depth (ft)-\textit{Active}", r"DS Node Depth (ft)-\textit{Passive}", 
        r"DS Node Flooding (cfs)-\textit{Passive}"]
comb = pd.concat([res_smrt.node_depth_df["J3"], res_dumb.node_depth_df["J3"], res_dumb.node_flood_df["J3"]], 1)
comb.columns = col_names 
font_size = 12
ax = comb.plot(fontsize=font_size, lw=3)
lines = ax.lines
passive_color = "0.55"
lines[1].set_color(passive_color)
lines[2].set_color(passive_color)
lines[2].set_linestyle("--")
lgd = ax.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol=1, fontsize=font_size)
ax.set_xlabel("Time elapsed (hr)", fontsize=font_size)
fig = plt.gcf()
fig.savefig("../../figures/dumb_vs_smart",  bbox_inches="tight")

plt.show()
