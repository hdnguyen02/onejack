# GIỚI THIỆU

## Tổng quan

Đề tài "Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu" xây dựng một ứng dụng demo bằng C trên Linux, chạy trong môi trường giả lập mạng EVE-NG. Phần này nêu cách hiểu của đề tài về các khái niệm chính, mô hình thử nghiệm và ý tưởng giải quyết.

**Truy vấn** là một thông điệp ở tầng ứng dụng theo mô hình yêu cầu – phản hồi (request – response): client gửi một yêu cầu tới server và chờ server trả lời. Mỗi truy vấn được đóng gói trong một gói UDP (User Datagram Protocol) gửi tới cổng 9000 của server. Gói UDP chỉ là phương tiện vận chuyển ở tầng giao vận, còn nội dung truy vấn do chương trình của đề tài định nghĩa (mục 4.2.1). Trong phạm vi đề tài, chỉ những gói UDP tới cổng 9000 được xem là truy vấn.

**Truy vấn xấu** được xác định qua đặc điểm quan sát được, không dựa vào việc suy đoán ý đồ của người gửi: đó là các truy vấn đến từ một địa chỉ IP (Internet Protocol) nguồn với tần suất vượt một ngưỡng cho trước, và tổng lưu lượng của chúng vượt khả năng của đường truyền, làm giảm chất lượng dịch vụ của người dùng khác. Trong kịch bản thử nghiệm, máy tấn công được cấu hình gửi {{attack_rate}} gói/giây, mỗi gói {{attack_size}} byte, còn máy người dùng hợp lệ được cấu hình gửi {{client_rate}} truy vấn/giây. Đây là các thông số giả định, chọn sao cho lưu lượng tấn công vượt rõ băng thông của nút cổ chai còn lưu lượng hợp lệ thì rất nhỏ.

**Hiệu năng mạng** được đánh giá bằng hai nhóm chỉ số. Nhóm chỉ số **chất lượng dịch vụ** phản ánh trải nghiệm của người dùng hợp lệ, gồm thời gian khứ hồi (Round-Trip Time – RTT) và tỉ lệ mất gói của client. Nhóm chỉ số **sử dụng tài nguyên mạng** phản ánh mức chiếm dụng đường truyền, là thông lượng (throughput) đo được trên đường R1 → R2, tính bằng Mbit/s.

Mô hình thử nghiệm gồm sáu node. Client và attacker cùng nối vào mạng LAN1 qua cổng `eth1` của router R1. Ba router R1, R2, R3 nối nối tiếp nhau. Server nối vào cổng `eth2` của R3. Ngoài ra, ba router có chung một mạng điều khiển riêng. Sơ đồ chi tiết với địa chỉ và cổng của từng node được trình bày ở Hình 4.1 và Bảng 4.1.

Hai đoạn R1 – R2 và R2 – R3 được giới hạn băng thông {{bottleneck}} Mbit/s để tạo nút cổ chai có chủ đích. Đây là đoạn đường **chung** mà cả lưu lượng hợp lệ lẫn lưu lượng tấn công phải đi qua để tới server, tương tự đường trục giữa các mạng trong thực tế. Mức {{bottleneck}} Mbit/s lớn hơn rất nhiều so với lưu lượng của client nhưng chỉ bằng khoảng một phần tư lưu lượng tấn công, nên khi bị tấn công, đường truyền chắc chắn bị nghẽn.

R3 đóng vai trò **điểm giám sát lưu lượng đi tới server**: mọi gói từ LAN1 tới server đều phải đi vào cổng `eth1` của R3, nên chương trình trên R3 thống kê được số truy vấn theo từng địa chỉ IP nguồn. Việc chặn được thực hiện bằng tường lửa iptables có sẵn trong Linux: router thêm vào tường lửa một **quy tắc chặn** (rule) yêu cầu loại bỏ mọi gói có địa chỉ nguồn là địa chỉ cần chặn (chi tiết ở mục 2.4.1). Có hai cách xử lý khi R3 phát hiện một nguồn vượt ngưỡng:

- **Chặn tại phía đích:** R3 tự chặn nguồn đó. Server được bảo vệ, nhưng lưu lượng tấn công vẫn đi qua và chiếm băng thông của hai đoạn R1 – R2, R2 – R3 trước khi bị loại bỏ, nên client đi chung đường vẫn bị ảnh hưởng.
- **Chặn gần nguồn:** R3 gửi cảnh báo cho các router phía trước. R1 là router nơi lưu lượng tấn công đi vào mạng, nên khi R1 chặn, gói tấn công bị loại bỏ trước khi chiếm băng thông của các đoạn phía sau. R2 cũng nhận cảnh báo và chặn theo. Trong mô hình này, lưu lượng tấn công đã bị R1 loại bỏ trước nên việc chặn ở R2 chỉ mang tính dự phòng, mô phỏng việc cảnh báo được lan tới mọi router trên đường đi.

