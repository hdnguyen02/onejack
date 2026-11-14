# Báo cáo KLTN onejack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sinh file `report/BaoCao_KLTN_onejack.docx` dựa trên file mẫu của Khoa. Phần nội dung không quá 40 trang, số liệu lấy từ `results/eve-v2-report/`, văn phong tự nhiên.

**Architecture:** Nội dung viết bằng markup đơn giản (`report/content/*.md`). Script Python thuần (thư viện chuẩn và PIL) chuyển markup thành XML của Word, rồi ghép vào bản giải nén của `MauTrinhBayDoAn.docx`, giữ nguyên style, header/footer và trang bìa. Mọi con số đo đạc đi qua token `{{tên}}`, được tính từ file kết quả, nên không thể gõ tay. Script kiểm tra dùng LibreOffice để xuất PDF, đếm trang và soát định dạng.

**Tech Stack:** Python 3 (zipfile, xml, unittest), PIL, LibreOffice headless (`soffice`, `python3-uno`), poppler (`pdftotext`, `pdftoppm`), gnuplot, `validate.py` của skill docx.

**Spec:** `docs/superpowers/specs/2026-11-14-kltn-report-design.md`

## Global Constraints

- A4. Lề trên 1701, dưới 1701, trái 1985, phải 1134 (twip), giữ như file mẫu.
- Times New Roman cỡ 13 cho toàn bộ văn bản, kể cả bảng, nhãn hình/bảng và đoạn code. Không dùng font khác trong `document.xml`.
- Style Normal giãn dòng `w:line="360" w:lineRule="auto"` (1,5 dòng).
- Chỉ dùng style có sẵn của mẫu: Normal, Heading1–3, Caption, TOC1–3, TableofFigures, Tailieuthamkhao, ListParagraph, TableGrid.
- Nhãn: `Hình <chương>.<số>` đặt dưới hình, `Bảng <chương>.<số>` đặt trên bảng, căn giữa, style Caption, dùng trường STYLEREF + SEQ.
- Mục lục tới cấp 3. Mỗi Heading 2 có Heading 3 thì phải có ít nhất 2 Heading 3.
- Trang 1 bắt đầu ở LỜI MỞ ĐẦU, số trang góc dưới bên phải. Phụ lục không đánh số trang.
- Nội dung (LỜI MỞ ĐẦU tới hết TÀI LIỆU THAM KHẢO) đo bằng LibreOffice **≤ 38 trang**, chừa 2 trang cho chênh lệch giữa LibreOffice và Word.
- Chỗ trống giữ nguyên dạng: `[Họ tên]`, `[MSSV]`, `[Lớp]`, `[Ngành]`, `[Khóa]`, `[Tên giáo viên hướng dẫn]`, `[Học vị]`, `[Năm]`.
- Mọi con số đo đạc (ms, Mbit/s, giây, số gói) trong nội dung phải viết bằng token `{{...}}`. Số thập phân dùng dấu phẩy kiểu Việt.
- Văn phong theo mục 5a của spec. Tài liệu tham khảo chỉ dùng các nguồn có thật liệt kê trong spec.
- Commit trên nhánh `v2`. Commit message không nhắc tới Claude. File PDF và ảnh xem thử nằm trong `report/out/`, đã được bỏ qua bởi git.

## Review Focus

1. **Ký tự đặc biệt trong nội dung** (`&`, `<`, `>`, ngoặc kép, chữ Việt có dấu) phải được escape đúng để Word mở được file. Test: `test_escapes_xml_special_chars` (Task 2).
2. **Chỗ trống dạng `[Họ tên]`** không bị hiểu nhầm thành link hay markup, phải giữ nguyên chữ. Test: `test_placeholders_kept_verbatim` (Task 2).
3. **File hỏng với Word** dù LibreOffice vẫn mở được (thiếu relationship, sai content type của ảnh). Test: `validate.py` chạy không lỗi (Task 3, Task 12).
4. **Số liệu gõ tay lệch khỏi dữ liệu đo.** Cần chặn bằng token. Test: `test_raw_measurements_rejected` (Task 4).
5. **Số trang khác nhau giữa LibreOffice và Word** làm vượt 40 trang. Cách chặn: ngưỡng 38 trang trong `check.py` (Task 4), kèm hướng dẫn kiểm tra lại trong Word ở Task 12.

