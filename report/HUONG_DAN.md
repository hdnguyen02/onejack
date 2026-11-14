# Hướng dẫn hoàn thiện báo cáo khóa luận

File cần nộp: `report/BaoCao_KLTN_onejack.docx`. Đây là **bản nháp**, đúng mẫu và đúng số liệu. Bạn đọc kỹ rồi viết lại bằng giọng của mình trước khi nộp.

## 1. Mở file bằng Word

Khi mở file, Word hỏi "This document contains fields that may refer to other files. Update the fields?": chọn **Yes**. Mục lục, danh mục hình và danh mục bảng sẽ tự điền số trang.

Nếu Word không hỏi, nhấn `Ctrl + A` rồi `F9` để cập nhật toàn bộ.

## 2. Điền các chỗ trống `[...]`

Dùng Find & Replace (`Ctrl + H`) để thay một lần cho cả file:

| Tìm | Thay bằng |
|---|---|
| `[Họ tên]` | Họ tên của bạn |
| `[HỌ TÊN SINH VIÊN]` | Họ tên viết hoa (bìa) |
| `[MSSV]` | Mã số sinh viên |
| `[Lớp]` | Lớp, ví dụ DHKTPM18A |
| `[Khóa]` | Khóa học |
| `[Ngành]` | Ngành học (dùng ở bìa, header, bìa tiếng Anh) |
| `[Học vị]` | ThS. / TS. ... |
| `[Tên giáo viên hướng dẫn]` | Tên giáo viên hướng dẫn |

Header và footer cũng có các chỗ trống này. Find & Replace của Word thay được cả trong header và footer.

Ở bìa tiếng Anh, `Major: [Ngành]` cần ghi tên ngành bằng tiếng Anh, ví dụ "Software Engineering".

## 3. Những chỗ phải tự bổ sung

- **Hình 4.3:** mở `http://<IP máy EVE>`, vào lab `collab-defense`, chụp màn hình, rồi dán đè lên khung chờ. Giữ nguyên dòng nhãn "Hình 4.3 ..." bên dưới.
- **Lời mở đầu, mục 1:** câu `[Bổ sung đề tài liên quan của các khóa trước tại Khoa, nếu có.]`. Xóa câu này nếu không có gì để bổ sung.
- **Tài liệu tham khảo, nhóm Tiếng Việt:** nếu giáo viên yêu cầu tài liệu tiếng Việt thì thêm vào đầu danh mục. Khi đó **phải đánh số lại** toàn bộ danh mục và các trích dẫn `[1]`…`[12]` trong bài, vì số trích dẫn được ghi cố định.
- **Phụ lục C, D:** điền tiếp kế hoạch và nhật ký cho các tuần sau.
- **Lời cảm ơn:** chọn "thầy" hoặc "cô" thay cho "thầy/cô".

## 4. Đọc lại và viết lại

Nên viết lại kỹ nhất ở những phần mang tính cá nhân: Lời mở đầu, Lời cảm ơn, mục 5.1 (đoạn tự nhận xét) và các đoạn bạn thấy chưa giống cách mình viết. Mọi con số trong bài đã khớp với dữ liệu trong `results/eve-v2-report/`. Nếu sửa câu có số liệu, giữ nguyên con số.

## 5. Kiểm tra số trang trong Word

Quy định: phần nội dung, từ LỜI MỞ ĐẦU tới hết TÀI LIỆU THAM KHẢO, không quá 40 trang. Đo bằng LibreOffice hiện là **37 trang**. Word có thể dàn trang lệch 1–2 trang, nên kiểm tra lại số trang ở dòng TÀI LIỆU THAM KHẢO trong mục lục sau khi cập nhật.

## 6. Nếu muốn sinh lại file

Nội dung gốc nằm trong `report/content/*.md`, số liệu tự lấy từ `results/eve-v2-report/`. Sau khi sửa nội dung gốc, chạy:

```
python3 report/check.py
```

Lệnh này sinh lại file Word, đếm số trang và báo lỗi định dạng. Lưu ý: sinh lại sẽ **ghi đè** mọi chỉnh sửa bạn đã làm trực tiếp trong file Word. Nên chọn một trong hai cách: sửa trong Word, hoặc sửa nội dung gốc rồi sinh lại.
