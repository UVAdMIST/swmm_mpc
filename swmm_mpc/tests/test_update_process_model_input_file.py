import unittest
import pandas as pd
from swmm_mpc import update_process_model_input_file as up


class test_update_process_model_input_file(unittest.TestCase):

    
    def test_get_control_rule_string_pump(self):
        policy = {'PUMP p1': ['OFF', 'ON'], 'ORIFICE r1': [0.714, 0.857]}
        control_time_step = 900
        ctl_rule_str = up.get_control_rule_string(control_time_step, policy)
        with file('example_rules_pumps.txt', 'r') as rules_file:
            expected_str = rules_file.readlines()
        self.assertEqual(expected_str, ctl_rule_str)

        
    def test_get_control_rule_string_just_orifice(self):
        policy = {'ORIFICE r1': [0.714, 0.857, 0.523, 0.451], 
                  'ORIFICE r2': [0.124, 0.512, 0.857, 0.543]}
        control_time_step = 900
        ctl_rule_str = up.get_control_rule_string(control_time_step, policy)
        with file('example_rules_orifices.txt', 'r') as rules_file:
            expected_str = rules_file.readlines()
        self.assertEqual(expected_str, ctl_rule_str)


    def test_get_ctl_time_step(self):
        policy_file = 'ctl_results.csv'
        pol_df = pd.read_csv(policy_file)
        time_step = up.get_control_time_step(pol_df)
        self.assertEqual(time_step, 900)


    def test_get_ctl_time_step_err(self):
        policy_file = 'ctl_results_err.csv'
        pol_df = pd.read_csv(policy_file)
        with self.assertRaises(Exception):
            time_step = up.get_control_time_step(pol_df)
        

if __name__ == '__main__':
        unittest.main()