---

### Task 1: Thư mục report và bảng số liệu (facts)

**Files:**
- Create: `report/template/MauTrinhBayDoAn.docx` (copy từ `~/Downloads/drive-download-20261114T075932Z-1-001/`)
- Create: `report/facts.py`, `report/tests/test_facts.py`
- Modify: `.gitignore` (thêm `report/out/`)

**Interfaces:**
- Produces: `load_facts(results_dir: Path, demo_sh: Path) -> dict[str, str]`. Giá trị đã định dạng tiếng Việt (dấu phẩy thập phân, dấu chấm phân cách hàng nghìn).

- [ ] **Step 1: Viết test hỏng** `report/tests/test_facts.py::test_facts_match_dataset`:

```python
f = load_facts(ROOT / "results/eve-v2-report", ROOT / "scripts/demo.sh")
assert f["rtt_off"] == "407,97" and f["rtt_on"] == "6,29" and f["rtt_inband"] == "6,91"
assert f["link_off"] == "10,02" and f["link_on"] == "0,17" and f["link_inband"] == "0,19"
assert f["detect_off"] == "0,566" and f["detect_on"] == "0,495" and f["detect_inband"] == "0,577"
assert f["block_on_ms"] == "7" and f["block_inband_ms"] == "4"
assert f["qos_normal_eve"] == "401,94" and f["qos_prio_eve"] == "3,07"
assert f["qos_normal_netns"] == "399,85" and f["qos_prio_netns"] == "0,07"
assert f["qos_prio_pkts"] == "100" and f["qos_normal_dropped"] == "55.965"
assert f["duration"] == "60" and f["attack_at"] == "15" and f["client_rate"] == "20"
assert f["attack_rate"] == "5.000" and f["attack_size"] == "1.000" and f["threshold"] == "200"
assert f["bottleneck"] == "10" and f["queue_kb"] == "500"
```

- [ ] **Step 2: Chạy** `python3 -m unittest report/tests/test_facts.py`. Kỳ vọng: FAIL (chưa có `load_facts`).
- [ ] **Step 3: Viết `load_facts`.**
  - RTT và lưu lượng link: tính như `scripts/plot.sh`, tức trung bình các dòng có `t > 15`.
  - Thời gian phát hiện và chặn: lấy từ `events_*.log`.
  - Số liệu qos: lấy từ `qos-check-*.txt`. Số gói làn ưu tiên và số gói làn thường bị vứt lấy từ khối `bfifo 101` và `bfifo 102` trong `qos-check-eve.txt`.
  - Thông số demo: đọc từ khối "Thông số demo" trong `demo.sh`.
  - `bottleneck` và `queue_kb`: đọc từ `lab/r1.sh` (`TC_RATE` mặc định `10mbit`, `bfifo limit 500000`).
- [ ] **Step 4: Chạy lại test.** Kỳ vọng: PASS.
- [ ] **Step 5: Commit** `feat(report): add facts loader from measured dataset`.

### Task 2: Bộ chuyển markup sang XML của Word

**Files:**
- Create: `report/docxgen.py`, `report/tests/test_docxgen.py`

**Interfaces:**
- Consumes: `load_facts` (Task 1).
- Produces:
  - `render(markup: str, facts: dict[str, str], media: MediaRegistry) -> str`: trả về chuỗi các phần tử `<w:p>` và `<w:tbl>`.
  - `class MediaRegistry`, gồm `add(path: Path) -> str` (trả về rId) và `items() -> list[tuple[str, Path]]`.
  - Ném `KeyError` nếu gặp token không có trong `facts`.

