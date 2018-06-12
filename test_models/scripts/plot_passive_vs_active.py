from swmm_mpc.plot_control_vs_no_control import plot

input_file = "../models/simple_2_ctl.inp"
policy_file = "~/Documents/research/control_results_2018.06.11.15.55.csv"
plot(input_file, policy_file, 900, "NODE J3", "Flooding", "../figures/", figsize=(5,4))
plot(input_file, policy_file, 900, "NODE J3", "Depth", "../figures/", figsize=(5,4))
plot(input_file, policy_file, 900, "Node ST1", "Depth", "../figures/", figsize=(5,4))
plot(input_file, policy_file, 900, "Node ST2", "Depth", "../figures/", figsize=(5,4))
