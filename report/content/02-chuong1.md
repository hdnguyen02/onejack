# GIỚI THIỆU

## Tổng quan

Đề tài xây dựng một mô hình mạng gồm sáu máy Linux chạy trong EVE-NG, rồi đo độ trễ của người dùng khi router chọn đường theo những cách khác nhau. Phần này giải thích các khái niệm chính, mô hình thử nghiệm và hướng giải quyết.

Trong đề tài, độ trễ được đo bằng thời gian khứ hồi (Round-Trip Time – RTT), tức thời gian từ lúc client gửi một truy vấn tới lúc nhận được trả lời của server. Vì RTT được đo ngay trong chương trình của client, con số này phản ánh sát thời gian người dùng phải chờ.

Mô hình thử nghiệm gồm sáu node. Hai máy đầu cuối nằm chung mạng LAN1 phía sau router R1.

- Client đóng vai người dùng cần phản hồi nhanh, ví dụ đang gọi thoại hay chơi trò chơi trực tuyến. Client gửi {{client_rate}} truy vấn nhỏ mỗi giây và đo RTT của từng truy vấn.
- Loadgen đóng vai một máy đang tải dữ liệu lớn, ví dụ tải tệp hay xem video. Loadgen gửi {{load_mbit}} Mbit/s, chia thành {{load_flows}} luồng.

Server nằm sau router R3. Từ R1 sang R3 có hai đường:

- Đường dài R1 → R2 → R3, đi qua hai đoạn đường truyền và router trung gian R2.
- Đường ngắn R1 → R3, chỉ có một đoạn nối thẳng.

Mỗi đoạn đường truyền giữa hai router có độ trễ truyền {{link_delay}} mili giây mỗi chiều để mô phỏng khoảng cách địa lý, và băng thông {{link_rate}} Mbit/s. Lưu lượng {{load_mbit}} Mbit/s của loadgen vượt băng thông của một đường, nhưng vẫn nhỏ hơn hai đường cộng lại ({{two_links_mbit}} Mbit/s). Sơ đồ chi tiết được trình bày ở Hình 4.1.

Router có hai việc chính là chọn đường và chuyển tiếp gói tin. Đề tài giữ nguyên thiết bị và băng thông, chỉ thay đổi cách R1 và R3 chọn đường, rồi so sánh ba cách:

- Đi đường dài: mọi lưu lượng đi qua R2, dùng làm mốc so sánh.
- Đi đường ngắn: mọi lưu lượng đi thẳng R1 → R3, qua ít đoạn truyền và ít thiết bị trung gian hơn.
- Chia tải: các luồng được chia ra cả hai đường để không đường nào bị quá tải.

## Mục tiêu đề tài

Mục tiêu chung là xây dựng mô hình thử nghiệm và đo xem độ trễ của người dùng giảm được bao nhiêu khi router chọn đường hợp lý, so với khi mọi lưu lượng dồn vào một đường. Các mục tiêu cụ thể được nêu trong bảng dưới.

Bảng: Các mục tiêu cụ thể và tiêu chí đánh giá
| STT | Mục tiêu | Chỉ số đo | Tiêu chí đạt |
|---|---|---|---|
| 1 | Xây dựng mô hình có hai đường đi, đo được độ trễ của từng đường | RTT của client khi chưa có tải | RTT đường ngắn thấp hơn rõ rệt so với đường dài |
| 2 | Tái hiện được tình trạng tắc nghẽn làm tăng độ trễ | RTT của client khi có tải, mọi lưu lượng đi một đường | RTT tăng ít nhất 5 lần so với khi chưa có tải |
| 3 | Giảm độ trễ khi mạng có tải bằng cách chọn đường | RTT trung bình của client khi có tải | Giảm ít nhất 80% so với lượt đi đường dài |
| 4 | Không làm giảm khả năng truyền dữ liệu | Thông lượng server nhận được | Không thấp hơn lượt đi đường dài |
| 5 | Kết quả tái hiện được | Toàn bộ quá trình dựng mô hình, đo và vẽ biểu đồ | Thực hiện bằng script, chạy lại cho kết quả tương đương |

Mỗi lượt thử nghiệm kéo dài {{duration}} giây, loadgen bắt đầu gửi từ giây thứ {{load_at}}. Nhờ vậy trong cùng một lượt đo được độ trễ cả lúc mạng chưa có tải lẫn lúc có tải.

## Phạm vi đề tài

Đề tài giới hạn ở các nội dung sau:

- Mô hình gồm sáu node: một client, một máy tạo tải, ba router và một server. Mọi node là máy ảo Alpine Linux {{alpine_version}} chạy trong EVE-NG Community Edition.
- Router là máy Linux có bật chức năng chuyển tiếp gói. Việc chọn đường dùng bảng định tuyến tĩnh của Linux, kể cả khi chia tải ra hai đường.
- Độ trễ truyền và băng thông của đường truyền được giả lập bằng công cụ `tc` của Linux, không phải đo trên đường truyền vật lý.
- Lưu lượng dùng giao thức UDP (User Datagram Protocol), do chương trình C của đề tài tạo ra, với tốc độ cố định.
- Đề tài tập trung vào nhóm giải pháp chọn đường: dùng đường ngắn và phân phối tải. Các giải pháp như nâng cấp thiết bị hay ưu tiên lưu lượng theo loại dịch vụ không thuộc phạm vi đề tài.

## Mô tả yêu cầu chức năng

### Chức năng xây dựng mô hình mạng

Hệ thống cần dựng được mô hình sáu node trên EVE-NG, đặt địa chỉ IP, bật chuyển tiếp gói trên router và tạo hai đường giữa R1 và R3. Việc tạo máy ảo, tạo mạng và nối dây được làm bằng script qua giao diện lập trình của EVE-NG, nên có thể dựng lại đúng mô hình đó chỉ bằng một lệnh.

### Chức năng tạo lưu lượng

Lưu lượng đến từ hai nguồn. Client gửi đều đặn các truy vấn nhỏ và nhận trả lời từ server. Loadgen gửi lưu lượng lớn với tốc độ cố định, chia thành nhiều luồng có cổng nguồn khác nhau. Tốc độ, kích thước gói và số luồng đều chỉnh được qua tham số dòng lệnh.

### Chức năng đo lường hiệu năng

Mỗi giây, hệ thống ghi lại:

- Ở client: số truy vấn gửi, số trả lời nhận, tỷ lệ mất gói, RTT trung bình và jitter.
- Ở server: số gói và thông lượng nhận được.
- Ở R1: lưu lượng gửi ra trên từng đường.

Số liệu được ghi thành tệp CSV (Comma-Separated Values) để vẽ biểu đồ và tính toán.

### Chức năng cấu hình chọn đường

R1 và R3 cần chuyển được giữa ba cách chọn đường (đường dài, đường ngắn, chia tải) chỉ bằng một lệnh, không phải khởi động lại. R2 thì luôn chuyển tiếp như nhau.

### Chức năng so sánh và đánh giá kết quả

Ba lượt thử nghiệm dùng cùng thông số, chỉ khác cách chọn đường. Chạy xong, script tính trung bình các chỉ số lúc chưa có tải và lúc có tải, in bảng so sánh và vẽ biểu đồ theo thời gian.

### Chức năng giám sát trực quan

Trong lúc chạy, màn hình chia làm bốn ô, cập nhật mỗi giây: RTT của client, lưu lượng trên từng đường, thông lượng server nhận được và tiến trình của lượt thử nghiệm. Người xem thấy được ngay chuyện gì xảy ra khi tải bắt đầu.
