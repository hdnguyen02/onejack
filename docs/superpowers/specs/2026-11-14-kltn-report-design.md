# Thiết kế: Báo cáo khóa luận tốt nghiệp cho đề tài onejack

Ngày: 2026-11-14. Nhánh: `v2`.

## 1. Mục đích

Người dùng cần **một file Word báo cáo khóa luận tốt nghiệp (KLTN)** để nộp giáo viên hướng dẫn (GVHD) và hội đồng của Khoa CNTT, Trường ĐH Công nghiệp TP.HCM. Đề tài: *"Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu"*. Yêu cầu của đề: lập trình ứng dụng demo bằng C trên Linux, chạy trên EVE-NG.

- **Hạn nộp:** báo cáo cho GVHD **trước 06/12/2026**. Hội đồng đánh giá sáng 23/12/2026. Nguồn: ảnh thông báo trong thư mục mẫu.
- **Người đọc:** GVHD, giáo viên phản biện, hội đồng. Họ đánh giá cả nội dung kỹ thuật lẫn việc tuân thủ mẫu trình bày.
- **Khóa luận cá nhân:** một sinh viên thực hiện, theo người dùng xác nhận.
- **Người dùng** là dev .NET, không chuyên mạng. Báo cáo phải giúp họ hiểu và bảo vệ được đề tài, nên lời văn cần rõ, đi từ khái niệm tới hiện thực.

## 2. Mục tiêu, không làm, và điều tuyệt đối tránh

**Mục tiêu**

1. Phần nội dung, tính từ *Lời mở đầu* tới hết *Tài liệu tham khảo*, khoảng 40 trang. **Cập nhật 2026-11-15:** người dùng làm rõ 40 trang là mức tối thiểu tham khảo, không phải giới hạn trên; độ dài hợp lý là được. Bìa, các trang đầu và phụ lục không tính.
2. **Tuân thủ hoàn toàn** mẫu và quy định trong thư mục `~/Downloads/drive-download-20261114T075932Z-1-001/` (mục 4).
3. Nội dung **viết mới hoàn toàn**, dựa trên chính dự án onejack. Mọi kiến thức lấy từ nguồn ngoài đều có trích dẫn. Mục tiêu là không trùng văn bản với tài liệu khác (phần đạo văn của Turnitin).
4. Mọi con số trong báo cáo đều lấy từ **lần chạy thật** đã lưu trong repo (mục 6).
5. Thông tin cá nhân để chỗ trống trong ngoặc vuông cho người dùng tự điền: `[Họ tên]`, `[MSSV]`, `[Lớp]`, `[Ngành]`, `[Khóa]`, `[Tên giáo viên hướng dẫn]`, `[Học vị]`, `[Năm]`.

**Không làm**

- Không cam kết về kết quả của bất kỳ công cụ phát hiện AI nào, và không dùng mẹo kỹ thuật để đánh lừa công cụ. Người dùng muốn **văn phong tự nhiên như người viết**, đây là yêu cầu về chất lượng viết (mục 5a). Bản do Claude viết là bản nháp, người dùng sẽ đọc và sửa lại theo giọng của mình. Việc khai báo dùng AI là do người dùng quyết định theo quy định của trường.
- Không làm slide thuyết trình hay poster.

**Tuyệt đối tránh** (dù file vẫn mở được bình thường, gặp một trong các lỗi này là coi như hỏng)

- Bịa số liệu, bịa kết quả, hoặc bịa tài liệu tham khảo không tồn tại.
- Chép nguyên văn từ tài liệu khác mà không trích dẫn.
- Lệch mẫu: sai font hoặc cỡ chữ, sai lề, mục lục không cập nhật được, nhãn hình hoặc bảng không tự đánh số.
- Mô tả tính năng mà code không có, hoặc mô tả sai cách code chạy.

## 3. Cách làm đã chọn

| Cách | Đánh giá |
|---|---|
| **A. Viết vào chính file mẫu `MauTrinhBayDoAn.docx`** (giải nén, thay phần nội dung trong `word/document.xml`, giữ nguyên style, header/footer, trang bìa, trường mục lục) | **Người dùng đã chọn.** Giữ đúng style của Khoa: Heading 1 tự đánh "CHƯƠNG n", Heading 2/3 tự đánh số, style Caption, mục lục và danh mục hình/bảng tự cập nhật. |
| B. Tạo file Word mới bằng script docx-js, chép lại định dạng | Bỏ: style tự tạo dễ lệch mẫu. |
| C. Viết Markdown rồi chuyển sang Word, dùng file mẫu làm khuôn | Bỏ: nhãn hình/bảng đánh số theo chương và các trang bìa không chuyển chuẩn. Máy cũng chưa cài pandoc. |

