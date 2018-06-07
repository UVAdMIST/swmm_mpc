from swmm_mpc.swmm_mpc import swmm_mpc
inp_file = "simple_smart_blank.inp"
control_horizon = 6. #hr
control_time_step = 900. #sec
control_str_ids = ["ORIFICE R1"]
results_dir = "~/Documents/research/sadler4"

swmm_mpc_obj = swmm_mpc(inp_file,
			control_horizon,
			control_time_step,
			control_str_ids,
			results_dir)

# def main():
    # swmm_mpc_obj.run_swmm_mpc()

# if __name__ == "__main__":
    # main()
