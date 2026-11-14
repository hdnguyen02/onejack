"""Chuyển markup đơn giản của báo cáo thành XML body của Word (WordprocessingML).

Cú pháp (xem plan, Task 2):
  # Tiêu đề        Heading1 có đánh số chương
  #! Tiêu đề       Heading1 không đánh số
  ## / ###         Heading2 / Heading3
  - mục            gạch đầu dòng
  1. mục           danh sách đánh số (số viết thẳng vào chữ)
  **đậm** *nghiêng* `mã`
  ``` ... ```      khối code
  Bảng: tên        nhãn đặt trên bảng pipe ngay sau
  ![tên](file)     ảnh, nhãn đặt dưới
  >> chữ           đoạn căn phải (chữ ký, ngày tháng)
  {{khóa}}         số liệu từ facts
  [[REF:n]]        trích dẫn [n]
Chỉ dùng style có sẵn trong file mẫu của Khoa.
"""
import re
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

TEXT_WIDTH_DXA = 8788            # A4 trừ lề trái 3,5cm và lề phải 2cm
MIN_COLUMN_DXA = 900             # đủ chỗ cho chữ "STT" in đậm mà không gãy dòng
MAX_IMAGE_EMU = 5400000          # 15cm
EMU_PER_INCH = 914400
BULLET_NUM_ID = 8                # danh sách gạch đầu dòng có sẵn trong numbering.xml của mẫu
CODE_SIZE = 24                   # 12pt


class MediaRegistry:
    """Ghi nhớ các ảnh đã chèn, mỗi ảnh một rId."""

    def __init__(self, first_id: int = 1000):
        self._next = first_id
        self._items = []

    def add(self, path: Path) -> str:
        rid = f"rIdImg{self._next}"
        self._next += 1
        self._items.append((rid, Path(path)))
        return rid

    def items(self) -> list:
        return list(self._items)


def substitute(text: str, facts: dict) -> str:
    """Thay {{khóa}} bằng số liệu, [[REF:n]] bằng [n]. Khóa lạ thì báo lỗi."""
    def fact(match):
        key = match.group(1)
        if key not in facts:
            raise KeyError(f"Không có số liệu '{key}'")
        return facts[key]

    text = re.sub(r"\{\{(\w+)\}\}", fact, text)
    text = re.sub(r"\[\[REF:(\d+)\]\]", r"[\1]", text)
    return text


def run(text: str, bold: bool = False, italic: bool = False, size: int = 0) -> str:
    props = ""
    if bold:
        props += "<w:b/>"
    if italic:
        props += "<w:i/>"
    if size:
        props += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def inline_runs(text: str, facts: dict, bold: bool = False) -> str:
    """Tách **đậm**, *nghiêng*, `mã` thành các run."""
    text = substitute(text, facts)
    parts = re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text)
    runs = ""
    for part in parts:
        if part == "":
            continue
        if part.startswith("**") and part.endswith("**"):
            runs += run(part[2:-2], bold=True)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            runs += run(part[1:-1], bold=bold, italic=True)
        elif part.startswith("`") and part.endswith("`"):
            runs += run(part[1:-1], bold=bold)
        else:
            runs += run(part, bold=bold)
    return runs


def paragraph(runs: str, style: str = "", extra_ppr: str = "") -> str:
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    ppr += extra_ppr
    if ppr:
        ppr = f"<w:pPr>{ppr}</w:pPr>"
    return f"<w:p>{ppr}{runs}</w:p>"


def field(instr: str, shown: str) -> str:
    return (
        f'<w:fldSimple w:instr=" {instr} "><w:r><w:rPr><w:noProof/></w:rPr>'
        f"<w:t>{shown}</w:t></w:r></w:fldSimple>"
    )


def caption(label: str, title: str, facts: dict, keep_next: bool) -> str:
    """Nhãn kiểu 'Hình 2.1 Tên', số chương lấy từ Heading 1 gần nhất."""
    runs = run(f"{label} ")
    runs += field("STYLEREF 1 \\s", "1")
    runs += run(".")
    runs += field(f"SEQ {label} \\* ARABIC \\s 1", "1")
    runs += run(" ") + inline_runs(title, facts)
    extra = "<w:keepNext/>" if keep_next else ""
    return paragraph(runs, "Caption", extra)


def heading(level: int, text: str, facts: dict, numbered: bool = True) -> str:
    extra = ""
    if not numbered:
        extra = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
    elif level == 1:
        # Mẫu đánh số "CHƯƠNG %1" không có khoảng cách; chữ tiêu đề tự bắt đầu bằng ": ".
        text = ": " + text
    return paragraph(inline_runs(text, facts), f"Heading{level}", extra)


def bullet(text: str, facts: dict) -> str:
    extra = f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{BULLET_NUM_ID}"/></w:numPr>'
    return paragraph(inline_runs(text, facts), "ListParagraph", extra)