Vì client và attacker cùng nằm sau R1, việc chặn phải dựa trên địa chỉ IP nguồn để chỉ loại bỏ gói của attacker (10.0.1.10), còn gói của client (10.0.1.20) vẫn đi qua bình thường. Mục 4.6.2 kiểm chứng điều này bằng danh sách quy tắc chặn trên các router và số liệu của client.

## Mục tiêu đề tài

Mục tiêu chung là xây dựng hệ thống demo và đo được mức cải thiện hiệu năng mạng khi các router hợp tác chặn lưu lượng xấu, so với cách chỉ chặn tại phía đích. Các mục tiêu cụ thể gồm hai nhóm: mục tiêu 1–3 về phát hiện và ngăn chặn, mục tiêu 4–6 về cải thiện hiệu năng.

Bảng: Các mục tiêu cụ thể và tiêu chí đánh giá
| STT | Mục tiêu | Chỉ số đo | Tiêu chí đạt |
|---|---|---|---|
| 1 | Phát hiện nhanh | Thời gian từ lúc bắt đầu tấn công tới lúc R3 chặn | Không quá 2 giây |
| 2 | Báo cho router cửa vào chặn nhanh | Thời gian từ lúc R3 phát hiện tới lúc R1 chặn | Dưới 100 mili giây |
| 3 | Không chặn nhầm người dùng hợp lệ | Danh sách địa chỉ bị chặn trên ba router | Chỉ địa chỉ của attacker bị chặn; client và server không bị chặn |
| 4 | Giải phóng đường truyền | Thông lượng trung bình trên đường R1 → R2 | Giảm ít nhất 90% so với lượt chỉ chặn tại phía đích |
| 5 | Khôi phục chất lượng dịch vụ | RTT trung bình của client | Giảm ít nhất 90% so với lượt chỉ chặn tại phía đích |
| 6 | Cảnh báo đi chung đường vẫn hiệu quả | Thời gian chặn, thông lượng và RTT khi cảnh báo được gửi chung đường dữ liệu (có ưu tiên QoS) thay vì qua mạng điều khiển riêng | Đạt cùng tiêu chí như mục tiêu 2, 4 và 5 |

Mỗi lượt thử nghiệm kéo dài {{duration}} giây, kẻ tấn công bắt đầu gửi ở giây thứ {{attack_at}}. Thông lượng và RTT trung bình được tính từ lúc bị tấn công tới hết lượt. Các khoảng thời gian ở mục tiêu 1 và 2 được đo bằng dấu thời gian trong log mà các router và script điều khiển ghi lại khi sự kiện xảy ra: lúc tấn công bắt đầu, lúc R3 chặn, và lúc R1 chặn. Vì R1 chỉ ghi log sau khi đã chặn xong, thời gian ở mục tiêu 2 đã gồm cả thời gian truyền cảnh báo và thời gian R1 thực hiện việc chặn.

## Phạm vi đề tài

Đề tài nằm trong những giới hạn sau:

- **Một nguồn tấn công với địa chỉ IP nguồn hợp lệ, không giả mạo.** Tấn công kiểu UDP flood vào cổng 9000 của server. Đề tài không xử lý trường hợp địa chỉ nguồn bị giả mạo hoặc tấn công phân tán từ nhiều máy.
- **Phát hiện dựa trên ngưỡng tần suất.** Đếm số truy vấn của mỗi địa chỉ nguồn trong mỗi chu kỳ 1 giây, vượt {{threshold}} gói/giây thì xem là bất thường. Ngưỡng này được chọn cho môi trường thử nghiệm: gấp {{threshold}}/{{client_rate}} lần tần suất của client và nhỏ hơn nhiều so với tần suất tấn công, không phải ngưỡng chuẩn áp dụng cho mọi hệ thống. Đề tài không dùng học máy hay phân tích nội dung gói.
- **Ba router Linux, mỗi router chạy chương trình `guard` với vai trò riêng.** R3 phát hiện, chặn và gửi cảnh báo. R1 và R2 chỉ nhận cảnh báo và chặn theo. Lượt chỉ chặn tại phía đích chỉ chạy `guard` trên R3. Việc chặn dùng iptables.
- **Cảnh báo chưa được xác thực.** Router nhận chỉ kiểm tra định dạng và danh sách địa chỉ không được chặn. Một node bất kỳ gửi được cảnh báo giả tới router có thể khiến router chặn nhầm một địa chỉ hợp lệ. Hạn chế này được phân tích ở Chương 5.
- **Môi trường thử nghiệm** là EVE-NG Community Edition chạy trong máy ảo KVM trên một laptop. Các node dùng Alpine Linux {{alpine_version}} (kernel 6.6, bản `virt`), có iptables {{iptables_version}} chạy trên backend nf_tables và bộ công cụ `iproute2` (lệnh `ip`, `tc`). Ngoài ra có một bản thu nhỏ dùng network namespace trên Linux để kiểm thử nhanh và làm phương án dự phòng.

