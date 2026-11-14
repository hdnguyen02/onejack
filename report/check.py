"""Kiểm tra báo cáo trước khi bàn giao. Chạy: python3 report/check.py

1. Số trang nội dung (LỜI MỞ ĐẦU tới hết TÀI LIỆU THAM KHẢO) <= 38 khi dàn trang bằng LibreOffice.
2. Font chữ Việt (ascii/hAnsi/eastAsia) trong document.xml chỉ là Times New Roman.
3. Không còn {{, [[REF, "Error!".
4. Heading 2 có Heading 3 thì có ít nhất 2 Heading 3.
5. Không có số đo gõ tay (ms, Mbit/s, giây) ngoài token {{...}}.
6. Mọi ảnh trong markup đều tồn tại.
Trả exit code 1 nếu có lỗi.
"""
import re
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from report.build import APPENDIX_FILES, CONTENT, FRONT_FILES, MAIN_FILES, build  # noqa: E402

MAX_CONTENT_PAGES = 38
MEASUREMENT = re.compile(r"\d+,\d+\s*(ms|Mbit/s|giây|s)\b|\d+\s*(ms|Mbit/s)\b")
FONT_ATTR = re.compile(r'w:(ascii|hAnsi|eastAsia)="([^"]+)"')


def strip_code_and_tokens(markup: str) -> str:
    markup = re.sub(r"```.*?```", "", markup, flags=re.S)
    return re.sub(r"\{\{\w+\}\}", "", markup)


def raw_measurements(markup: str) -> list:
    """Các số đo gõ tay (không qua token) trong markup."""
    found = []
    for match in MEASUREMENT.finditer(strip_code_and_tokens(markup)):
        found.append(match.group(0))
    return found


def heading3_violations(markup: str) -> list:
    """Các Heading 2 chỉ có đúng 1 Heading 3."""
    problems = []
    current = None
    count = 0
    for line in markup.splitlines() + ["## (hết)"]:
        if line.startswith("## ") or line.startswith("# ") or line.startswith("#! "):
            if current is not None and count == 1:
                problems.append(current)
            current = line[3:] if line.startswith("## ") else None
            count = 0
        elif line.startswith("### "):
            count += 1
    return problems


def font_violations(document_xml: str) -> list:
    problems = []
    for match in FONT_ATTR.finditer(document_xml):
        if match.group(2) != "Times New Roman":
            problems.append(f"{match.group(1)}={match.group(2)}")
    return problems


def leftover_markers(document_xml: str) -> list:
    return [marker for marker in ["{{", "[[REF", "Error!"] if marker in document_xml]


def missing_images(markup: str) -> list:
    missing = []
    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", markup):
        path = Path(match.group(1))
        if not path.is_absolute():
            path = CONTENT / path
        if not path.exists():
            missing.append(match.group(1))
    return missing


def export_pdf_with_updated_indexes(docx: Path, pdf: Path) -> None:
    """Mở bản sao bằng LibreOffice qua UNO, cập nhật mục lục và danh mục, xuất PDF."""
    import uno  # python3-uno, chỉ cần khi chạy check thật
    from com.sun.star.beans import PropertyValue

    port = 2002
    office = subprocess.Popen(
        ["soffice", "--headless", "--invisible", "--norestore",
         f"--accept=socket,host=127.0.0.1,port={port};urp;"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        resolver = uno.getComponentContext().ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", uno.getComponentContext())
        context = None
        for _ in range(60):
            try:
                context = resolver.resolve(
                    f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(0.5)
        if context is None:
            raise RuntimeError("Không kết nối được LibreOffice")
        desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)

        hidden = PropertyValue()
        hidden.Name = "Hidden"
        hidden.Value = True
        document = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(docx)), "_blank", 0, (hidden,))
        indexes = document.getDocumentIndexes()
        for i in range(indexes.getCount()):
            indexes.getByIndex(i).update()
        document.refresh()

        pdf_filter = PropertyValue()
        pdf_filter.Name = "FilterName"
        pdf_filter.Value = "writer_pdf_Export"
        document.storeToURL(uno.systemPathToFileUrl(str(pdf)), (pdf_filter,))
        document.close(True)
        try:
            desktop.terminate()
        except Exception:
            pass
    finally:
        try:
            office.wait(timeout=20)
        except subprocess.TimeoutExpired:
            office.kill()


def page_texts(pdf: Path) -> list:
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    return text.split("\f")


def first_page_with_line(pages: list, title: str, start: int = 0) -> int:
    """Trang đầu tiên (từ start) có một dòng đúng bằng title (bỏ qua dòng mục lục có chấm và số trang)."""
    for index in range(start, len(pages)):
        for line in pages[index].splitlines():
            if line.strip() == title:
                return index
    return -1


def content_pages(pdf: Path) -> int:
    pages = page_texts(pdf)
    start = first_page_with_line(pages, "LỜI MỞ ĐẦU")
    end = first_page_with_line(pages, "PHỤ LỤC", start + 1)
    if start < 0 or end < 0:
        return -1
    return end - start


def main() -> int:
    out = ROOT / "report/out"
    docx = build(out)
    pdf = out / "BaoCao_KLTN_onejack.pdf"
    export_pdf_with_updated_indexes(docx, pdf)

    with zipfile.ZipFile(docx) as z:
        document_xml = z.read("word/document.xml").decode("utf-8")

    errors = []
    pages = content_pages(pdf)
    print(f"Số trang nội dung (LibreOffice): {pages} / tối đa {MAX_CONTENT_PAGES}")
    if pages < 0:
        errors.append("không tìm thấy LỜI MỞ ĐẦU hoặc PHỤ LỤC trong PDF")
    elif pages > MAX_CONTENT_PAGES:
        errors.append(f"nội dung {pages} trang, vượt {MAX_CONTENT_PAGES}")

    for problem in font_violations(document_xml):
        errors.append(f"font không phải Times New Roman: {problem}")
    for marker in leftover_markers(document_xml):
        errors.append(f"còn sót '{marker}' trong tài liệu")

    for name in FRONT_FILES + MAIN_FILES + APPENDIX_FILES:
        markup = (CONTENT / name).read_text(encoding="utf-8")
        for heading in heading3_violations(markup):
            errors.append(f"{name}: mục '{heading}' chỉ có 1 tiểu mục")
        for value in raw_measurements(markup):
            errors.append(f"{name}: số đo gõ tay '{value}', hãy dùng token {{{{...}}}}")
        for image in missing_images(markup):
            errors.append(f"{name}: không có ảnh {image}")

    for error in errors:
        print("LỖI:", error)
    if errors:
        return 1
    print("Không có lỗi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
