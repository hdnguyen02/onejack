import unittest

from report.check import font_violations, heading3_violations, raw_measurements


class CheckTest(unittest.TestCase):
    def test_raw_measurements_rejected(self):
        self.assertTrue(raw_measurements("RTT 455,85 ms khi có tải"))
        self.assertTrue(raw_measurements("link đầy {{bottleneck}} Mbit/s, đo được 10 Mbit/s"))
        self.assertEqual(raw_measurements("RTT {{rtt_off}} ms, mỗi 1 giây in một dòng"), [])
        self.assertEqual(raw_measurements("```\nsleep 0,5 s\n```"), [])

    def test_heading3_min_two(self):
        self.assertTrue(heading3_violations("## A\n### a1\n## B"))
        self.assertEqual(heading3_violations("## A\n### a1\n### a2\n## B"), [])
        self.assertEqual(heading3_violations("## A\nchữ\n## B"), [])

    def test_font_check(self):
        self.assertTrue(font_violations('<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>'))
        self.assertEqual(font_violations('<w:rFonts w:ascii="Times New Roman"/><w:rFonts w:cs="Arial"/>'), [])


if __name__ == "__main__":
    unittest.main()