## Mô tả yêu cầu chức năng

### Các chương trình

Hệ thống gồm bốn chương trình C. Chi tiết hiện thực được trình bày ở mục 4.3.

- **server** nhận truy vấn trên cổng UDP 9000. Với mỗi truy vấn hợp lệ `Q <số thứ tự> <thời điểm>`, server trả lời ngay bằng `A <số thứ tự> <thời điểm>`, giữ nguyên số thứ tự và thời điểm. Mỗi giây server in số gói nhận được trên socket của nó, tách theo địa chỉ nguồn. Đây là thống kê ở tầng ứng dụng, chỉ gồm các gói thực sự tới được server.
- **client** gửi {{client_rate}} truy vấn/giây, số thứ tự tăng dần từ 1. Mỗi trả lời được đối chiếu với truy vấn cùng số thứ tự để tính RTT. Truy vấn quá 1 giây chưa có trả lời bị tính là mất. Mỗi giây client ghi một dòng vào tệp CSV (Comma-Separated Values) gồm các cột: giây thứ, số gói gửi, số gói nhận, tỉ lệ mất (%), RTT trung bình (ms).
- **attacker** gửi gói UDP tới cổng 9000 của server. Tốc độ (gói/giây), kích thước gói và thời gian chạy đều cấu hình qua tham số dòng lệnh. Mọi lượt thử nghiệm dùng cùng giá trị: {{attack_rate}} gói/giây, {{attack_size}} byte, chạy từ giây thứ {{attack_at}} tới hết lượt.
- **guard** chạy trên router:
  - Bắt gói bằng raw socket `AF_PACKET` gắn vào một cổng mạng, không dùng thư viện libpcap.
  - Đếm số truy vấn theo địa chỉ nguồn trong từng chu kỳ 1 giây. Việc kiểm tra ngưỡng và chặn thực hiện ở **cuối mỗi chu kỳ**, không chặn ngay giữa chu kỳ.
  - Khi chặn một địa chỉ mới, guard gửi cảnh báo qua **UDP** tới cổng 9999 của từng router được cấu hình, nội dung `BLOCK <địa chỉ IP> <tên router gửi>`. Cảnh báo không mang thời điểm phát hiện; thời điểm được lấy từ log.
  - Router nhận cảnh báo kiểm tra định dạng, kiểm tra danh sách địa chỉ không được chặn, và kiểm tra địa chỉ đã bị chặn trước đó chưa để không thêm quy tắc trùng.
  - Quy tắc chặn được gỡ toàn bộ khi guard dừng (tín hiệu `SIGINT` hoặc `SIGTERM`). Đề tài chưa có cơ chế tự gỡ chặn sau một thời gian, nên trong lúc guard còn chạy, địa chỉ đã bị chặn sẽ bị chặn cho tới cuối lượt. Đây là một hạn chế được nêu ở Chương 5.

### Các phương án thử nghiệm

Ba lượt thử nghiệm dùng cùng mô hình mạng và cùng thông số, chỉ khác cách xử lý sau khi phát hiện:

- **off (chỉ chặn tại phía đích):** chỉ R3 phát hiện và tự chặn. Lưu lượng tấn công vẫn đi qua các đoạn phía trước R3.
- **on (hợp tác qua mạng điều khiển riêng):** R3 gửi cảnh báo cho R1, R2 qua mạng 10.0.99.0/24. Mạng này được tạo bằng một cổng mạng ảo riêng (`eth3`) trên mỗi router, nối chung vào một cầu mạng ảo trong EVE-NG, tách biệt với các cổng dữ liệu. Đề tài không dùng VLAN.
- **inband (hợp tác chung đường, ưu tiên QoS):** R3 gửi cảnh báo theo chính đường dữ liệu R3 → R2 → R1. Guard đánh dấu gói cảnh báo bằng giá trị DSCP EF (byte TOS `0xB8`). Trên mọi cổng nối giữa hai router, theo cả hai chiều, hàng đợi được chia làm hai làn bằng công cụ `tc`. Gói mang dấu EF đi vào làn ưu tiên và luôn được gửi trước gói thường (mục 4.4.2).