## 4. Ràng buộc về hình thức

Lấy từ `2. Yeu cau trinh bay ...docx`, `3. MAU BAO CAO KLTN-BT HOC PHAN.doc` và `MauTrinhBayDoAn.docx`.

- **Khổ giấy và lề:** A4. Lề trên 3cm, dưới 3cm, trái 3,5cm, phải 2cm. File mẫu đã đặt đúng (1701/1701/1985/1134 twip), giữ nguyên.
- **Chữ:** Times New Roman cỡ 13, mật độ bình thường. File mẫu có font mặc định Times New Roman, style Normal cỡ 13.
- **Giãn dòng 1,5:** văn bản quy định yêu cầu 1,5 dòng, nhưng style Normal của file mẫu đang là `line=312` (1,3 dòng). **Quyết định của Claude:** theo văn bản quy định, sửa Normal thành `line=360` (1,5 dòng). Lý do: văn bản quy định là nguồn chính thức, file mẫu chỉ là ví dụ.
- **Thứ tự các phần** (tất cả trong một file Word):
  1. Bìa tiếng Việt: trang bìa có logo đã có trong file mẫu.
  2. Bìa tiếng Anh: tên trường và tên khoa cỡ 12 in đậm viết hoa; tên sinh viên cỡ 14 in đậm viết hoa; tên đề tài cỡ 18 in đậm viết hoa; ngành cỡ 14; GVHD cỡ 14 in đậm căn trái; nơi và năm cỡ 12. Tất cả căn giữa trừ dòng GVHD.
  3. Tóm tắt tiếng Anh, gói trong 1 trang A4, cỡ 13: Title; Abstract gồm Reason for writing, Problem, Methods, Results, Conclusion.
  4. Lời cảm ơn.
  5. Nhận xét của GVHD (trang để trống có dòng kẻ).
  6. Nhận xét của giáo viên phản biện (trang để trống có dòng kẻ).
  7. Mục lục (chỉ tới cấp 3).
  8. Danh mục hình.
  9. Danh mục bảng.
  10. Danh mục từ viết tắt, xếp theo A, B, C. Bắt buộc vì báo cáo có hơn 10 từ viết tắt.
  11. Lời mở đầu.
  12. Chương 1 tới Chương 5.
  13. Tài liệu tham khảo.
  14. Phụ lục, gồm cả *Kế hoạch thực hiện* và *Nhật ký làm việc* như mẫu yêu cầu.
- **Số trang:** góc dưới bên phải, **trang 1 bắt đầu từ Lời mở đầu**. Các trang trước đó không đánh số hoặc đánh số La Mã. **Phụ lục không đánh số trang.** Cần tách thành các section riêng.
- **Header:** thông tin khóa luận, ví dụ "Khóa luận tốt nghiệp chuyên ngành [Ngành]". **Footer:** thông tin sinh viên, gồm `[Họ tên]` và `[Lớp]`. Thay các ô tô vàng của file mẫu bằng chỗ trống ngoặc vuông, bỏ tô vàng.
- **Đánh số mục:** tối đa 4 cấp, số đầu là số chương. **Mỗi mục có ít nhất 2 tiểu mục**, áp dụng cho mọi Heading 2 có Heading 3 bên dưới.
- **Hình, bảng, công thức:**
  - Đánh số theo chương (Hình 3.2, Bảng 4.1).
  - Tên bảng đặt **trên** bảng, căn giữa. Tên hình đặt **dưới** hình, căn giữa. Cỡ chữ bằng cỡ chữ văn bản.
  - Số công thức đặt trong ngoặc đơn, căn phải.
  - Dùng style `Caption` và trường SEQ (STYLEREF chương + SEQ) như file mẫu, để danh mục hình/bảng tự cập nhật.
- **Viết tắt:** viết đầy đủ ở lần đầu, chữ viết tắt để trong ngoặc đơn.
- **Tài liệu tham khảo:**
  - Nhóm theo ngôn ngữ: tiếng Việt trước, tiếng Anh sau.
  - Trong mỗi nhóm, tác giả nước ngoài xếp theo họ; tác giả Việt xếp theo tên; tài liệu không có tác giả xếp theo tên cơ quan.
  - Ghi đúng định dạng quy định cho bài báo, sách và trang web.
  - Dòng thứ hai trở đi thụt vào 1cm.
- **Style:** chỉ dùng style có sẵn của file mẫu (Normal, Heading1–3, Caption, TOC1–3, TableofFigures, Tailieuthamkhao/RefList, ListParagraph, TableGrid). Hạn chế định dạng thủ công.

