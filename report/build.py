"""Ghép nội dung báo cáo vào file mẫu của Khoa, xuất report/out/BaoCao_KLTN_onejack.docx.

Chạy: python3 report/build.py
Giữ nguyên style, trang bìa (logo), header của MauTrinhBayDoAn.docx; chỉ thay phần body.
Body chia 3 section:
  1. bìa, các trang đầu, mục lục       — không đánh số trang
  2. LỜI MỞ ĐẦU tới TÀI LIỆU THAM KHẢO — trang 1, 2, 3... góc dưới bên phải
  3. PHỤ LỤC                           — không đánh số trang
"""
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from report import frontmatter  # noqa: E402
from report.docxgen import MediaRegistry, RenderState, render  # noqa: E402
from report.facts import load_facts  # noqa: E402

TEMPLATE = ROOT / "report/template/MauTrinhBayDoAn.docx"
CONTENT = ROOT / "report/content"
OUTPUT_NAME = "BaoCao_KLTN_onejack.docx"

FRONT_FILES = ["00a-abstract.md", "00b-thanks.md", "00c-abbrev.md"]
MAIN_FILES = [
    "01-mo-dau.md", "02-chuong1.md", "03-chuong2.md", "04-chuong3.md",
    "05-chuong4.md", "06-chuong5.md", "07-tltk.md",
]
APPENDIX_FILES = ["09-appendix.md"]

HEADER_RID = "rId9"        # header1.xml của mẫu: dòng thông tin khóa luận
FIRST_HEADER_RID = "rId25"  # header2.xml của mẫu: trống, dùng cho trang bìa
FOOTER_PAGE_RID = "rIdFooterPage"
FOOTER_INFO_RID = "rIdFooterInfo"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def section_properties(footer_rid: str, start_page: bool = False, title_page: bool = False) -> str:
    xml = f'<w:sectPr><w:headerReference w:type="default" r:id="{HEADER_RID}"/>'
    if title_page:
        xml += f'<w:headerReference w:type="first" r:id="{FIRST_HEADER_RID}"/>'
    xml += f'<w:footerReference w:type="default" r:id="{footer_rid}"/>'
    xml += '<w:pgSz w:w="11907" w:h="16840" w:code="9"/>'
    xml += '<w:pgMar w:top="1701" w:right="1134" w:bottom="1701" w:left="1985" w:header="709" w:footer="709" w:gutter="0"/>'
    if start_page:
        xml += '<w:pgNumType w:start="1"/>'
    xml += '<w:cols w:space="708"/>'
    if title_page:
        xml += "<w:titlePg/>"
    xml += '<w:docGrid w:linePitch="360"/></w:sectPr>'
    return xml


def section_break(footer_rid: str, start_page: bool = False, title_page: bool = False) -> str:
    """Đoạn rỗng mang sectPr: kết thúc một section, section sau bắt đầu ở trang mới."""
    return f"<w:p><w:pPr>{section_properties(footer_rid, start_page, title_page)}</w:pPr></w:p>"


def footer_xml(with_page_number: bool) -> str:
    """Footer: [Họ tên] – [MSSV] bên trái, lớp ở giữa, số trang bên phải (nếu có)."""
    rpr = '<w:rPr><w:i/><w:sz w:val="24"/></w:rPr>'
    ppr_base = '<w:pStyle w:val="Footer"/><w:spacing w:before="0" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/>'

    def cell(width: int, align: str, runs: str) -> str:
        return (
            f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
            f'<w:p><w:pPr>{ppr_base}<w:jc w:val="{align}"/></w:pPr>{runs}</w:p></w:tc>'
        )

    name = f'<w:r>{rpr}<w:t xml:space="preserve">SVTH: [Họ tên] – [MSSV]</w:t></w:r>'
    klass = f'<w:r>{rpr}<w:t xml:space="preserve">Lớp [Lớp]</w:t></w:r>'
    page = ""
    if with_page_number:
        page = (
            f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{rpr}<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r>{rpr}<w:t>1</w:t></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>'
        )
    table = (
        '<w:tbl><w:tblPr><w:tblW w:w="8788" w:type="dxa"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders>'
        '<w:tblLayout w:type="fixed"/></w:tblPr>'
        '<w:tblGrid><w:gridCol w:w="4394"/><w:gridCol w:w="2697"/><w:gridCol w:w="1697"/></w:tblGrid>'
        "<w:tr>" + cell(4394, "left", name) + cell(2697, "center", klass) + cell(1697, "right", page) + "</w:tr></w:tbl>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{table}'
        f'<w:p><w:pPr>{ppr_base}</w:pPr></w:p></w:ftr>'
    )


