import unittest
from pathlib import Path

from report.facts import load_facts, vn_number

ROOT = Path(__file__).resolve().parents[2]


def facts():
    return load_facts(ROOT / "results/eve", ROOT / "scripts/demo.sh")


class FactsTest(unittest.TestCase):
    def test_parameters_from_scripts(self):
        f = facts()
        self.assertEqual(f["duration"], "60")
        self.assertEqual(f["load_at"], "15")
        self.assertEqual(f["client_rate"], "20")
        self.assertEqual(f["load_rate"], "1.500")
        self.assertEqual(f["load_size"], "1.000")
        self.assertEqual(f["load_flows"], "32")
        self.assertEqual(f["load_mbit"], "12")
        self.assertEqual(f["link_rate"], "10")
        self.assertEqual(f["link_delay"], "10")
        self.assertEqual(f["two_links_mbit"], "20")
        self.assertEqual(f["queue_kb"], "500")
        self.assertEqual(f["queue_delay_ms"], "400")
        self.assertEqual(f["prop_long_ms"], "40")
        self.assertEqual(f["prop_short_ms"], "20")
        self.assertEqual(f["alpine_version"], "3.20")

    def test_measurements_match_dataset(self):
        # Cùng cách tính với scripts/plot.sh results/eve.
        f = facts()
        self.assertEqual(f["idle_base"], "43,87")
        self.assertEqual(f["idle_short"], "22,42")
        self.assertEqual(f["idle_balance"], "32,58")
        self.assertEqual(f["rtt_base"], "455,85")
        self.assertEqual(f["rtt_short"], "421,55")
        self.assertEqual(f["rtt_balance"], "32,85")
        self.assertEqual(f["server_base"], "9,58")
        self.assertEqual(f["server_balance"], "12,00")
        self.assertEqual(f["long_balance"], "6,66")
        self.assertEqual(f["short_balance"], "5,89")

    def test_reductions(self):
        f = facts()
        self.assertEqual(f["idle_drop_short"], "48,9")
        self.assertEqual(f["rtt_drop_balance"], "92,8")
        self.assertEqual(f["dropped_pct_base"], "20,2")
        self.assertEqual(f["dropped_pct_balance"], "0,0")

    def test_english_variants(self):
        f = facts()
        self.assertEqual(f["rtt_base_en"], "455.85")
        self.assertEqual(f["load_rate_en"], "1,500")

    def test_vn_number(self):
        self.assertEqual(vn_number(55965, 0), "55.965")
        self.assertEqual(vn_number(3.14159, 2), "3,14")


if __name__ == "__main__":
    unittest.main()