## 5. Dàn ý và phân bổ trang (~37 trang nội dung)

Lời văn: tiếng Việt học thuật, rõ ràng. **Khóa luận cá nhân (1 sinh viên)**, xưng "em" ở Lời mở đầu, Lời cảm ơn và Kết luận; các chương kỹ thuật viết khách quan ("đề tài", "hệ thống"). Bìa và footer chỉ có một bộ `[Họ tên]`, `[MSSV]`, `[Lớp]`. Mỗi khái niệm gắn với cách đề tài dùng nó.

### 5a. Văn phong

- **Cụ thể, bám dự án:** dùng số liệu, tên file, cấu hình thật, và các khó khăn thật đã gặp khi làm. Ví dụ:
  - Trên Alpine, `pkill -x` không khớp tên tiến trình nên lượt demo bị treo; đã đổi sang `killall`.
  - Đồng hồ các node lệch nhau nên phải đóng dấu giờ lại bằng đồng hồ máy EVE.
  - Đoán sai định dạng MAC của EVE làm 6 node trùng một IP.
  - Cảnh báo đi ngược chiều với lưu lượng tấn công nên lượt inband gần bằng lượt on.
- **Tránh văn rập khuôn:**
  - Không mở bằng câu sáo kiểu "Trong thời đại công nghệ số...".
  - Không kết đoạn bằng câu tổng kết lặp lại ý.
  - Không ép mọi danh sách thành 3 ý.
  - Không lạm dụng từ nối như "Bên cạnh đó", "Ngoài ra", "Tóm lại".
  - Câu dài ngắn xen kẽ, ưu tiên đoạn văn liền mạch hơn gạch đầu dòng ở các phần lập luận.
- **Giọng sinh viên:** Lời mở đầu, Lời cảm ơn và Kết luận xưng "em", có tự nhận xét về quá trình làm và điều rút ra. Các chương kỹ thuật viết khách quan, đi thẳng vào vấn đề.
- **Chỉ đưa thuật ngữ khi dùng tới,** giải thích bằng ví dụ trong chính demo.

### Lời mở đầu (~2 trang)

1. **Tổng quan tình hình nghiên cứu.**
   - Thế giới: DoS/DDoS là mối đe dọa phổ biến; các cơ chế lọc hợp tác đã có như RTBH (RFC 5635), BGP FlowSpec (RFC 8955), lọc theo cổng vào BCP 38 (RFC 2827).
   - Trong nước: viết chung chung, không bịa công trình cụ thể; để `[bổ sung đề tài liên quan của khóa trước nếu có]`.
2. **Ý nghĩa khoa học và thực tiễn.**

### Chương 1: Giới thiệu (~3 trang)

- **1.1 Tổng quan:** bài toán; vì sao chặn gần nạn nhân là chưa đủ.
- **1.2 Mục tiêu đề tài:** Bảng 1.1 liệt kê mục tiêu đo được: RTT của client, lưu lượng link R1→R2, thời gian từ lúc phát hiện tới lúc chặn, không chặn nhầm client.
- **1.3 Phạm vi đề tài:** một attacker, UDP flood, mô hình 6 node, EVE-NG; ngoài phạm vi: IP giả mạo, DDoS nhiều nguồn, xác thực cảnh báo.
- **1.4 Mô tả yêu cầu chức năng:** server, client, attacker, guard; ba lượt demo off/on/inband.

### Chương 2: Cơ sở lý thuyết (~9 trang)

Mỗi mục có ít nhất 2 tiểu mục:

- **2.1 Truyền thông mạng và giao thức UDP:** mô hình TCP/IP; UDP và lập trình socket (`socket`, `bind`, `sendto`, `recvfrom`, `poll`).
- **2.2 Hiệu năng mạng:** băng thông, thông lượng, RTT, mất gói; hàng đợi và nút cổ chai, token bucket (`tc tbf`).
- **2.3 Tấn công từ chối dịch vụ:** DoS/DDoS, UDP flood; phát hiện theo ngưỡng tần suất.
- **2.4 Lọc gói trên Linux:** Netfilter/iptables, chain riêng; raw socket `AF_PACKET`.
- **2.5 Phòng thủ cộng tác:** chặn gần nạn nhân và chặn ở đầu nguồn; RTBH, BGP FlowSpec; kênh điều khiển out-of-band và in-band.
- **2.6 Chất lượng dịch vụ (QoS):** DSCP và EF (RFC 2474, RFC 3246); hàng đợi ưu tiên (`tc prio`), trust boundary.
- **2.7 Môi trường giả lập:** KVM/QEMU, ảo hóa lồng nhau; EVE-NG Community; network namespace.