def fix_header(header: str) -> str:
    """Header của mẫu: 'Khóa tốt nghiệp chuyên ngành <tô vàng>' -> 'Khóa luận tốt nghiệp chuyên ngành [Ngành]'."""
    header = header.replace("<w:highlight w:val=\"yellow\"/>", "")
    header = header.replace(">Khóa </w:t>", ">Khóa luận</w:t>")
    header = header.replace(">Kỹ Thuật</w:t>", ">[Ngành]</w:t>")
    header = header.replace("> Phần Mềm</w:t>", "></w:t>")
    header = header.replace(">, CNTT, Khoa Học Máy Tính</w:t>", "></w:t>")
    return header


def cover_vi(document: str) -> str:
    """Lấy khối bìa của mẫu (tới hết </w:sdt>), thay chữ mẫu bằng tên đề tài và thông tin sinh viên."""
    body_start = document.index("<w:body>") + len("<w:body>")
    sample = document.index("Mẫu Khóa Luận Tốt Nghiệp")
    # Bìa là một khối sdt bên ngoài, bên trong có sdt nhỏ chứa chữ mẫu; lấy tới hết khối ngoài.
    page_break = document.index('w:type="page"', sample)
    cover_end = document.index("</w:sdt>", page_break) + len("</w:sdt>")
    cover = document[body_start:cover_end]

    # Khối sdt nhỏ chứa chữ mẫu được gắn với thuộc tính Title của file, nên LibreOffice/Word
    # hiển thị theo thuộc tính đó. Thay cả khối này bằng đoạn tên đề tài thường.
    sample_in_cover = cover.index("Mẫu Khóa Luận Tốt Nghiệp")
    inner_start = cover.rfind("<w:sdt>", 0, sample_in_cover)
    inner_end = cover.index("</w:sdt>", sample_in_cover) + len("</w:sdt>")
    break_index = cover.index('w:type="page"', inner_end)
    break_start = cover.rfind("<w:p ", 0, break_index)
    return (
        cover[:inner_start]
        + frontmatter.cover_title_vi()
        + frontmatter.cover_details_vi()
        + cover[break_start:]
    )


def add_page_break_before(xml: str) -> str:
    """Thêm pageBreakBefore vào đoạn đầu tiên (thường là Heading 1 của chương)."""
    return re.sub(r'(<w:pStyle w:val="[^"]+"/>)', r"\1<w:pageBreakBefore/>", xml, count=1)


def render_files(names: list, facts: dict, media: MediaRegistry, break_first: bool,
                 state: RenderState) -> str:
    xml = ""
    for index, name in enumerate(names):
        part = render((CONTENT / name).read_text(encoding="utf-8"), facts, media, CONTENT, state)
        if index > 0 or break_first:
            part = add_page_break_before(part)
        xml += part
    return xml


def front_matter(facts: dict, media: MediaRegistry) -> str:
    abstract = render((CONTENT / "00a-abstract.md").read_text(encoding="utf-8"), facts, media, CONTENT)
    thanks = render((CONTENT / "00b-thanks.md").read_text(encoding="utf-8"), facts, media, CONTENT)
    abbrev = render((CONTENT / "00c-abbrev.md").read_text(encoding="utf-8"), facts, media, CONTENT)
    return (
        frontmatter.cover_en()
        + frontmatter.page_title("ABSTRACT") + abstract
        + frontmatter.page_title("LỜI CẢM ƠN") + thanks
        + frontmatter.review_page("NHẬN XÉT CỦA GIÁO VIÊN HƯỚNG DẪN", "Giáo viên hướng dẫn")
        + frontmatter.review_page("NHẬN XÉT CỦA GIÁO VIÊN PHẢN BIỆN", "Giáo viên phản biện")
        + frontmatter.table_of_contents()
        + frontmatter.lists_of_figures_and_tables()
        + frontmatter.page_title("DANH MỤC TỪ VIẾT TẮT") + abbrev
    )


def write_media(work: Path, media: MediaRegistry) -> str:
    """Copy ảnh vào word/media, trả về các dòng Relationship cần thêm."""
    rels = ""
    for rid, path in media.items():
        target = f"media/report_{rid}{path.suffix.lower()}"
        shutil.copyfile(path, work / "word" / target)
        rels += (
            f'<Relationship Id="{rid}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="{target}"/>'
        )
    return rels


