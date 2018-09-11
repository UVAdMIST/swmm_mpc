import unittest
from swmm_mpc.rpt_ele import rpt_ele


class test_rpt_ele(unittest.TestCase):
    test_rpt_file = "example.rpt"
    rpt = rpt_ele(test_rpt_file)

    def test_total_flood(self):
        true_flood_vol = 0.320
        self.assertEqual(true_flood_vol, self.rpt.total_flooding)

    def test_get_start_line(self):
        start_text = 'Infiltration Method'
        start_line = self.rpt.get_start_line(start_text)
        self.assertEqual(start_line, 23)

        start_text = 'Node Surcharge Summary'
        start_line = self.rpt.get_start_line(start_text)
        self.assertEqual(start_line, 138)

    def test_get_end_line(self):
        start_text = 'Node Depth Summary'
        start_line = self.rpt.get_start_line(start_text)
        end_line = self.rpt.get_end_line(start_line)
        self.assertEqual(end_line, 118)



if __name__ == '__main__':
        unittest.main()