**Cú pháp markup** (đã chốt):

| Markup | Chuyển thành |
|---|---|
| `# Tiêu đề` | Heading1, chương có đánh số |
| `#! Tiêu đề` | Heading1 không đánh số (LỜI MỞ ĐẦU, TÀI LIỆU THAM KHẢO, PHỤ LỤC). Tắt số bằng `numPr` với `numId=0` |
| `##` / `###` | Heading2 / Heading3 |
| Dòng thường | Normal |
| `- ` | ListParagraph có gạch đầu dòng (dùng một `numId` dấu "-" có sẵn trong numbering.xml của mẫu) |
| `1. ` | ListParagraph đánh số |
| `**đậm**`, `*nghiêng*` | đậm, nghiêng |
| `` `mã` `` | giữ chữ, không đổi font |
| Khối ```` ``` ```` | đoạn Times New Roman 12, không thụt đầu dòng, giữ khoảng trắng (`xml:space="preserve"`) |
| `Bảng: <tên>` ngay trước bảng pipe | nhãn Caption đặt **trên** bảng; bảng dùng TableGrid, độ rộng cột theo DXA, tổng bằng 8788 |
| `![<tên>](đường/dẫn.png)` | ảnh căn giữa, rộng tối đa 15cm, nhãn Caption đặt **dưới** ảnh |
| `{{khóa}}` | thay bằng `facts[khóa]` |
| `[[REF:n]]` | `[n]` |
| `[Họ tên]`… | giữ nguyên chữ |

- [ ] **Step 1: Viết các test hỏng:**
  - `test_heading_levels`: `# A` có `w:pStyle w:val="Heading1"`; `#! B` có `<w:numId w:val="0"/>`; `## C` → Heading2; `### D` → Heading3.
  - `test_escapes_xml_special_chars`: `a & b < c "d"` → XML có `a &amp; b &lt; c`, và `xml.dom.minidom.parseString` chạy không lỗi khi bọc trong phần tử gốc.
  - `test_placeholders_kept_verbatim`: `[Họ tên] và [MSSV]` → `<w:t` chứa đúng chuỗi `[Họ tên] và [MSSV]`.
  - `test_table_caption_above`: vị trí `Caption` < vị trí `<w:tbl>`; nhãn chứa `SEQ Bảng`.
  - `test_figure_caption_below`: vị trí `<w:drawing>` < vị trí `Caption`; nhãn chứa `SEQ Hình`; `media.items()` có 1 phần tử.
  - `test_fact_tokens`: `{{rtt_off}} ms` với `{"rtt_off": "407,97"}` → `407,97 ms`; token lạ → `KeyError`.
  - `test_code_block_preserves_spaces`: dòng `    poll(...)` giữ 4 khoảng trắng đầu dòng.
- [ ] **Step 2: Chạy** `python3 -m unittest report/tests/test_docxgen.py`. Kỳ vọng: FAIL.
- [ ] **Step 3: Viết `render` và `MediaRegistry`.** Cấu trúc trường của nhãn chép từ đoạn nhãn có sẵn trong mẫu ("Thao tác cập nhật mục lục"), đổi dấu phân cách số thành `.`.
- [ ] **Step 4: Chạy lại test.** Kỳ vọng: PASS cả 7 test.
- [ ] **Step 5: Commit** `feat(report): add markup to OOXML renderer`.

### Task 3: Ghép tài liệu vào file mẫu

**Files:**
- Create: `report/build.py`, `report/frontmatter.py`, `report/tests/test_build.py`
- Create (nội dung tạm cho test): `report/content/00-front.md` … `report/content/09-appendix.md`, mỗi file 1 dòng.

