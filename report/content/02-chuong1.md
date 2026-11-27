# GIỚI THIỆU

## Tổng quan

Đề tài xây dựng một mô hình mạng thử nghiệm gồm sáu máy Linux chạy trong EVE-NG, rồi đo độ trễ của người dùng khi router chọn đường đi theo các cách khác nhau. Phần này nêu cách hiểu của đề tài về các khái niệm chính, mô hình thử nghiệm và ý tưởng giải quyết.

**Độ trễ** trong đề tài được đo bằng thời gian khứ hồi (Round-Trip Time – RTT): thời gian từ lúc client gửi một truy vấn tới lúc nhận được trả lời của server. RTT được đo ngay tại chương trình của client nên phản ánh đúng thời gian người dùng phải chờ.

**Mô hình thử nghiệm** gồm sáu node. Hai máy đầu cuối nằm chung mạng LAN1 sau router R1:

- **Client** đóng vai người dùng cần phản hồi nhanh, như đang gọi thoại hay chơi trò chơi trực tuyến. Client gửi {{client_rate}} truy vấn nhỏ mỗi giây và đo RTT của từng truy vấn.
- **Loadgen** đóng vai một máy đang tải dữ liệu lớn, như tải tệp hay xem video. Loadgen gửi {{load_mbit}} Mbit/s, chia thành {{load_flows}} luồng.

Server nằm sau router R3. Giữa R1 và R3 có **hai đường đi**:

- **Đường dài** R1 → R2 → R3, gồm hai đoạn đường truyền và một router trung gian.
- **Đường ngắn** R1 → R3, gồm một đoạn đường truyền nối thẳng.

Mỗi đoạn đường truyền giữa hai router được cấu hình độ trễ truyền {{link_delay}} mili giây mỗi chiều để mô phỏng khoảng cách địa lý, và băng thông {{link_rate}} Mbit/s. Lưu lượng {{load_mbit}} Mbit/s của loadgen lớn hơn băng thông của một đường nhưng nhỏ hơn tổng băng thông của hai đường ({{two_links_mbit}} Mbit/s). Sơ đồ chi tiết được trình bày ở Hình 4.1.

**Ý tưởng giải quyết** dựa trên vai trò của router: router chỉ làm hai việc là **chọn đường** và **chuyển tiếp** gói tin. Đề tài không thêm thiết bị, không tăng băng thông, mà chỉ thay đổi cách R1 và R3 chọn đường. Ba cách chọn đường được so sánh:

- **Đi đường dài:** mọi lưu lượng đi qua R2. Đây là mốc so sánh.
- **Đi đường ngắn:** mọi lưu lượng đi thẳng R1 → R3, ít đoạn truyền và ít thiết bị trung gian hơn.
- **Chia tải:** các luồng được chia ra cả hai đường, để không đường nào bị quá tải.

## Mục tiêu đề tài

Mục tiêu chung là xây dựng mô hình thử nghiệm và đo được mức giảm độ trễ của người dùng khi router chọn đường phù hợp, so với khi mọi lưu lượng dồn vào một đường. Các mục tiêu cụ thể:

Bảng: Các mục tiêu cụ thể và tiêu chí đánh giá
| STT | Mục tiêu | Chỉ số đo | Tiêu chí đạt |
|---|---|---|---|
| 1 | Xây dựng mô hình có hai đường đi, đo được độ trễ của từng đường | RTT của client khi chưa có tải | RTT đường ngắn thấp hơn rõ rệt so với đường dài |
| 2 | Tái hiện được tình trạng tắc nghẽn làm tăng độ trễ | RTT của client khi có tải, mọi lưu lượng đi một đường | RTT tăng ít nhất 5 lần so với khi chưa có tải |
| 3 | Giảm độ trễ khi mạng có tải bằng cách chọn đường | RTT trung bình của client khi có tải | Giảm ít nhất 80% so với lượt đi đường dài |
| 4 | Không làm giảm khả năng truyền dữ liệu | Thông lượng server nhận được | Không thấp hơn lượt đi đường dài |
| 5 | Kết quả tái hiện được | Toàn bộ quá trình dựng mô hình, đo và vẽ biểu đồ | Thực hiện bằng script, chạy lại cho kết quả tương đương |