Hình gợi ý: Hình 2.1 (mô hình TCP/IP), Hình 2.2 (hàng đợi tại nút cổ chai), Hình 2.3 (chặn gần nạn nhân và chặn ở đầu nguồn), Hình 2.4 (hàng đợi 2 làn ưu tiên).

### Chương 3: Phân tích (~5 trang)

- **3.1 Phân tích bài toán:** kịch bản tấn công và ảnh hưởng tới người dùng thật; vì sao router gần server phát hiện được còn router cửa vào thì không.
- **3.2 Các phương án:** Bảng 3.1 so sánh 3 phương án (chặn tại R3 / hợp tác qua mạng điều khiển riêng / hợp tác chung đường + QoS) theo các tiêu chí: hiệu quả, độ phức tạp, tính thực tế.
- **3.3 Yêu cầu hệ thống:** chức năng; phi chức năng (thời gian phản ứng dưới 1 giây, không chặn nhầm, dọn sạch rule khi thoát, an toàn khi gọi iptables).
- **3.4 Luồng xử lý:** Hình 3.1, sơ đồ trình tự phát hiện → chặn → gửi cảnh báo → R1/R2 chặn.

### Chương 4: Thiết kế và hiện thực (~14 trang)

- **4.1 Kiến trúc tổng thể:**
  - Hình 4.1: sơ đồ mạng.
  - Bảng 4.1: địa chỉ IP và vai trò từng node.
  - Ba tầng: chương trình C, cấu hình lab, script điều khiển.
- **4.2 Thiết kế giao thức:**
  - Gói truy vấn `Q/A <seq> <ts>`, cách client tính RTT bằng đồng hồ của chính nó.
  - Gói cảnh báo `BLOCK <ip> <node>`, kiểm tra đầu vào.
  - Bảng 4.2: các cổng và định dạng gói.
- **4.3 Hiện thực các chương trình:**
  - server, client (module `stats`), attacker.
  - guard: Hình 4.2, lưu đồ vòng lặp `poll()`; các module `ratecount`, `blocklist`, `alert`, `firewall`; đoạn code ngắn minh họa, mỗi đoạn dưới 15 dòng.
  - Cờ dòng lệnh: Bảng 4.3.
- **4.4 Cấu hình mạng và QoS:** route và `ip_forward`; nút cổ chai 10 Mbit/s có 2 làn (`tbf` + `prio` + bộ lọc `u32` theo DSCP); cờ `-Q`.
- **4.5 Dựng môi trường thử nghiệm:**
  - Cài EVE-NG trên KVM.
  - Tạo image Alpine tự động; tạo lab qua REST API; IP quản lý tự đặt theo MAC.
  - Hình 4.3: ảnh chụp giao diện EVE-NG với lab `collab-defense`. Người dùng tự chụp; tạm để khung `[Ảnh chụp giao diện EVE-NG]`.
- **4.6 Kiểm thử và kết quả:**
  - Unit test: Bảng 4.4.
  - Kịch bản 3 lượt và màn hình tmux: Hình 4.4, ảnh vẽ lại từ nội dung chụp được của các ô tmux.
  - Kết quả: Bảng 4.5; Hình 4.5 `rtt.png`; Hình 4.6 `link.png`.
  - Kiểm chứng QoS: Bảng 4.6.
  - Đánh giá so với mục tiêu ở Bảng 1.1.

### Chương 5: Kết luận (~3 trang)

- **5.1 Kết quả đạt được:** đối chiếu từng mục tiêu.
- **5.2 Hạn chế của đề tài:** 7 hạn chế đã ghi trong README mục 8.
- **5.3 Hướng phát triển:** xác thực cảnh báo bằng HMAC, trust boundary, tự gỡ chặn (TTL), nhiều attacker, lan truyền cảnh báo theo đường đi, thử nghiệm FlowSpec thật.

### Tài liệu tham khảo (~1 trang)

Chỉ dùng nguồn có thật và kiểm chứng được:

| Nhóm | Nguồn |
|---|---|
| Sách | Kurose J. F., Ross K. W. (2021), *Computer Networking: A Top-Down Approach*, 8th ed., Pearson. |
| Bài báo | Mirkovic J., Reiher P. (2004), "A taxonomy of DDoS attack and DDoS defense mechanisms", *ACM SIGCOMM Computer Communication Review* 34 (2), pp. 39-53. |
| RFC | 768 (UDP), 2474 (DS field), 3246 (EF PHB), 2827 (BCP 38), 4732 (Internet DoS considerations), 5635 (RTBH), 8955 (FlowSpec) |
| Trang web | Trang man của Linux: `packet(7)`, `tc-tbf(8)`, `tc-prio(8)`, `iptables(8)`; tài liệu EVE-NG; Alpine Linux |

