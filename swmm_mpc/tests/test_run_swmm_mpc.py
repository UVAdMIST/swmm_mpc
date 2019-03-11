import unittest
from swmm_mpc import swmm_mpc as sm


class test_swmm_mpc(unittest.TestCase):

    
    def test_validate_control_str_ids(self):
        control_str_ids_valid = ['ORIFICE ja', 'WEIR blah', 'PUMP p']
        sm.valid_structure_types(control_str_ids_invalid)
        control_str_ids_invalid = ['ORFICE ja', 'WEIR blah', 'PUMP p']
        with self.assertRaises(ValueError):
            sm.validate_control_str_ids(control_str_ids_invalid)

    
    def test_save_results_file(self):
        pass



if __name__ == '__main__':
        unittest.main()
