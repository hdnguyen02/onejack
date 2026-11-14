import tempfile
import unittest
from pathlib import Path
from xml.dom import minidom

from PIL import Image

from report.docxgen import MediaRegistry, render

NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
)


def parse(xml: str):
    return minidom.parseString(f"<root {NS}>{xml}</root>")


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.media = MediaRegistry()

    def test_heading_levels(self):
        xml = render("# A\n\n#! B\n\n## C\n\n### D", {}, self.media)
        self.assertIn('<w:pStyle w:val="Heading1"/>', xml)
        self.assertIn('<w:numId w:val="0"/>', xml)
        self.assertIn('<w:pStyle w:val="Heading2"/>', xml)
        self.assertIn('<w:pStyle w:val="Heading3"/>', xml)
        self.assertEqual(xml.count('<w:pStyle w:val="Heading1"/>'), 2)

    def test_chapter_heading_has_colon_like_template(self):
        xml = render("# GIỚI THIỆU\n\n#! LỜI MỞ ĐẦU", {}, self.media)
        self.assertIn(">: GIỚI THIỆU<", xml)
        self.assertIn(">LỜI MỞ ĐẦU<", xml)

    def test_escapes_xml_special_chars(self):
        xml = render('a & b < c "d"', {}, self.media)
        self.assertIn("a &amp; b &lt; c", xml)
        parse(xml)

    def test_placeholders_kept_verbatim(self):
        xml = render("[Họ tên] và [MSSV]", {}, self.media)
        self.assertIn("[Họ tên] và [MSSV]", xml)

    def test_table_caption_above(self):
        xml = render("Bảng: Tên bảng\n| A | B |\n|---|---|\n| 1 | 2 |", {}, self.media)
        self.assertLess(xml.index('w:val="Caption"'), xml.index("<w:tbl>"))
        self.assertIn("SEQ Bảng", xml)
        parse(xml)

    def test_figure_caption_below(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "x.png"
            Image.new("RGB", (400, 200), "white").save(png)
            xml = render(f"![Sơ đồ mạng]({png})", {}, self.media)
        self.assertLess(xml.index("<w:drawing>"), xml.index('w:val="Caption"'))
        self.assertIn("SEQ Hình", xml)
        self.assertEqual(len(self.media.items()), 1)
        parse(xml)

    def test_fact_tokens(self):
        xml = render("RTT {{rtt_off}} ms", {"rtt_off": "407,97"}, self.media)
        self.assertIn("RTT 407,97 ms", xml)
        with self.assertRaises(KeyError):
            render("{{khong_co}}", {}, self.media)

    def test_code_block_preserves_spaces(self):
        xml = render("```\nwhile (true) {\n    poll(x);\n}\n```", {}, self.media)
        self.assertIn('<w:t xml:space="preserve">    poll(x);</w:t>', xml)
        parse(xml)

    def test_bold_and_ref(self):
        xml = render("**đậm** theo [[REF:3]]", {}, self.media)
        self.assertIn("<w:b/>", xml)
        self.assertIn("[3]", xml)

    def test_right_aligned_line(self):
        xml = render(">> Sinh viên thực hiện", {}, self.media)
        self.assertIn('<w:jc w:val="right"/>', xml)
        self.assertIn(">Sinh viên thực hiện<", xml)

    def test_bullets(self):
        xml = render("- một\n- hai", {}, self.media)
        self.assertEqual(xml.count('<w:pStyle w:val="ListParagraph"/>'), 2)
        self.assertIn("<w:numPr>", xml)


if __name__ == "__main__":
    unittest.main()