Nhóm tài liệu tiếng Việt: để `[bổ sung tài liệu tiếng Việt nếu GVHD yêu cầu]`, **không bịa**.

### Phụ lục (không đánh số trang, ~4 trang)

- Hướng dẫn chạy demo (rút gọn từ README).
- Mã nguồn guard: các phần chính.
- **Kế hoạch thực hiện:** bảng các mốc thời gian.
- **Nhật ký làm việc:** lấy mốc thật từ `git log` (11/11 tới 14/11/2026); các tuần sau để trống `[...]`.

## 6. Nguồn số liệu (bắt buộc dùng đúng)

Báo cáo chỉ dùng **một bộ số liệu nhất quán**: thư mục `results/eve-v2-report/`, đo ngày 14/11/2026 trên EVE-NG với code nhánh `v2`. Mỗi con số trong báo cáo phải tra ngược được về một file trong thư mục này. **Quyết định của Claude**, sau câu hỏi của người review: các bộ cũ (`results/eve/`, `results/eve-v2/`, `results/netns/`) không dùng, vì ảnh tmux và bảng số phải cùng một lần chạy.

**Kết quả 3 lượt** (`plot.sh results/eve-v2-report`; trung bình từ giây 16 tới 60):

| Lượt | RTT | Lưu lượng link R1→R2 | R3 phát hiện sau khi bắt đầu tấn công | R1 chặn sau khi R3 phát hiện |
|---|---|---|---|---|
| off | **407,97 ms** | **10,02 Mbit/s** | 0,566 s | (không chặn) |
| on | **6,29 ms** | **0,17 Mbit/s** | 0,495 s | 0,007 s |
| inband | **6,91 ms** | **0,19 Mbit/s** | 0,577 s | 0,004 s |

Mất gói: 0% ở cả 3 lượt.

**Kiểm chứng QoS:**

| File | Truy vấn thường | Truy vấn ưu tiên | Chi tiết khác |
|---|---|---|---|
| `qos-check-eve.txt` (EVE) | **401,94 ms** | **3,07 ms** | Bộ đếm `tc` trên R1 eth2: làn ưu tiên 100 gói, không mất gói; làn thường mất 55.965 gói |
| `qos-check-netns.txt` (mini-lab, chạy trong máy ảo EVE) | **399,85 ms** | **0,07 ms** | |

**Ảnh màn hình demo:** `tmux/<lượt>_pane<0..3>.txt` là nội dung thật của 4 ô tmux, chụp bằng `tmux capture-pane` lúc chạy 3 lượt trên.
- Hình 4.4 vẽ lại từ các file này thành ảnh. Chỉ tái hiện đúng chữ đã chụp, không thêm bớt.
- Hình 4.5 và 4.6 dùng `rtt.png` và `link.png` vẽ từ chính bộ này.

**Thông số demo:** 60 giây, tấn công từ giây 15, client 20 gói/s, attacker 5000 gói/s × 1000 byte, ngưỡng 200 gói/s, nút cổ chai 10 Mbit/s, mỗi làn hàng đợi 500KB.

**Code:** mô tả code phải khớp mã nguồn trên nhánh `v2`.

## 7. Phần để người xây dựng tự quyết

- Kỹ thuật tạo XML: tự viết script sinh `document.xml` từ một bản nguồn có cấu trúc (khuyến nghị lưu nguồn nội dung và script trong `report/` của repo để sinh lại được).
- Cách vẽ sơ đồ: PIL, hoặc SVG chuyển sang PNG bằng ImageMagick. Máy không có graphviz hay matplotlib.
- Có cập nhật sẵn mục lục và danh mục khi xuất file hay không. Nếu không làm được, ghi rõ hướng dẫn "Update Field" cho người dùng.
- Cách kiểm tra số trang: xuất PDF bằng LibreOffice rồi đếm trang từ Lời mở đầu tới hết Tài liệu tham khảo.
- Tên file đầu ra, ví dụ `report/BaoCao_KLTN_onejack.docx`.

## 8. Quyết định của Claude về lưu trữ

- Nguồn nội dung, script sinh file và file `.docx` đầu ra đều commit vào nhánh `v2`, thư mục `report/`.
- File PDF và ảnh xem thử (dùng để kiểm tra số trang) không commit, thêm vào `.gitignore`.
- Nhật ký làm việc trong phụ lục lấy mốc từ `git log`, tính tới thời điểm sinh báo cáo.
