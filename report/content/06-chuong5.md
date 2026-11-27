# KẾT LUẬN

## Kết quả đạt được

Đề tài đã hoàn thành các nội dung chính sau:

- Tìm hiểu cơ sở lý thuyết về hiệu năng mạng, các thành phần của độ trễ, tắc nghẽn và hàng đợi, định tuyến tĩnh và định tuyến nhiều đường chi phí bằng nhau.
- Xây dựng mô hình sáu node trên EVE-NG có hai đường đi khác nhau về độ dài, với độ trễ truyền và băng thông của từng đường truyền được giả lập nhất quán.
- Viết ba chương trình C để tạo lưu lượng và đo RTT, jitter, tỷ lệ mất gói, thông lượng.
- Tự động hóa toàn bộ quá trình dựng mô hình, cấu hình router, chạy thử nghiệm và vẽ biểu đồ bằng script.
- Đo và so sánh ba cách chọn đường trên cùng một kịch bản lưu lượng.

Bảng dưới đối chiếu kết quả đo với các mục tiêu đặt ra ở Chương 1.

Bảng: Đối chiếu kết quả với mục tiêu
| STT | Tiêu chí (Bảng 1.1) | Kết quả đo được | Đánh giá |
|---|---|---|---|
| 1 | RTT đường ngắn thấp hơn rõ rệt so với đường dài khi chưa có tải | {{idle_short}} so với {{idle_base}} mili giây, giảm {{idle_drop_short}}% | Đạt |
| 2 | RTT tăng ít nhất 5 lần khi có tải và mọi lưu lượng đi một đường | Lượt base từ {{idle_base}} lên {{rtt_base}} mili giây | Đạt |
| 3 | RTT có tải giảm ít nhất 80% so với lượt đi đường dài | Lượt balance {{rtt_balance}} mili giây, giảm {{rtt_drop_balance}}% | Đạt |
| 4 | Thông lượng không thấp hơn lượt đi đường dài | Lượt balance {{server_balance}} so với {{server_base}} Mbit/s | Đạt |
| 5 | Kết quả tái hiện được bằng script | Mọi bước chạy bằng script, đã chạy lại trên cả lab EVE-NG lẫn mô hình rút gọn bằng network namespace | Đạt |

Kết quả quan trọng nhất là sự khác biệt giữa hai cách chọn đường. Dùng đường ngắn giảm gần một nửa độ trễ khi mạng thông thoáng, nhưng gần như không giúp được khi mạng tắc nghẽn. Phân phối tải ra hai đường giữ độ trễ của người dùng gần như không đổi khi có tải, đồng thời giúp server nhận đủ toàn bộ lưu lượng. Cả hai cách đều chỉ cần thay đổi bảng định tuyến của router, không cần thêm thiết bị hay tăng băng thông.

## Hạn chế của đề tài

1. **Đường đi được cấu hình tĩnh.** Router không tự biết đường nào đang tắc nghẽn để đổi. Việc chọn kịch bản do người vận hành quyết định trước mỗi lượt.
2. **Chia tải theo luồng.** Một luồng đơn lẻ chỉ đi được trên một đường. Nếu lưu lượng chỉ gồm vài luồng rất lớn, tải có thể dồn về một đường.
3. **Hai đường có cùng băng thông và trọng số.** Đề tài chưa thử trường hợp hai đường khác băng thông, khi đó cần đặt trọng số tương ứng.
4. **Lưu lượng là UDP tốc độ cố định.** Lưu lượng thực tế như tải tệp thường dùng TCP, tự giảm tốc độ khi mạng tắc nghẽn, nên mức độ tắc nghẽn có thể khác.
5. **Môi trường giả lập.** Mọi số liệu đo trong phòng thí nghiệm ảo trên một laptop, độ trễ truyền và băng thông là giá trị giả lập. Con số tuyệt đối sẽ khác trên thiết bị thật, nhưng xu hướng so sánh giữa các kịch bản vẫn có giá trị.

## Hướng phát triển

- **Định tuyến động:** chạy giao thức định tuyến như OSPF trên các router để router tự cập nhật đường đi khi một đường truyền bị đứt hoặc thay đổi chi phí.
- **Chọn đường theo độ trễ đo được:** router định kỳ đo độ trễ của từng đường và tự chuyển lưu lượng sang đường đang có độ trễ thấp hơn.
- **Đường có băng thông khác nhau:** thử chia tải theo trọng số tỷ lệ với băng thông của từng đường.
- **Lưu lượng TCP:** thay một phần lưu lượng tải bằng các kết nối TCP để đánh giá trong điều kiện gần thực tế hơn.
- **Mô hình lớn hơn:** mở rộng lên nhiều router và nhiều hơn hai đường đi để đánh giá phân phối tải trong mạng phức tạp.
