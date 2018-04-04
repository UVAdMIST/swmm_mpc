from plot_rpt import rpt_ele
import matplotlib.pyplot as plt

rpt_file = ("../simple_model/s_s_b_630.rpt")
rpt_file2 = ("../simple_model/s_s_b.rpt")
rpt_file3 = ("../simple_model/s_s_b_500.rpt")
rpt_file4 = ("../simple_model/s_s_b_400.rpt")
rpt = rpt_ele(rpt_file, "Node J1", "Inflow")
rpt2 = rpt_ele(rpt_file2, "Node J1", "Inflow")
rpt3 = rpt_ele(rpt_file3, "Node J1", "Inflow")
rpt4 = rpt_ele(rpt_file4, "Node J1", "Inflow")

ax = rpt2.ele_df["Inflow"].plot(label="Reality model")
rpt.ele_df["Inflow"].plot(ax=ax, label="Process start 06:30")
rpt3.ele_df["Inflow"].plot(ax=ax, label="Process start 05:00")
rpt4.ele_df["Inflow"].plot(ax=ax, label="Process start 04:00")
ax.legend()
ax.set_ylabel("Flow (cfs)")
ax.set_xlabel("Date/Time")
ax.grid(axis='both', which='both')
ax.set_title("Inflow at Node J1 (Inlet Node)")

plt.savefig("../../Figures/reality_vs_process_models", dpi=300)
