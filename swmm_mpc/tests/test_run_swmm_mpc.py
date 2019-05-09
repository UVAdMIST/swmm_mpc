import unittest
from swmm_mpc import swmm_mpc as sm
import datetime
import random


class test_swmm_mpc(unittest.TestCase):

    def test_validate_control_str_ids(self):
        control_str_ids_valid = ['ORIFICE ja', 'WEIR blah', 'PUMP p']
        sm.validate_ctl_str_ids(control_str_ids_valid)
        control_str_ids_invalid = ['ORFICE ja', 'WEIR blah', 'PUMP p']
        with self.assertRaises(ValueError):
            sm.validate_ctl_str_ids(control_str_ids_invalid)

    
    def test_save_results_file(self):
        pass


    def test_update_policy_ts_list(self):
        fmtd_policy = {'ORIFICE R1': [0.1, 0.2, 0.1],
                       'WEIR W1': [0.3, 0.4, 0.3]
                        }
        dt = datetime.datetime.strptime("10/08/2018 12:15", "%m/%d/%Y %H:%M")
        ctl_time_step = 900
        best_policy_ts = []
        cost = 1
        updated_ts = sm.update_policy_ts_list(fmtd_policy, dt, ctl_time_step,
                                              best_policy_ts, cost)
        self.assertEqual(len(updated_ts), 2)
        expected_ts = [{'datetime': dt, 'setting_ORIFICE R1': 0.1},
                       {'datetime': dt, 'setting_WEIR W1': 0.3}]
        self.assertItemsEqual(updated_ts, expected_ts)

        cost = 0
        best_policy_ts = []
        ts_zero = sm.update_policy_ts_list(fmtd_policy, dt, ctl_time_step,
                                              best_policy_ts, cost)
        self.assertEqual(len(ts_zero), 6)

        dt1 = datetime.datetime.strptime("10/08/2018 12:30", "%m/%d/%Y %H:%M")
        dt2 = datetime.datetime.strptime("10/08/2018 12:45", "%m/%d/%Y %H:%M")
        expected_ts = [{'datetime': dt, 'setting_ORIFICE R1': 0.1},
                       {'datetime': dt1, 'setting_ORIFICE R1': 0.2},
                       {'datetime': dt2, 'setting_ORIFICE R1': 0.1},
                       {'datetime': dt, 'setting_WEIR W1': 0.3},
                       {'datetime': dt1, 'setting_WEIR W1': 0.4},
                       {'datetime': dt2, 'setting_WEIR W1': 0.3}]

        self.assertItemsEqual(ts_zero, expected_ts)


    def test_get_initial_guess(self):
        best_pol = [0.24, 0.3, 0.22, 0.1, 0.04, 0.6]
        ctl_str_ids = ['ORIFICE r1', 'WEIR w1']
        new_guess = sm.get_initial_guess(best_pol, ctl_str_ids)
        print new_guess
        self.assertEqual(len(best_pol), len(new_guess))
        self.assertEqual(best_pol[1], new_guess[0])
        self.assertEqual(best_pol[4], new_guess[3])


if __name__ == '__main__':
        unittest.main()