def numbered(number: str, text: str, facts: dict) -> str:
    # Số viết thẳng vào chữ để mỗi danh sách tự bắt đầu lại từ 1.
    extra = '<w:ind w:left="567" w:hanging="283"/>'
    return paragraph(run(f"{number}. ") + inline_runs(text, facts), "ListParagraph", extra)


def code_block(lines: list) -> str:
    xml = ""
    extra = '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="284" w:firstLine="0"/><w:jc w:val="left"/>'
    for line in lines:
        xml += paragraph(run(line, size=CODE_SIZE), "", extra)
    return xml


def column_widths(rows: list) -> list:
    """Chia độ rộng cột theo độ dài chữ dài nhất mỗi cột, tổng bằng TEXT_WIDTH_DXA."""
    count = len(rows[0])
    weights = []
    for col in range(count):
        longest = max(len(row[col]) for row in rows if col < len(row))
        weights.append(min(max(longest, 6), 60))
    total = sum(weights)
    widths = [max(TEXT_WIDTH_DXA * w // total, MIN_COLUMN_DXA) for w in weights]
    # Bù phần dư hoặc thiếu vào cột rộng nhất để tổng luôn bằng TEXT_WIDTH_DXA.
    widest = widths.index(max(widths))
    widths[widest] += TEXT_WIDTH_DXA - sum(widths)
    return widths


def table(rows: list, facts: dict) -> str:
    widths = column_widths(rows)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    cell_ppr = '<w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/>'
    xml = (
        '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
        f'<w:tblW w:w="{TEXT_WIDTH_DXA}" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr>'
        f"<w:tblGrid>{grid}</w:tblGrid>"
    )
    for index, row in enumerate(rows):
        header = index == 0
        trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if header else "<w:trPr><w:cantSplit/></w:trPr>"
        xml += f"<w:tr>{trpr}"
        for col, width in enumerate(widths):
            text = row[col] if col < len(row) else ""
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/>' if header else ""
            xml += (
                f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>'
                + paragraph(inline_runs(text, facts, bold=header), "", cell_ppr)
                + "</w:tc>"
            )
        xml += "</w:tr>"
    return xml + "</w:tbl>"


def image(path: Path, media: MediaRegistry) -> str:
    with Image.open(path) as img:
        width_px, height_px = img.size
        dpi = img.info.get("dpi", (96, 96))[0] or 96
    cx = int(width_px / dpi * EMU_PER_INCH)
    cy = int(height_px / dpi * EMU_PER_INCH)
    if cx > MAX_IMAGE_EMU:
        cy = cy * MAX_IMAGE_EMU // cx
        cx = MAX_IMAGE_EMU
    rid = media.add(path)
    pic_id = len(media.items())
    name = escape(Path(path).name)
    drawing = (
        "<w:drawing>"
        f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pic_id}" name="{name}"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{pic_id}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        "</a:graphicData></a:graphic></wp:inline></w:drawing>"
    )
    extra = '<w:keepNext/><w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="center"/>'
    return paragraph(f"<w:r>{drawing}</w:r>", "", extra)


def split_row(line: str) -> list:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render(markup: str, facts: dict, media: MediaRegistry, base_dir: Path = Path(".")) -> str:
    lines = markup.splitlines()
    xml = ""
    i = 0
    pending_caption = None
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            i += 1
            continue

        if stripped.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            xml += code_block(block)
            i += 1
            continue

        if stripped.startswith("Bảng:"):
            pending_caption = stripped[len("Bảng:"):].strip()
            i += 1
            continue

        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_row(lines[i])
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if pending_caption is not None:
                xml += caption("Bảng", pending_caption, facts, keep_next=True)
                pending_caption = None
            xml += table(rows, facts)
            continue

        figure = re.fullmatch(r"!\[(.*)\]\((.+)\)", stripped)
        if figure:
            path = Path(figure.group(2))
            if not path.is_absolute():
                path = base_dir / path
            xml += image(path, media)
            xml += caption("Hình", figure.group(1), facts, keep_next=False)
            i += 1
            continue

        if stripped.startswith("#! "):
            xml += heading(1, stripped[3:], facts, numbered=False)
        elif stripped.startswith("### "):
            xml += heading(3, stripped[4:], facts)
        elif stripped.startswith("## "):
            xml += heading(2, stripped[3:], facts)
        elif stripped.startswith("# "):
            xml += heading(1, stripped[2:], facts)
        elif stripped.startswith(">> "):
            extra = '<w:spacing w:before="0"/><w:ind w:firstLine="0"/><w:jc w:val="right"/>'
            xml += paragraph(inline_runs(stripped[3:], facts), "", extra)
        elif stripped.startswith("- "):
            xml += bullet(stripped[2:], facts)
        elif re.match(r"\d+\. ", stripped):
            number, text = stripped.split(". ", 1)
            xml += numbered(number, text, facts)
        elif stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
            # Đoạn chỉ có chữ đậm là tiêu đề nhỏ: giữ cùng trang với đoạn sau.
            xml += paragraph(inline_runs(stripped, facts), "", "<w:keepNext/>")
        else:
            xml += paragraph(inline_runs(stripped, facts))
        i += 1
    return xml