**Interfaces:**
- Consumes: `render`, `MediaRegistry` (Task 2); `load_facts` (Task 1).
- Produces: `build(out: Path) -> Path`, ghi file `report/out/BaoCao_KLTN_onejack.docx` rồi copy sang `report/BaoCao_KLTN_onejack.docx`.

**Thứ tự body** (theo spec mục 4), chia **3 section**:

| Section | Gồm | Đánh số trang |
|---|---|---|
| 1 | Bìa tiếng Việt (giữ khối bìa của mẫu, thay chữ "Mẫu Khóa Luận Tốt Nghiệp" bằng tên đề tài, ngành, `[Họ tên]`, `[MSSV]`, GVHD, `TP. HỒ CHÍ MINH, [Năm]`); bìa tiếng Anh (cỡ chữ đúng spec, tên đề tài: "IMPROVING NETWORK PERFORMANCE THROUGH COLLABORATIVE FILTERING OF MALICIOUS QUERIES AMONG NETWORK NODES"); Abstract; Lời cảm ơn; 2 trang nhận xét (tiêu đề + 25 dòng chấm); MỤC LỤC (`TOC \o "1-3" \h \z \u`); DANH MỤC CÁC HÌNH VẼ (`TOC \h \z \c "Hình"`); DANH MỤC CÁC BẢNG BIỂU (`TOC \h \z \c "Bảng"`); DANH MỤC TỪ VIẾT TẮT | không số trang |
| 2 | LỜI MỞ ĐẦU tới hết TÀI LIỆU THAM KHẢO | `pgNumType start=1`, footer có trường PAGE căn phải |
| 3 | PHỤ LỤC | footer không có PAGE |

**Thay đổi khác:**
- `styles.xml`: Normal `w:line` đổi từ 312 thành 360.
- `settings.xml`: thêm `<w:updateFields w:val="true"/>`.
- Header: "Khóa luận tốt nghiệp chuyên ngành [Ngành]". Footer: `[Họ tên] – [Lớp]`. Bỏ tô vàng và MACROBUTTON.
- Ảnh: thêm vào `word/media/`, khai báo trong `document.xml.rels` và `[Content_Types].xml` (Default png).
- Trước khi zip: xóa các file symlink trong thư mục giải nén.

- [ ] **Step 1: Viết test hỏng** `test_build.py::test_build_produces_valid_docx`:
  - `build()` trả về đường dẫn có tồn tại.
  - `validate.py <file> --original report/template/MauTrinhBayDoAn.docx` có exit code 0. Đường dẫn: `/home/devnguyenho/.claude/skills/synced/6eced0eb-06d5-47f3-a786-21d89e367b0b_66d3d5dd-78fe-4599-973b-5b4a18e76758/docx/scripts/office/validate.py`.
  - Trong `document.xml` có đúng 3 `w:sectPr`, có `w:pgNumType w:start="1"`, và chứa `[MSSV]`.
- [ ] **Step 2: Chạy.** Kỳ vọng: FAIL.
- [ ] **Step 3: Viết `build.py` và `frontmatter.py`.**
- [ ] **Step 4: Chạy test**, rồi xuất PDF bằng `soffice --headless --convert-to pdf --outdir report/out report/out/BaoCao_KLTN_onejack.docx`. Kỳ vọng: test PASS, PDF mở được, bìa giống mẫu khi xem bằng `pdftoppm -r 50`.
- [ ] **Step 5: Commit** `feat(report): assemble report into faculty template`.

### Task 4: Script kiểm tra

**Files:**
- Create: `report/check.py`, `report/tests/test_check.py`

**Interfaces:**
- Consumes: `build` (Task 3).
- Produces: `python3 report/check.py`. In bảng kết quả và trả exit code 1 nếu có lỗi. Bản có cập nhật mục lục để đếm trang được tạo bằng UNO (`python3-uno`): mở bản sao, gọi `getDocumentIndexes()` rồi `.update()` từng mục, lưu PDF vào `report/out/`. **Không** ghi đè file `.docx` giao cho người dùng.

