from swmm_mpc.swmm_mpc import run_swmm_mpc

inp_file = "simple_2_ctl.inp"
control_horizon = 3. #hr
control_time_step = 900. #sec
control_str_ids = ["ORIFICE R1", "ORIFICE R2"]
results_dir = "~/Documents/research/results"
ngen = 7
nindividuals = 50

# target_depth_dict={'St1':{'target':1, 'weight':0.1}, 'St2':{'target':1.5, 'weight':0.1}}



def main():
    run_swmm_mpc(inp_file,
                 control_horizon,
                 control_time_step,
                 control_str_ids,
                 results_dir,
                 # target_depth_dict=target_depth_dict,
                 ngen=ngen,
                 nindividuals=nindividuals
                 )

if __name__ == "__main__":
    main()
