# Hướng dẫn hoàn thiện báo cáo khóa luận

File cần nộp: `report/BaoCao_KLTN_onejack.docx`. Đây là **bản nháp**, đúng mẫu và đúng số liệu. Bạn đọc kỹ rồi viết lại bằng giọng của mình trước khi nộp.

## 1. Mở file bằng Word

Khi mở file, Word hỏi "This document contains fields that may refer to other files. Update the fields?": chọn **Yes**. Mục lục, danh mục hình và danh mục bảng sẽ tự điền số trang.

Nếu Word không hỏi, nhấn `Ctrl + A` rồi `F9` để cập nhật toàn bộ.

## 2. Thông tin cá nhân

Đã điền sẵn: họ tên, MSSV 21143751, lớp DHCNTT17ATT, ngành Công Nghệ Thông Tin (tiếng Anh: Information Technology), giáo viên hướng dẫn ThS. Nguyễn Xuân Lô, năm 2026. Bìa không ghi khóa học. Nếu cần ghi khóa, thêm vào dòng "Lớp: DHCNTT17ATT" trên bìa tiếng Việt.

## 3. Những chỗ đã điền sẵn, cần kiểm tra lại

- **Tên đề tài:** "CẢI THIỆN HIỆU NĂNG MẠNG: GIẢM ĐỘ TRỄ BẰNG CÁCH CHỌN ĐƯỜNG VÀ PHÂN PHỐI TẢI GIỮA CÁC ROUTER". Nếu giáo viên đổi tên, sửa `TITLE_VI` và `TITLE_EN` trong `report/frontmatter.py` rồi sinh lại (hoặc sửa thẳng trên bìa trong Word).
- **Hình 4.2:** ảnh chụp thật lab `net-perf` trên giao diện web EVE-NG (`report/figures/eve_topology.png`).
- **Ngày ở Lời cảm ơn:** đang ghi 05/12/2026. Đổi nếu nộp ngày khác.
- **Phụ lục C, D:** kế hoạch và nhật ký đã điền theo các mốc thực tế. Nếu giáo viên góp ý sau ngày 28/11, thêm dòng vào nhật ký.
- **Tài liệu tham khảo:** chỉ có tài liệu tiếng Anh và trang web. Nếu giáo viên yêu cầu thêm tài liệu tiếng Việt thì thêm mục "Tiếng Việt" lên đầu và **đánh số lại** toàn bộ danh mục cùng các trích dẫn `[1]`…`[14]` trong bài.
- Hai trang "Nhận xét của giáo viên" để trống, giáo viên tự ghi.

## 4. Đọc lại và viết lại

Nên viết lại kỹ nhất ở những phần mang tính cá nhân: Lời mở đầu, Lời cảm ơn, mục 5.1 (đoạn tự nhận xét) và các đoạn bạn thấy chưa giống cách mình viết. Mọi con số trong bài đã khớp với dữ liệu trong `results/eve/`. Nếu sửa câu có số liệu, giữ nguyên con số.

## 5. Kiểm tra số trang trong Word

Phần nội dung, từ LỜI MỞ ĐẦU tới hết TÀI LIỆU THAM KHẢO, khoảng 40 trang là mức tham khảo, không phải giới hạn trên. Đo bằng LibreOffice hiện là **38 trang**; Word có thể dàn trang lệch 1–2 trang.

## 6. Nếu muốn sinh lại file

Nội dung gốc nằm trong `report/content/*.md`, số liệu tự lấy từ `results/eve/`. Hình minh họa vẽ lại bằng `python3 report/figures.py`. Sau khi sửa nội dung gốc, chạy:

```
python3 report/check.py
```

Lệnh này sinh lại file Word, đếm số trang và báo lỗi định dạng. Lưu ý: sinh lại sẽ **ghi đè** mọi chỉnh sửa bạn đã làm trực tiếp trong file Word. Nên chọn một trong hai cách: sửa trong Word, hoặc sửa nội dung gốc rồi sinh lại.
