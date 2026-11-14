import tempfile
import unittest
from pathlib import Path
from xml.dom import minidom

from PIL import Image

from report.docxgen import MediaRegistry, RenderState, render

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

    def test_bold_only_paragraph_keeps_with_next(self):
        xml = render("**2. Ý nghĩa**\n\nĐoạn sau.", {}, self.media)
        first = xml.split("</w:p>")[0]
        self.assertIn("<w:keepNext/>", first)

    def test_short_column_not_too_narrow(self):
        xml = render("| STT | Mục tiêu dài dài dài dài dài dài dài | Cách đo dài dài dài dài dài dài dài dài dài dài dài dài |\n|---|---|---|\n| 1 | a | b |", {}, self.media)
        first_width = int(xml.split('<w:gridCol w:w="')[1].split('"')[0])
        self.assertGreaterEqual(first_width, 900)

    def test_caption_numbers_follow_chapter(self):
        state = RenderState()
        table = "Bảng: T\n| A |\n|---|\n| 1 |"
        render("# MỘT\n\n" + table + "\n\n" + table, {}, self.media, state=state)
        xml = render("# HAI\n\n" + table + "\n\n" + table, {}, self.media, state=state)
        captions = [p for p in xml.split("</w:p>") if 'w:val="Caption"' in p]
        self.assertIn(">Bảng 2.<", captions[0])
        self.assertIn("SEQ Bảng \\* ARABIC \\r 1", captions[0])
        self.assertIn("<w:t>1</w:t>", captions[0])
        self.assertNotIn("\\r 1", captions[1])
        self.assertIn("<w:t>2</w:t>", captions[1])

    def test_reference_entry_hanging_indent(self):
        xml = render("[3]. Postel J. (1980), *User Datagram Protocol*, RFC 768.", {}, self.media)
        self.assertIn('<w:ind w:left="567" w:hanging="567"/>', xml)
        self.assertIn(">[3]. <", xml)
        self.assertIn("<w:i/>", xml)

    def test_appendix_captions_use_pl(self):
        state = RenderState()
        table = "Bảng: T\n| A |\n|---|\n| 1 |"
        render("# MỘT\n\n" + table, {}, self.media, state=state)
        xml = render("#! PHỤ LỤC\n\n" + table, {}, self.media, state=state)
        self.assertIn(">Bảng PL.<", xml)

    def test_bullets(self):
        xml = render("- một\n- hai", {}, self.media)
        self.assertEqual(xml.count('<w:pStyle w:val="ListParagraph"/>'), 2)
        self.assertIn("<w:numPr>", xml)


if __name__ == "__main__":
    unittest.main()
