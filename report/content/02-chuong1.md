# GIỚI THIỆU

## Tổng quan

Đề tài được giao có tên "Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu", yêu cầu lập trình một ứng dụng demo bằng C trên Linux và chạy trong môi trường EVE-NG. Đề bài không kèm tài liệu tham khảo, nên việc đầu tiên là cụ thể hóa ba khái niệm: "truy vấn xấu" là gì, "hiệu năng mạng" đo bằng gì, và "cộng tác" diễn ra giữa những node nào.

Trong đề tài này, **truy vấn** là một gói UDP (User Datagram Protocol) mà client gửi tới server để hỏi và chờ trả lời, giống như một lần gọi API (Application Programming Interface) của một dịch vụ web. **Truy vấn xấu** là truy vấn được gửi ra không phải để dùng mà để làm nghẽn: một địa chỉ IP (Internet Protocol) gửi tới {{attack_rate}} gói mỗi giây, mỗi gói {{attack_size}} byte, trong khi người dùng bình thường chỉ gửi {{client_rate}} gói mỗi giây. **Hiệu năng mạng** được đo bằng hai đại lượng mà người dùng cảm nhận rõ nhất: thời gian khứ hồi (Round-Trip Time – RTT) của từng truy vấn, và lượng dữ liệu đang chạy trên đường truyền giữa các router.

Mô hình gồm sáu node nối thành một đường thẳng: attacker và client ở một đầu, server ở đầu kia, ba router R1, R2, R3 ở giữa. Hai đoạn R1–R2 và R2–R3 bị giới hạn {{bottleneck}} Mbit/s để tạo nút cổ chai. Khi attacker bắt đầu gửi rác, R3, router đứng sát server, là nơi thấy rõ nhất ai đang dồn truy vấn vào. Nếu R3 chỉ tự chặn, server được an toàn nhưng rác vẫn chạy đầy hai đoạn phía trước, và client đi chung đường vẫn bị chậm. Nếu R3 báo cho R1 để R1 chặn ngay ở cửa vào, toàn bộ đường truyền phía sau sẽ thông thoáng trở lại. Đó là ý tưởng "cộng tác" mà đề tài muốn chứng minh bằng số liệu.

## Mục tiêu đề tài

Mục tiêu chung là xây dựng một hệ thống demo cho thấy sự hợp tác giữa các router cải thiện hiệu năng mạng một cách đo được, so với cách chỉ chặn tại một điểm. Mục tiêu cụ thể được tóm tắt trong bảng dưới. Mỗi mục đều có cách đo rõ ràng để Chương 4 và Chương 5 đối chiếu lại.

Bảng: Các mục tiêu cụ thể và cách đánh giá
| STT | Mục tiêu | Cách đo, tiêu chí đạt |
|---|---|---|
| 1 | Phát hiện kẻ tấn công nhanh | Thời gian từ lúc bắt đầu tấn công tới lúc R3 chặn, dưới 1 giây |
| 2 | Chặn được ở cửa vào nhờ hợp tác | Thời gian từ lúc R3 phát hiện tới lúc R1 chặn, tính bằng mili giây |
| 3 | Giải phóng đường truyền | Lưu lượng trung bình trên link R1 → R2 sau khi bị tấn công giảm từ mức nghẽn về gần mức của riêng client |
| 4 | Người dùng thật trở lại bình thường | RTT trung bình của client sau khi bị tấn công giảm từ hàng trăm mili giây về vài mili giây |
| 5 | Không chặn nhầm | Client và server không bao giờ bị chặn; client không mất gói |
| 6 | Cảnh báo vẫn tới khi đi chung đường | Lượt dùng QoS cho kết quả tương đương lượt dùng mạng điều khiển riêng |
| 7 | Chạy lại được | Dựng lab và chạy demo bằng script, kết quả lặp lại được |

## Phạm vi đề tài

Đề tài nằm trong những giới hạn sau, được chọn để vừa với thời gian thực hiện và đủ rõ để đo:

- **Một kẻ tấn công, một địa chỉ IP thật**, tấn công kiểu UDP flood vào một cổng cố định. Đề tài không xử lý trường hợp địa chỉ nguồn bị giả mạo hoặc tấn công phân tán từ nhiều máy.
- **Phát hiện dựa trên ngưỡng tần suất**: đếm số gói của mỗi IP trong mỗi giây, vượt {{threshold}} gói/giây thì xem là tấn công. Đề tài không dùng học máy hay phân tích nội dung gói.
- **Ba router Linux** trên một đường thẳng, mỗi router chạy chương trình `guard`; chặn bằng iptables.
- **Cảnh báo chưa được xác thực.** Đây là hạn chế đã biết, được phân tích ở Chương 5.
- **Môi trường thử nghiệm** là EVE-NG Community Edition chạy trong máy ảo trên một laptop, các node dùng Alpine Linux. Ngoài ra có một bản thu nhỏ dùng network namespace để chạy nhanh và làm phương án dự phòng.

## Mô tả yêu cầu chức năng

Hệ thống gồm bốn chương trình C, mỗi chương trình đóng một vai trong kịch bản:

- **server** nhận truy vấn trên cổng UDP 9000 và trả lời ngay, đồng thời in số truy vấn nhận được mỗi giây theo từng IP nguồn.
- **client** đóng vai người dùng thật: gửi {{client_rate}} truy vấn mỗi giây có đánh số thứ tự, khớp từng câu trả lời để tính RTT và tỉ lệ mất gói, ghi kết quả mỗi giây ra tệp CSV (Comma-Separated Values).
- **attacker** gửi gói UDP liên tục với tốc độ cố định để làm nghẽn đường truyền.
- **guard** chạy trên router, có hai vai trò bật bằng tham số dòng lệnh: *phát hiện* (đếm gói, chặn kẻ vượt ngưỡng, gửi cảnh báo) và *nghe cảnh báo* (nhận cảnh báo và chặn theo).

Bên cạnh đó, hệ thống cần một bộ script để dựng mạng, chạy từng lượt demo {{duration}} giây, thu số liệu và vẽ biểu đồ. Ba lượt cần so sánh là:

- **off**: chỉ R3 tự phát hiện và tự chặn.
- **on**: R3 gửi cảnh báo cho R1, R2 qua mạng điều khiển riêng.
- **inband**: R3 gửi cảnh báo đi chung đường dữ liệu, gói cảnh báo được đánh dấu ưu tiên.