**Các kiểm tra:**
1. **Số trang nội dung ≤ 38**, đếm từ trang chứa "LỜI MỞ ĐẦU" (tiêu đề, không phải dòng trong mục lục) tới trang ngay trước "PHỤ LỤC", dùng `pdftotext` từng trang.
2. **Font:** mọi `w:rFonts` trong `document.xml` là Times New Roman, hoặc không khai báo.
3. Không còn `{{`, `[[REF`, "Error!".
4. **Mỗi Heading2 có Heading3 thì có ít nhất 2 Heading3** (đọc từ markup).
5. **Số liệu gõ tay:** khớp regex `\d+,\d+\s*(ms|Mbit/s|giây|s)\b|\d+\s*(ms|Mbit/s)\b` trên markup **sau khi bỏ** các token `{{...}}` và các khối code. Có kết quả khớp là lỗi. Câu thường như "mỗi 1 giây" vẫn được phép. Băng thông nút cổ chai cũng phải dùng token: "{{bottleneck}} Mbit/s".
6. Mọi ảnh trong markup đều tồn tại.

- [ ] **Step 1: Viết test hỏng:**
  - `test_raw_measurements_rejected`: markup `RTT 407,97 ms` → có lỗi; `RTT {{rtt_off}} ms` → không lỗi.
  - `test_heading3_min_two`: `## A\n### a1` → lỗi; thêm `### a2` → hết lỗi.
  - `test_font_check`: XML có `w:ascii="Courier New"` → lỗi.
- [ ] **Step 2: Chạy.** Kỳ vọng: FAIL.
- [ ] **Step 3: Viết `check.py`.**
- [ ] **Step 4: Chạy test** rồi `python3 report/check.py`. Kỳ vọng: test PASS; check chạy hết và in số trang nội dung với bản nội dung tạm.
- [ ] **Step 5: Commit** `feat(report): add report checks (pages, fonts, facts, structure)`.

### Task 5: Hình vẽ

**Files:**
- Create: `report/figures.py` → `report/figures/*.png`

**Interfaces:**
- Produces: các file PNG dưới đây (Task 7–10 tham chiếu theo đúng tên). Chữ trong hình dùng Liberation Serif, cỡ tương đương 11pt khi in rộng 15cm, nền trắng, 200 dpi.

| File | Nội dung |
|---|---|
| `tcpip.png` | 4 tầng TCP/IP, đánh dấu UDP và vị trí của raw socket |
| `bottleneck_queue.png` | hàng đợi ở nút cổ chai, gói client xếp sau gói rác |
| `victim_vs_edge.png` | chặn ở R3 (rác vẫn chiếm R1→R3) so với chặn ở R1 |
| `two_lane_queue.png` | tbf → prio 2 làn → bộ lọc DSCP |
| `sequence.png` | trình tự: attacker → R3 phát hiện → BLOCK → R1/R2 chặn |
| `topology.png` | 6 node, địa chỉ IP, mạng CTRL, mạng MGMT |
| `guard_flow.png` | lưu đồ vòng lặp `poll()` của guard |
| `tmux_inband.png` | vẽ lại 4 ô từ `results/eve-v2-report/tmux/inband_pane*.txt`, đúng nguyên văn chữ đã chụp |
| `rtt.png`, `link.png` | `scripts/plot.sh results/eve-v2-report`, rồi copy sang |

- [ ] **Step 1: Viết `figures.py`** (một hàm cho mỗi hình), chạy `python3 report/figures.py`.
- [ ] **Step 2: Kiểm tra.** Kỳ vọng: có đủ 9 file PNG. Xem từng hình bằng Read để soát chữ và bố cục; trong `tmux_inband.png`, các dòng log phải khớp nguyên văn file chụp.
- [ ] **Step 3: Commit** `feat(report): generate report figures`.

### Task 6–11: Viết nội dung

