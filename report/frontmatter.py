"""Các trang đầu của báo cáo: bìa tiếng Anh, tiêu đề trang, trang nhận xét, mục lục.

Định dạng bìa tiếng Anh theo "2. Yeu cau trinh bay tom tat _ tieng anh_KLTN.docx".
"""
from xml.sax.saxutils import escape

TITLE_VI = (
    "CẢI THIỆN HIỆU NĂNG MẠNG THÔNG QUA VIỆC CỘNG TÁC GIỮA CÁC NODE MẠNG "
    "NHẰM NGĂN CẢN CÁC TRUY VẤN XẤU"
)
TITLE_EN = (
    "IMPROVING NETWORK PERFORMANCE THROUGH COLLABORATIVE FILTERING "
    "OF MALICIOUS QUERIES AMONG NETWORK NODES"
)

def line(text: str, size: int = 26, bold: bool = False, align: str = "center",
         before: int = 0, after: int = 0, new_page: bool = False) -> str:
    """Một dòng định dạng trực tiếp (dùng cho bìa và tiêu đề trang). size tính theo nửa point.
    new_page: dòng này bắt đầu một trang mới (không dùng đoạn ngắt trang riêng, tránh sinh trang trắng)."""
    props = ""
    if bold:
        props += "<w:b/>"
    props += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    ppr = "<w:pageBreakBefore/>" if new_page else ""
    ppr += (
        f'<w:spacing w:before="{before}" w:after="{after}" w:line="276" w:lineRule="auto"/>'
        f'<w:ind w:firstLine="0"/><w:jc w:val="{align}"/>'
    )
    run = f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>' if text else ""
    return f"<w:p><w:pPr>{ppr}</w:pPr>{run}</w:p>"


def page_title(text: str, new_page: bool = True) -> str:
    """Tiêu đề trang đầu (không phải Heading nên không vào mục lục), mặc định sang trang mới."""
    return line(text, size=32, bold=True, before=0, after=360, new_page=new_page)


def cover_title_vi() -> str:
    """Tên đề tài trên bìa tiếng Việt."""
    return (
        line("KHOA CÔNG NGHỆ THÔNG TIN", size=26, bold=True, before=120)
        + line(TITLE_VI, size=32, bold=True, before=360, after=120)
    )


def cover_details_vi() -> str:
    """Phần thông tin trên bìa tiếng Việt, đặt dưới tên đề tài."""
    return (
        line("", before=240)
        + line("[HỌ TÊN SINH VIÊN] – [MSSV]", size=28, bold=True, before=240)
        + line("Ngành: [Ngành]", size=28, before=360)
        + line("Lớp: [Lớp] – Khóa: [Khóa]", size=26, before=120)
        + line("Giáo viên hướng dẫn: [Học vị] [Tên giáo viên hướng dẫn]", size=28, bold=True, align="left", before=960)
        + line("TP. HỒ CHÍ MINH, [Năm]", size=26, bold=True, before=1200)
    )


def cover_en() -> str:
    return (
        line("INDUSTRIAL UNIVERSITY OF HO CHI MINH CITY", size=24, bold=True, new_page=True)
        + line("FACULTY OF INFORMATION TECHNOLOGY", size=24, bold=True, before=60)
        + line("[HỌ TÊN SINH VIÊN]", size=28, bold=True, before=2400)
        + line(TITLE_EN, size=36, bold=True, before=1800)
        + line("Major: [Ngành]", size=28, before=600)
        + line("Supervisor: [Học vị] [Tên giáo viên hướng dẫn]", size=28, bold=True, align="left", before=2400)
        + line("HO CHI MINH CITY, [Năm]", size=24, before=2400)
    )


def dotted_line() -> str:
    """Một dòng chấm kéo hết chiều ngang (tab phải có dấu chấm dẫn)."""
    ppr = (
        '<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8788"/></w:tabs>'
        '<w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/><w:ind w:firstLine="0"/>'
    )
    return f"<w:p><w:pPr>{ppr}</w:pPr><w:r><w:tab/></w:r></w:p>"


def review_page(title: str, signer: str) -> str:
    xml = page_title(title)
    for _ in range(24):
        xml += dotted_line()
    xml += line("TP. Hồ Chí Minh, ngày ..... tháng ..... năm [Năm]", align="right", before=240)
    xml += line(signer, bold=True, align="right", before=60)
    xml += line("(Ký và ghi rõ họ tên)", align="right")
    return xml


def field_block(instr: str, hint: str) -> str:
    """Một trường TOC. Word cập nhật khi mở file (settings có updateFields)."""
    ppr = '<w:pPr><w:pStyle w:val="TOC1"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8778"/></w:tabs></w:pPr>'
    return (
        f'<w:p>{ppr}<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
        f'<w:r><w:instrText xml:space="preserve"> {escape(instr)} </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f'<w:r><w:t xml:space="preserve">{escape(hint)}</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    )


HINT = "Mở file bằng Word, nhấn chuột phải vào đây và chọn Update Field để cập nhật."


def table_of_contents() -> str:
    return page_title("MỤC LỤC") + field_block('TOC \\o "1-3" \\h \\z \\u', HINT)


def lists_of_figures_and_tables() -> str:
    return (
        page_title("DANH MỤC CÁC HÌNH VẼ")
        + field_block('TOC \\h \\z \\c "Hình"', HINT)
        + line("", before=480)
        + page_title("DANH MỤC CÁC BẢNG BIỂU", new_page=False)
        + field_block('TOC \\h \\z \\c "Bảng"', HINT)
    )
