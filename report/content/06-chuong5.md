# KẾT LUẬN

## Kết quả đạt được

Đề tài đã xây dựng hoàn chỉnh một hệ thống demo gồm bốn chương trình C, một mô hình sáu node chạy trên EVE-NG và bộ script để dựng lab, chạy thử và đo đạc. Bảng dưới đối chiếu kết quả đo với các mục tiêu đặt ra ở Chương 1.

Bảng: Đối chiếu kết quả với mục tiêu
| STT | Mục tiêu | Kết quả đo được | Đánh giá |
|---|---|---|---|
| 1 | Phát hiện kẻ tấn công nhanh | R3 chặn chưa tới một giây sau khi tấn công: {{detect_off}} giây (off), {{detect_on}} giây (on), {{detect_inband}} giây (inband) | Đạt |
| 2 | Chặn được ở cửa vào nhờ hợp tác | R1 chặn sau {{block_on_ms}} ms (on) và {{block_inband_ms}} ms (inband) kể từ lúc R3 phát hiện | Đạt |
| 3 | Giải phóng đường truyền | Link R1 → R2 giảm từ {{link_off}} Mbit/s xuống {{link_on}} Mbit/s | Đạt |
| 4 | Người dùng thật trở lại bình thường | RTT trung bình giảm từ {{rtt_off}} ms xuống {{rtt_on}} ms, sau một giây về khoảng {{rtt_base}} ms | Đạt |
| 5 | Không chặn nhầm | Chỉ địa chỉ của attacker bị chặn; client không mất gói ở cả ba lượt | Đạt |
| 6 | Cảnh báo vẫn tới khi đi chung đường | Lượt inband cho RTT {{rtt_inband}} ms, gần bằng lượt on; truy vấn ưu tiên qua đường nghẽn chỉ mất {{qos_prio_eve}} ms | Đạt |
| 7 | Chạy lại được | Lab dựng lại bằng script, kiểm tra cả sau khi khởi động lại máy ảo EVE-NG | Đạt |

Kết quả quan trọng nhất là sự chênh lệch giữa lượt off và hai lượt có hợp tác. Cả ba lượt đều bảo vệ được server, nhưng chỉ khi các router chia sẻ quyết định chặn thì đường truyền mới được giải phóng và người dùng thật mới không còn bị ảnh hưởng. Thông tin cần chia sẻ chỉ là một gói tin vài chục byte, và việc này diễn ra trong vài mili giây.

Về bản thân, đây là lần đầu em làm việc ở tầng thấp của mạng: đọc từng byte của tiêu đề IP, cấu hình hàng đợi bằng `tc`, dựng máy ảo lồng trong máy ảo. Phần tốn thời gian nhất không phải là viết chương trình C, mà là làm cho môi trường thử nghiệm chạy ổn định và đo cho đúng. Những lỗi nêu ở mục 4.6.4 đều chỉ lộ ra khi chạy trên môi trường thật, và em rút ra rằng một kết quả đo chỉ đáng tin khi chạy lại được nhiều lần.

## Hạn chế của đề tài

1. **Cảnh báo chưa được xác thực.** Bất kỳ ai gửi được một gói `BLOCK <địa chỉ>` tới cổng 9999 của router đều có thể khiến mạng chặn một địa chỉ vô tội. Whitelist chỉ bảo vệ được một số địa chỉ cố định.
2. **Không chống được địa chỉ nguồn giả mạo.** Phát hiện và chặn đều dựa trên địa chỉ nguồn. Kẻ tấn công thay đổi địa chỉ liên tục thì mỗi địa chỉ chỉ gửi ít gói, không vượt ngưỡng và không bị chặn.
3. **Chỉ có một kẻ tấn công.** Tấn công DDoS thật đến từ hàng nghìn máy, mỗi máy có thể gửi dưới ngưỡng.
4. **Chặn vĩnh viễn.** Một địa chỉ đã bị chặn sẽ bị chặn tới khi guard dừng. Chưa có cơ chế tự gỡ chặn sau một khoảng thời gian.
5. **Gửi cảnh báo tới mọi peer.** Danh sách peer cấu hình tay. Với mạng lớn cần cách lan truyền theo đường đi thực tế của gói tấn công.
6. **Mạng điều khiển của lượt on là một switch chung.** Ngoài thực tế các router ở xa nhau. Lượt inband đã cho thấy một cách không cần switch chung, nhưng chưa thử với các phương án khác như VPN.
7. **QoS tin vào dấu ưu tiên do người gửi đặt.** Kẻ tấn công tự đánh dấu gói rác là EF thì sẽ chen được vào làn ưu tiên, vì demo chưa có ranh giới tin cậy ở router cửa vào.

Ngoài ra, mọi số liệu đều đo trong một phòng thí nghiệm ảo trên một laptop, với các đường truyền được giới hạn nhân tạo. Các con số tuyệt đối sẽ khác trên mạng thật, dù xu hướng so sánh giữa các phương án vẫn có giá trị.

## Hướng phát triển

- **Xác thực cảnh báo** bằng HMAC: các router dùng chung một khóa bí mật, mỗi cảnh báo kèm chữ ký và thời điểm gửi để chống phát lại. Router chỉ chặn khi chữ ký hợp lệ.
- **Thêm ranh giới tin cậy** cho QoS: router cửa vào xóa dấu DSCP trên mọi gói đến từ mạng ngoài, chỉ gói do chính các router sinh ra mới được mang dấu EF.
- **Tự gỡ chặn** sau một khoảng thời gian (TTL), rồi chặn lại nếu tấn công vẫn tiếp diễn, để không chặn nhầm vĩnh viễn một địa chỉ đã được trả lại cho người dùng khác.
- **Mở rộng mô hình** lên nhiều attacker và nhiều nhánh mạng, kết hợp lọc theo cổng vào kiểu BCP 38 [[REF:2]] để hạn chế giả mạo địa chỉ.
- **Thử nghiệm với giao thức thật**: thay thông điệp `BLOCK` tự định nghĩa bằng luật BGP FlowSpec [[REF:6]] trên phần mềm định tuyến, để so sánh độ trễ lan truyền và mức độ phức tạp khi triển khai.