def update_styles(work: Path) -> None:
    styles_path = work / "word/styles.xml"
    styles = styles_path.read_text(encoding="utf-8")
    start = styles.index('w:styleId="Normal"')
    end = styles.index("</w:style>", start)
    normal = styles[start:end].replace('w:line="312"', 'w:line="360"')
    styles_path.write_text(styles[:start] + normal + styles[end:], encoding="utf-8")


def update_settings(work: Path) -> None:
    settings_path = work / "word/settings.xml"
    settings = settings_path.read_text(encoding="utf-8")
    if "<w:updateFields" not in settings:
        # Theo schema, updateFields đứng ngay trước hdrShapeDefaults / footnotePr / endnotePr / compat.
        for anchor in ["<w:hdrShapeDefaults", "<w:footnotePr", "<w:endnotePr", "<w:compat"]:
            if anchor in settings:
                settings = settings.replace(anchor, '<w:updateFields w:val="true"/>' + anchor, 1)
                break
    settings_path.write_text(settings, encoding="utf-8")


def build(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    facts = load_facts(ROOT / "results/eve-v2-report", ROOT / "scripts/demo.sh")
    media = MediaRegistry()
    state = RenderState()

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        with zipfile.ZipFile(TEMPLATE) as z:
            z.extractall(work)
        for path in work.rglob("*"):
            if path.is_symlink():
                path.unlink()

        document_path = work / "word/document.xml"
        document = document_path.read_text(encoding="utf-8")
        # Ảnh chèn vào dùng các tiền tố pic:, a:, wp:; file mẫu không khai báo sẵn hết ở thẻ gốc.
        root_end = document.index(">", document.index("<w:document "))
        root = document[:root_end]
        for prefix, uri in [("pic", PIC_NS), ("a", A_NS), ("wp", WP_NS)]:
            if f"xmlns:{prefix}=" not in root:
                document = document.replace("<w:document ", f'<w:document xmlns:{prefix}="{uri}" ', 1)

        body = (
            cover_vi(document)
            + front_matter(facts, media)
            + section_break(FOOTER_INFO_RID, title_page=True)
            + render_files(MAIN_FILES, facts, media, break_first=False, state=state)
            + section_break(FOOTER_PAGE_RID, start_page=True)
            + render_files(APPENDIX_FILES, facts, media, break_first=False, state=state)
            + section_properties(FOOTER_INFO_RID)
        )
        head = document[: document.index("<w:body>") + len("<w:body>")]
        document_path.write_text(head + body + "</w:body></w:document>", encoding="utf-8")

        (work / "word/footerPage.xml").write_text(footer_xml(True), encoding="utf-8")
        (work / "word/footerInfo.xml").write_text(footer_xml(False), encoding="utf-8")
        header_path = work / "word/header1.xml"
        header_path.write_text(fix_header(header_path.read_text(encoding="utf-8")), encoding="utf-8")

        rels_path = work / "word/_rels/document.xml.rels"
        rels = rels_path.read_text(encoding="utf-8")
        footer_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
        new_rels = (
            f'<Relationship Id="{FOOTER_PAGE_RID}" Type="{footer_type}" Target="footerPage.xml"/>'
            f'<Relationship Id="{FOOTER_INFO_RID}" Type="{footer_type}" Target="footerInfo.xml"/>'
            + write_media(work, media)
        )
        rels_path.write_text(rels.replace("</Relationships>", new_rels + "</Relationships>"), encoding="utf-8")

        types_path = work / "[Content_Types].xml"
        types = types_path.read_text(encoding="utf-8")
        footer_ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"
        overrides = (
            f'<Override PartName="/word/footerPage.xml" ContentType="{footer_ct}"/>'
            f'<Override PartName="/word/footerInfo.xml" ContentType="{footer_ct}"/>'
        )
        types_path.write_text(types.replace("</Types>", overrides + "</Types>"), encoding="utf-8")

        core_path = work / "docProps/core.xml"
        if core_path.exists():
            core = core_path.read_text(encoding="utf-8")
            core = re.sub(r"<dc:title>.*?</dc:title>", f"<dc:title>{frontmatter.TITLE_VI}</dc:title>", core)
            core_path.write_text(core, encoding="utf-8")

        update_styles(work)
        update_settings(work)

        target = out / OUTPUT_NAME
        if target.exists():
            target.unlink()
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(work.rglob("*")):
                if path.is_file():
                    z.write(path, path.relative_to(work).as_posix())

    shutil.copyfile(target, ROOT / "report" / OUTPUT_NAME)
    return target


if __name__ == "__main__":
    print(build(ROOT / "report/out"))
