from swmm_mpc.plot_passive_vs_active import plot

input_file = "../models/simple_2_ctl.inp"
policy_file = "contro_res_edited"
  
plot(input_file, policy_file, 900, "NODE J3", "Flooding", "../figures/", figsize=(5,4), save_sfx='_abs_rain')
plot(input_file, policy_file, 900, "NODE J3", "Depth", "../figures/", figsize=(5,4), save_sfx='_abs_rain')
plot(input_file, policy_file, 900, "Node ST1", "Depth", "../figures/", figsize=(5,4), save_sfx='_abs_rain')
plot(input_file, policy_file, 900, "Node ST2", "Depth", "../figures/", figsize=(5,4), save_sfx='_abs_rain')
