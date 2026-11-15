#! LỜI MỞ ĐẦU

**1. Tổng quan tình hình nghiên cứu thuộc lĩnh vực của đề tài**

Tấn công từ chối dịch vụ (Denial of Service – DoS) là kiểu tấn công không cần đột nhập vào hệ thống. Kẻ tấn công chỉ cần gửi thật nhiều lưu lượng vô nghĩa tới một máy chủ hoặc một đường truyền cho tới khi người dùng thật không còn dùng được dịch vụ. Khi lưu lượng đến từ rất nhiều máy cùng lúc, ta gọi là tấn công từ chối dịch vụ phân tán (Distributed Denial of Service – DDoS). Mirkovic và Reiher đã phân loại khá đầy đủ các kiểu tấn công này cùng các hướng phòng thủ tương ứng [[REF:7]]. Một điểm được nhắc lại nhiều lần trong các tài liệu là: lọc càng gần nạn nhân thì càng dễ nhận ra kẻ tấn công, nhưng lọc càng gần nguồn thì càng tiết kiệm tài nguyên mạng [[REF:3]].

Ở quy mô Internet, các nhà mạng đã có những cơ chế cho phép một bên "nhờ" bên khác chặn giúp lưu lượng xấu. Remotely Triggered Black Hole (RTBH) cho phép ra lệnh từ xa để các router biên bỏ toàn bộ lưu lượng tới một địa chỉ đang bị tấn công [[REF:4]]. BGP FlowSpec đi xa hơn: các router trao đổi với nhau những quy tắc lọc chi tiết theo địa chỉ nguồn, đích, cổng, rồi tự áp dụng [[REF:6]]. Ngoài ra, khuyến nghị BCP 38 yêu cầu router ở cửa vào loại bỏ những gói mang địa chỉ nguồn giả mạo ngay từ đầu [[REF:2]]. Điểm chung của các giải pháp này là **các node mạng hợp tác với nhau**: thông tin về kẻ tấn công được đưa từ nơi phát hiện tới nơi chặn hiệu quả nhất.

Trong nước, các nghiên cứu và đồ án về an ninh mạng thường tập trung vào phát hiện xâm nhập hoặc cấu hình tường lửa trên một thiết bị đơn lẻ. Đề tài này chọn một góc nhỏ hơn và cụ thể hơn: dựng một mô hình mạng thu nhỏ, viết các chương trình C chạy trên router Linux, rồi đo xem việc hợp tác giữa các router thay đổi hiệu năng mạng như thế nào.

**2. Ý nghĩa khoa học và thực tiễn của đề tài**

Về khoa học, đề tài lượng hóa một nhận định quen thuộc nhưng ít khi được đo trực tiếp ở quy mô phòng lab: chặn ở gần nạn nhân bảo vệ được máy chủ nhưng không bảo vệ được mạng. Bằng cùng một kịch bản tấn công, cùng một mô hình mạng, đề tài so sánh độ trễ của người dùng thật và lưu lượng trên đường truyền giữa ba cách xử lý: chỉ chặn ở router gần máy chủ, hợp tác qua một mạng điều khiển riêng, và hợp tác ngay trên đường dữ liệu có ưu tiên chất lượng dịch vụ (Quality of Service – QoS).

Về thực tiễn, sản phẩm của đề tài là một bộ công cụ có thể chạy lại được từ đầu: mã nguồn C, cấu hình mạng, script dựng lab trên EVE-NG và script đo đạc. Bộ công cụ này có thể dùng để minh họa trong các học phần mạng máy tính, hoặc làm điểm xuất phát cho những thử nghiệm phức tạp hơn như xác thực cảnh báo hay chống giả mạo địa chỉ.