Mỗi task viết một file trong `report/content/`, theo dàn ý và số trang ở spec mục 5 và văn phong mục 5a. Mỗi task kết thúc bằng các bước giống nhau:

- [ ] Build: `python3 report/build.py`.
- [ ] Kiểm tra: `python3 report/check.py`. Kỳ vọng: chỉ còn có thể sai số trang tổng của các chương chưa viết, không có lỗi nào khác.
- [ ] Đọc lại phần vừa viết trên PDF (`pdftoppm -r 60`) để soát lỗi hiển thị.
- [ ] **Đối chiếu code:** mọi câu mô tả cách chương trình chạy phải đúng với `src/` và `scripts/` trên nhánh `v2`. Ghi số dòng đã đối chiếu vào commit message nếu có trích code.
- [ ] Commit `docs(report): <phần>`.

| Task | File | Nội dung | Số trang tối đa (theo PDF) |
|---|---|---|---|
| 6 | `00-front.md` | Abstract (1 trang, 5 mục theo quy định), Lời cảm ơn, Danh mục từ viết tắt (bảng 2 cột, xếp A–Z, gồm ít nhất: API, BGP, CNTT, CSV, DDoS, DoS, DSCP, EF, GVHD, IP, KVM, MAC, QoS, RFC, RTBH, RTT, SSH, TCP, TOS, UDP, VM) | 1 trang Abstract |
| 7 | `01-mo-dau.md`, `02-chuong1.md` | Lời mở đầu, Chương 1 (gồm Bảng 1.1 mục tiêu có chỉ số) | 2 + 3 |
| 8 | `03-chuong2.md` | Chương 2 (2.1–2.7; Hình 2.1–2.4) | 9 |
| 9 | `04-chuong3.md` | Chương 3 (Bảng 3.1 so sánh 3 phương án; Hình 3.1 sequence) | 5 |
| 10 | `05-chuong4.md` | Chương 4 (Hình 4.1–4.6, Bảng 4.1–4.6; Hình 4.3 là khung `[Ảnh chụp giao diện EVE-NG]`; đoạn code mỗi đoạn ≤ 15 dòng) | 14 |
| 11 | `06-chuong5.md`, `07-tltk.md`, `09-appendix.md` | Chương 5 (đối chiếu Bảng 1.1; 7 hạn chế; hướng phát triển); Tài liệu tham khảo (đúng thứ tự và định dạng của Khoa, chỉ dùng nguồn trong spec, nhóm tiếng Việt để chỗ trống); Phụ lục (hướng dẫn chạy, code guard, Kế hoạch thực hiện, Nhật ký làm việc lấy từ `git log --date=short --format='%ad %s'`) | 3 + 1 |

### Task 12: Hoàn thiện và bàn giao

- [ ] **Step 1:** Build, `check.py` sạch lỗi, `validate.py` exit 0.
- [ ] **Step 2:** Xuất toàn bộ PDF (đã cập nhật mục lục), xem tất cả các trang ở `-r 50` dạng montage. Soát:
  - Bìa giống mẫu.
  - Mục lục có đủ tới cấp 3.
  - Danh mục hình và bảng đủ số lượng.
  - Số trang bắt đầu đúng ở LỜI MỞ ĐẦU.
  - Phụ lục không có số trang.
- [ ] **Step 3:** Nếu nội dung > 38 trang, rút gọn Chương 2 trước, Chương 4 sau. Không cắt phần kết quả.
- [ ] **Step 4:** Commit `docs(report): final thesis report draft`.
- [ ] **Step 5:** Viết `report/HUONG_DAN.md`:
  - Mở file bằng Word, chọn **Yes** khi Word hỏi cập nhật trường.
  - Điền các chỗ trống dạng `[...]`.
  - Chèn ảnh EVE vào Hình 4.3.
  - Đọc lại và viết lại bằng giọng của mình.
  - Kiểm tra lại số trang trong Word.
