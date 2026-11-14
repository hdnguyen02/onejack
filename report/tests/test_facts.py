import unittest
from pathlib import Path

from report.facts import load_facts

ROOT = Path(__file__).resolve().parents[2]


class FactsTest(unittest.TestCase):
    def test_facts_match_dataset(self):
        f = load_facts(ROOT / "results/eve-v2-report", ROOT / "scripts/demo.sh")
        self.assertEqual(f["rtt_off"], "407,97")
        self.assertEqual(f["rtt_on"], "6,29")
        self.assertEqual(f["rtt_inband"], "6,91")
        self.assertEqual(f["link_off"], "10,02")
        self.assertEqual(f["link_on"], "0,17")
        self.assertEqual(f["link_inband"], "0,19")
        self.assertEqual(f["detect_off"], "0,566")
        self.assertEqual(f["detect_on"], "0,495")
        self.assertEqual(f["detect_inband"], "0,577")
        self.assertEqual(f["block_on_ms"], "7")
        self.assertEqual(f["block_inband_ms"], "4")
        self.assertEqual(f["qos_normal_eve"], "401,94")
        self.assertEqual(f["qos_prio_eve"], "3,07")
        self.assertEqual(f["qos_normal_netns"], "399,85")
        self.assertEqual(f["qos_prio_netns"], "0,07")
        self.assertEqual(f["qos_prio_pkts"], "100")
        self.assertEqual(f["qos_normal_dropped"], "55.965")
        self.assertEqual(f["duration"], "60")
        self.assertEqual(f["attack_at"], "15")
        self.assertEqual(f["client_rate"], "20")
        self.assertEqual(f["attack_rate"], "5.000")
        self.assertEqual(f["attack_size"], "1.000")
        self.assertEqual(f["threshold"], "200")
        self.assertEqual(f["bottleneck"], "10")
        self.assertEqual(f["queue_kb"], "500")


if __name__ == "__main__":
    unittest.main()
