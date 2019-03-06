import unittest
from swmm_mpc import update_process_model_input_file as up


class test_evaluate(unittest.TestCase):

    
    def test_get_control_rule_string_pump(self):
        policy = {'ORIFICE r1': [0.714, 0.857], 'PUMP p1': ['OFF', 'ON']}
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
        

if __name__ == '__main__':
        unittest.main()
