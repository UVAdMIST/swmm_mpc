import unittest
from swmm_mpc import evaluate
from swmm_mpc.rpt_ele import rpt_ele


class test_evaluate(unittest.TestCase):
    rpt_file = "example.rpt"
    rpt = rpt_ele(rpt_file)

    def test_get_flood_cost_no_dict(self):
        node_fld_wgt_dict = None
        cost = evaluate.get_flood_cost(self.rpt, node_fld_wgt_dict)
        self.assertEqual(cost, 0.620)

    def test_get_flood_cost_dict(self):
        node_fld_wgt_dict = {"J3":1, "St1":1, "St2":1}
        cost = evaluate.get_flood_cost(self.rpt, node_fld_wgt_dict)
        self.assertEqual(cost, 0.620)

if __name__ == '__main__':
        unittest.main()
