# KẾT LUẬN

## Kết quả đạt được

Sau thời gian thực hiện, đề tài đã làm được các việc sau:

- Tìm hiểu lý thuyết về hiệu năng mạng, các thành phần của độ trễ, tắc nghẽn và hàng đợi, định tuyến tĩnh và định tuyến nhiều đường chi phí bằng nhau.
- Dựng mô hình sáu node trên EVE-NG có hai đường đi dài ngắn khác nhau, độ trễ truyền và băng thông của từng đường được giả lập giống nhau ở mọi lượt.
- Viết ba chương trình C để tạo lưu lượng và đo RTT, jitter, tỷ lệ mất gói, thông lượng.
- Viết script để tự động dựng mô hình, cấu hình router, chạy thử nghiệm và vẽ biểu đồ.
- Đo và so sánh ba cách chọn đường với cùng một lưu lượng.

Bảng dưới so kết quả đo với các mục tiêu đã đặt ra ở Chương 1.

Bảng: Đối chiếu kết quả với mục tiêu
| STT | Tiêu chí (Bảng 1.1) | Kết quả đo được | Đánh giá |
|---|---|---|---|
| 1 | RTT đường ngắn thấp hơn rõ rệt so với đường dài khi chưa có tải | {{idle_short}} so với {{idle_base}} mili giây, giảm {{idle_drop_short}}% | Đạt |
| 2 | RTT tăng ít nhất 5 lần khi có tải và mọi lưu lượng đi một đường | Lượt base từ {{idle_base}} lên {{rtt_base}} mili giây | Đạt |
| 3 | RTT có tải giảm ít nhất 80% so với lượt đi đường dài | Lượt balance {{rtt_balance}} mili giây, giảm {{rtt_drop_balance}}% | Đạt |
| 4 | Thông lượng không thấp hơn lượt đi đường dài | Lượt balance {{server_balance}} so với {{server_base}} Mbit/s | Đạt |
| 5 | Kết quả tái hiện được bằng script | Mọi bước chạy bằng script, đã chạy lại trên cả lab EVE-NG lẫn mô hình rút gọn bằng network namespace | Đạt |

Qua ba lượt đo có thể thấy, dùng đường ngắn giảm được gần một nửa độ trễ khi mạng rảnh nhưng hầu như không giúp gì khi mạng tắc nghẽn. Còn khi chia tải ra hai đường, độ trễ của người dùng gần như giữ nguyên dù có tải nặng, và server vẫn nhận đủ lưu lượng. Cả hai cách chỉ cần sửa bảng định tuyến trên router, không phải thêm thiết bị hay tăng băng thông.

## Hạn chế của đề tài

1. **Đường đi được cấu hình tĩnh.** Router không tự biết đường nào đang tắc để đổi. Cách chọn đường do người vận hành đặt trước mỗi lượt.
2. **Chia tải theo luồng.** Mỗi luồng chỉ đi được trên một đường. Nếu lưu lượng chỉ gồm vài luồng rất lớn thì tải vẫn có thể dồn về một đường.
3. **Hai đường có cùng băng thông và trọng số.** Đề tài chưa thử trường hợp hai đường có băng thông khác nhau, khi đó cần đặt trọng số cho phù hợp.
4. **Lưu lượng là UDP tốc độ cố định.** Ngoài thực tế, việc tải tệp thường dùng TCP, vốn tự giảm tốc khi mạng tắc nghẽn, nên mức tắc nghẽn có thể khác.
5. **Môi trường giả lập.** Số liệu được đo trong một phòng thí nghiệm ảo trên laptop, độ trễ truyền và băng thông đều là giá trị giả lập. Trên thiết bị thật các con số sẽ khác, nhưng xu hướng khi so sánh các kịch bản vẫn đúng.

## Hướng phát triển

- **Định tuyến động:** chạy giao thức định tuyến như OSPF để router tự cập nhật đường đi khi một đường truyền bị đứt hoặc đổi chi phí.
- **Chọn đường theo độ trễ đo được:** router định kỳ đo độ trễ của từng đường và tự chuyển lưu lượng sang đường đang nhanh hơn.
- **Đường có băng thông khác nhau:** thử chia tải theo trọng số tỷ lệ với băng thông của từng đường.
- **Lưu lượng TCP:** thay một phần lưu lượng tải bằng kết nối TCP để thử trong điều kiện gần thực tế hơn.
- **Mô hình lớn hơn:** thêm router và thêm đường đi để thử phân phối tải trong mạng phức tạp hơn.
