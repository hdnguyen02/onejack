# KẾT LUẬN

## Kết quả đạt được

Đề tài đã xây dựng hoàn chỉnh một hệ thống thử nghiệm gồm bốn chương trình C, một mô hình sáu node chạy trên EVE-NG và bộ script để dựng lab, chạy thử và đo đạc. Bảng dưới đối chiếu kết quả đo với các mục tiêu đặt ra ở Chương 1.

Bảng: Đối chiếu kết quả với mục tiêu
| Nhóm | STT | Tiêu chí (Bảng 1.1) | Kết quả đo được | Đánh giá |
|---|---|---|---|---|
| Phát hiện và ngăn chặn | 1 | Phát hiện không quá 2 giây | {{detect_off}} giây (off), {{detect_on}} giây (on), {{detect_inband}} giây (inband) | Đạt |
| | 2 | Lan truyền tới R1 dưới 100 mili giây | {{block_on_ms}} ms (on), {{block_inband_ms}} ms (inband) | Đạt |
| | 3 | Chỉ attacker bị chặn | Trên R1, R2, R3 chỉ có địa chỉ 10.0.1.10 của attacker bị chặn | Đạt |
| Cải thiện hiệu năng | 4 | Thông lượng R1 → R2 giảm ít nhất 90% | Giảm {{link_drop_on}}% (on), {{link_drop_inband}}% (inband) | Đạt |
| | 5 | RTT của client giảm ít nhất 90% | Giảm {{rtt_drop_on}}% (on), {{rtt_drop_inband}}% (inband) | Đạt |
| | 6 | Cảnh báo đi chung đường đạt tiêu chí 2, 4, 5 | Đạt cả ba tiêu chí; qua đường đang nghẽn, gói ưu tiên chỉ mất {{qos_prio_eve}} ms | Đạt |

Kết quả quan trọng nhất là sự chênh lệch giữa lượt off và hai lượt có hợp tác. Cả ba lượt đều bảo vệ được server, nhưng chỉ khi các router chia sẻ quyết định chặn thì đường truyền mới được giải phóng và người dùng hợp lệ mới không còn bị ảnh hưởng. Thông tin cần chia sẻ chỉ là một gói tin vài chục byte, và việc này diễn ra trong vài mili giây.

Về bản thân, đề tài giúp em vận dụng và đào sâu kiến thức mạng máy tính đã học vào một hệ thống cụ thể: đọc trực tiếp tiêu đề IP trong chương trình C, cấu hình hàng đợi bằng `tc`, dựng mô hình nhiều node trên máy ảo lồng nhau. Phần đòi hỏi nhiều công sức nhất không phải là viết chương trình, mà là làm cho môi trường thử nghiệm chạy ổn định và đo cho đúng. Những lỗi nêu ở mục 4.6.4 đều chỉ xuất hiện khi chạy trên môi trường thật, và em rút ra rằng một kết quả đo chỉ đáng tin khi chạy lại được nhiều lần.

## Hạn chế của đề tài

1. **Cảnh báo chưa được xác thực.** Bất kỳ ai gửi được một gói `BLOCK <địa chỉ>` tới cổng 9999 của router đều có thể khiến mạng chặn một địa chỉ vô tội. Whitelist chỉ bảo vệ được một số địa chỉ cố định.
2. **Không chống được địa chỉ nguồn giả mạo.** Phát hiện và chặn đều dựa trên địa chỉ nguồn. Kẻ tấn công thay đổi địa chỉ liên tục thì mỗi địa chỉ chỉ gửi ít gói, không vượt ngưỡng và không bị chặn.
3. **Chỉ có một kẻ tấn công.** Tấn công DDoS thật đến từ hàng nghìn máy, mỗi máy có thể gửi dưới ngưỡng.
4. **Chặn vĩnh viễn.** Một địa chỉ đã bị chặn sẽ bị chặn tới khi guard dừng. Chưa có cơ chế tự gỡ chặn sau một khoảng thời gian.
5. **Gửi cảnh báo tới mọi router.** Danh sách router nhận cảnh báo được cấu hình thủ công. Với mạng lớn cần cách lan truyền theo đường đi thực tế của gói tấn công.
6. **Mạng điều khiển của lượt on là một switch chung.** Ngoài thực tế các router ở xa nhau. Lượt inband đã cho thấy một cách không cần switch chung, nhưng chưa thử với các phương án khác như VPN.
7. **QoS tin vào dấu ưu tiên do người gửi đặt.** Kẻ tấn công tự đánh dấu gói tấn công là EF thì sẽ được đưa vào làn ưu tiên, vì hệ thống thử nghiệm chưa có ranh giới tin cậy ở router đầu vào.

Ngoài ra, mọi số liệu đều đo trong một phòng thí nghiệm ảo trên một laptop, với các đường truyền được giới hạn nhân tạo. Các con số tuyệt đối sẽ khác trên mạng thật, dù xu hướng so sánh giữa các phương án vẫn có giá trị.

## Hướng phát triển

- **Xác thực cảnh báo** bằng HMAC: các router dùng chung một khóa bí mật, mỗi cảnh báo kèm chữ ký và thời điểm gửi để chống phát lại. Router chỉ chặn khi chữ ký hợp lệ.
- **Thêm ranh giới tin cậy** cho QoS: router đầu vào xóa dấu DSCP trên mọi gói đến từ mạng ngoài, chỉ gói do chính các router sinh ra mới được mang dấu EF.
- **Tự gỡ chặn** sau một khoảng thời gian (TTL), rồi chặn lại nếu tấn công vẫn tiếp diễn, để không chặn nhầm vĩnh viễn một địa chỉ đã được trả lại cho người dùng khác.
- **Mở rộng mô hình** lên nhiều attacker và nhiều nhánh mạng, kết hợp lọc theo cổng vào kiểu BCP 38 [[REF:2]] để hạn chế giả mạo địa chỉ.
- **Thử nghiệm với giao thức thật**: thay thông điệp `BLOCK` tự định nghĩa bằng quy tắc lọc BGP FlowSpec [[REF:6]] trên phần mềm định tuyến, để so sánh độ trễ lan truyền và mức độ phức tạp khi triển khai.
