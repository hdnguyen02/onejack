import hashlib
import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from report.build import build

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = Path(
    "/home/devnguyenho/.claude/skills/synced/"
    "6eced0eb-06d5-47f3-a786-21d89e367b0b_66d3d5dd-78fe-4599-973b-5b4a18e76758/"
    "docx/scripts/office/validate.py"
)


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        deliverable = ROOT / "report/BaoCao_KLTN_onejack.docx"
        cls.before = hashlib.sha256(deliverable.read_bytes()).hexdigest() if deliverable.exists() else None
        cls.tmp = tempfile.TemporaryDirectory()
        cls.docx = build(Path(cls.tmp.name))
        cls.after = hashlib.sha256(deliverable.read_bytes()).hexdigest() if deliverable.exists() else None
        with zipfile.ZipFile(cls.docx) as z:
            cls.document = z.read("word/document.xml").decode("utf-8")
            cls.styles = z.read("word/styles.xml").decode("utf-8")
            cls.settings = z.read("word/settings.xml").decode("utf-8")

    def test_build_produces_valid_docx(self):
        self.assertTrue(self.docx.exists())
        result = subprocess.run(
            ["python3", str(VALIDATE), str(self.docx), "--original",
             str(ROOT / "report/template/MauTrinhBayDoAn.docx")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_does_not_touch_deliverable(self):
        self.assertEqual(self.before, self.after)

    def test_drawing_ids_unique(self):
        ids = re.findall(r'<wp:docPr id="(\d+)"', self.document)
        self.assertEqual(len(ids), len(set(ids)), ids)

    def test_sections_and_page_numbers(self):
        # bìa (không header/footer), trang đầu, nội dung (số trang từ 1), phụ lục
        self.assertEqual(self.document.count("<w:sectPr"), 4)
        self.assertIn('<w:pgNumType w:start="1"/>', self.document)
        first_section = self.document[: self.document.index("</w:sectPr>")]
        self.assertIn('r:id="rIdFooterEmpty"', first_section)

    def test_placeholders_and_template_text(self):
        self.assertIn("[MSSV]", self.document)
        self.assertNotIn("Mẫu Khóa Luận Tốt Nghiệp", self.document)

    def test_line_spacing_and_update_fields(self):
        self.assertNotIn('w:line="312"', self.styles.split('w:styleId="Normal"')[1].split("</w:style>")[0])
        self.assertIn('w:line="360"', self.styles.split('w:styleId="Normal"')[1].split("</w:style>")[0])
        self.assertIn("<w:updateFields", self.settings)


if __name__ == "__main__":
    unittest.main()
