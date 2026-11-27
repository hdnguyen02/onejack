#! LỜI MỞ ĐẦU

**1. Tổng quan tình hình nghiên cứu thuộc lĩnh vực của đề tài**

Các dịch vụ mạng ngày nay như gọi thoại qua Internet, họp trực tuyến, trò chơi trực tuyến đều đòi hỏi dữ liệu tới nơi nhanh. Với những dịch vụ này, băng thông lớn chưa đủ: chỉ cần độ trễ tăng lên vài trăm mili giây là cuộc gọi bị vấp, hình ảnh bị giật, thao tác trong trò chơi bị chậm so với người khác. Khuyến nghị ITU-T G.114 cho thấy độ trễ một chiều của thoại nên giữ dưới {{g114_ms}} mili giây để người nghe không cảm thấy khó chịu [[REF:5]].

Độ trễ của một gói tin là tổng của nhiều thành phần: thời gian router xử lý, thời gian chờ trong hàng đợi, thời gian đẩy gói lên đường truyền và thời gian tín hiệu đi hết chiều dài đường truyền [[REF:6]]. Trong đó, thời gian chờ trong hàng đợi thay đổi mạnh nhất. Khi lưu lượng đi qua một đường truyền vượt quá băng thông của nó, gói tin dồn lại trong hàng đợi của router và có thể phải chờ hàng trăm mili giây. Vì vậy, các hướng giảm độ trễ thường gặp đều xoay quanh hai việc: cho dữ liệu đi con đường ngắn hơn, và tránh để một đường truyền hay một thiết bị bị quá tải.

Ở phía thiết bị mạng, router quyết định gói tin đi theo đường nào. Khi giữa hai điểm có nhiều đường đi, router có thể chọn một đường tốt nhất, hoặc chia lưu lượng ra nhiều đường có chi phí bằng nhau theo kỹ thuật định tuyến nhiều đường chi phí bằng nhau (Equal-Cost Multi-Path – ECMP) [[REF:4]] [[REF:10]]. Kỹ thuật này có sẵn trong nhân Linux và trong hầu hết router thương mại.

Đề tài này tập trung vào cách router **chọn đường** để giảm độ trễ. Đề tài dựng một mô hình mạng có hai đường đi với độ dài khác nhau trên nền tảng giả lập EVE-NG, rồi đo và so sánh độ trễ của người dùng trong ba trường hợp: mọi lưu lượng đi đường dài, mọi lưu lượng đi đường ngắn, và lưu lượng được chia ra cả hai đường.

**2. Ý nghĩa khoa học và thực tiễn của đề tài**

Về khoa học, đề tài tách được hai thành phần của độ trễ để đo riêng: phần do độ dài đường đi và phần do xếp hàng khi đường bị quá tải. Kết quả cho thấy thành phần nào chiếm phần lớn, và mỗi cách chọn đường tác động vào thành phần nào.

Về thực tiễn, sản phẩm của đề tài là một bộ công cụ tái hiện được hoàn toàn: chương trình đo đạc viết bằng C, cấu hình router, script dựng mô hình trên EVE-NG và script đo, vẽ biểu đồ. Bộ công cụ có thể dùng để minh họa trong các học phần mạng máy tính, hoặc làm điểm xuất phát cho các thử nghiệm khác về định tuyến và chất lượng đường truyền.
