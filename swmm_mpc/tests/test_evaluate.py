import unittest
from swmm_mpc import evaluate
from swmm_mpc.rpt_ele import rpt_ele


class test_evaluate(unittest.TestCase):
    rpt_file = "example.rpt"
    rpt = rpt_ele(rpt_file)
    ctl_str_ids = ["ORIFICE r1", "PUMP p1"]

    def test_get_flood_cost_no_dict(self):
        node_fld_wgt_dict = None
        cost = evaluate.get_flood_cost(self.rpt, node_fld_wgt_dict)
        self.assertEqual(cost, 0.320)

    def test_get_flood_cost_dict(self):
        node_fld_wgt_dict = {"J3": 1, "St1": 1, "St2": 1}
        cost = evaluate.get_flood_cost(self.rpt, node_fld_wgt_dict)
        self.assertEqual(cost, 0.640)

    def test_gene_to_policy_dict(self):
        gene = [1, 0, 1, 1, 1, 0, 0, 1]
        n_ctl_steps = 2
        policy = evaluate.gene_to_policy_dict(gene, self.ctl_str_ids,
                                              n_ctl_steps)
        self.assertEqual(policy, {'ORIFICE r1': [0.714, 0.857],
                                  'PUMP p1': ['OFF', 'ON']})

    def test_bits_to_perc(self):
        bits = [1, 1, 0, 1]
        perc = evaluate.bits_to_perc(bits)
        self.assertEqual(perc, 0.867)

    def test_bits_to_decimal(self):
        bits = [1, 0, 1, 1]
        dec = evaluate.bits_to_decimal(bits)
        self.assertEqual(dec, 11)

    def test_bits_max_val(self):
        bit_len = 8
        max_val = evaluate.bits_max_val(bit_len)
        self.assertEqual(max_val, 255)

    def test_list_to_policy(self):
        gene = [0.4, 0.2, 0.1, 0.6, 0.2, 0]
        n_ctl_steps = 3
        policy = evaluate.list_to_policy(gene, self.ctl_str_ids, n_ctl_steps)
        self.assertEqual(policy, {'ORIFICE r1': [0.4, 0.2, 0.1],
                                  'PUMP p1': ['ON', 'OFF', 'OFF']})

    def test_split_gene_by_ctl_ts(self):
        ctl_str_ids = ["ORIFICE r1", "ORIFICE p1"]
        gene = [1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1]
        n_steps = 2
        split = evaluate.split_gene_by_ctl_ts(gene, ctl_str_ids, n_steps)
        expected = [[[1, 0, 1], [0, 0, 1]], [[1, 0, 0], [1, 1, 1]]]
        self.assertEqual(expected, split)


    def test_split_list(self):
        l = [1, 2, 3, 4, 5, 6]
        n = 2
        split = evaluate.split_list(l, n)
        expected = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(split, expected)

        n = 3
        split = evaluate.split_list(l, n)
        expected = [[1, 2], [3, 4], [5, 6]]
        self.assertEqual(split, expected)



if __name__ == '__main__':
        unittest.main()