Mỗi lượt thử nghiệm kéo dài {{duration}} giây. Loadgen bắt đầu gửi ở giây thứ {{load_at}}, nên mỗi lượt đo được cả độ trễ lúc mạng chưa có tải lẫn lúc có tải.

## Phạm vi đề tài

Đề tài giới hạn ở các nội dung sau:

- Mô hình gồm sáu node: một client, một máy tạo tải, ba router và một server. Mọi node là máy ảo Alpine Linux {{alpine_version}} chạy trong EVE-NG Community Edition.
- Router là máy Linux có bật chức năng chuyển tiếp gói. Việc chọn đường dùng bảng định tuyến tĩnh của Linux, kể cả khi chia tải ra hai đường.
- Độ trễ truyền và băng thông của đường truyền được giả lập bằng công cụ `tc` của Linux, không phải đo trên đường truyền vật lý.
- Lưu lượng dùng giao thức UDP (User Datagram Protocol), do chương trình C của đề tài tạo ra, với tốc độ cố định.
- Đề tài tập trung vào nhóm giải pháp chọn đường: dùng đường ngắn và phân phối tải. Các giải pháp như nâng cấp thiết bị hay ưu tiên lưu lượng theo loại dịch vụ không thuộc phạm vi đề tài.

## Mô tả yêu cầu chức năng

### Chức năng xây dựng mô hình mạng

Hệ thống phải dựng được mô hình sáu node trên EVE-NG, đặt địa chỉ IP, bật chuyển tiếp gói trên router và tạo hai đường đi giữa R1 và R3. Việc tạo máy ảo, tạo mạng và nối dây được thực hiện bằng script thông qua giao diện lập trình của EVE-NG, để có thể dựng lại mô hình giống hệt bằng một lệnh.

### Chức năng tạo lưu lượng

Hệ thống có hai nguồn lưu lượng. Client gửi truy vấn nhỏ đều đặn và nhận trả lời từ server. Loadgen gửi lưu lượng lớn với tốc độ cố định, chia thành nhiều luồng có cổng nguồn khác nhau. Tốc độ, kích thước gói và số luồng đều chỉnh được bằng tham số.

### Chức năng đo lường hiệu năng

Mỗi giây, hệ thống ghi lại:

- Ở client: số truy vấn gửi, số trả lời nhận, tỉ lệ mất gói, RTT trung bình và jitter.
- Ở server: số gói và thông lượng nhận được.
- Ở R1: lưu lượng gửi ra trên từng đường.

Số liệu được ghi thành tệp CSV (Comma-Separated Values) để vẽ biểu đồ và tính toán.

### Chức năng cấu hình chọn đường

Router R1 và R3 phải chuyển được giữa ba chế độ chọn đường (đường dài, đường ngắn, chia tải) bằng một lệnh, không cần khởi động lại. Router R2 luôn chuyển tiếp như nhau.

### Chức năng so sánh và đánh giá kết quả

Hệ thống chạy ba lượt thử nghiệm với cùng thông số, chỉ khác cách chọn đường. Sau khi chạy xong, script tính trung bình các chỉ số lúc chưa có tải và lúc có tải, in bảng so sánh và vẽ biểu đồ theo thời gian.

### Chức năng giám sát trực quan

Trong lúc chạy, màn hình được chia làm bốn ô hiển thị theo từng giây: RTT của client, lưu lượng trên từng đường, thông lượng server nhận được và tiến trình của lượt thử nghiệm. Nhờ đó người xem thấy ngay sự thay đổi khi tải bắt đầu.
