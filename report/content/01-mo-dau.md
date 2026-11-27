#! LỜI MỞ ĐẦU

**1. Tổng quan tình hình nghiên cứu thuộc lĩnh vực của đề tài**

Các dịch vụ mạng ngày nay như gọi thoại qua Internet, họp trực tuyến, trò chơi trực tuyến đều đòi hỏi dữ liệu tới nơi nhanh. Với những dịch vụ này, chỉ có đường truyền tốc độ cao là chưa đủ. Khi độ trễ tăng thêm vài trăm mili giây, cuộc gọi bắt đầu bị vấp, hình ảnh bị giật và người chơi phản ứng chậm hơn người khác. Khuyến nghị ITU-T G.114 cho thấy độ trễ một chiều của thoại nên giữ dưới {{g114_ms}} mili giây để người nghe không cảm thấy khó chịu [[REF:5]].

Độ trễ của một gói tin là tổng của nhiều thành phần: thời gian router xử lý, thời gian chờ trong hàng đợi, thời gian đẩy gói lên đường truyền và thời gian tín hiệu đi hết chiều dài đường truyền [[REF:6]]. Trong đó, thời gian chờ trong hàng đợi thay đổi mạnh nhất. Khi lưu lượng đi qua một đường truyền vượt quá băng thông của nó, gói tin dồn lại trong hàng đợi của router và có thể phải chờ hàng trăm mili giây. Vì vậy, các cách giảm độ trễ thường gặp đều nhằm cho dữ liệu đi đường ngắn hơn, hoặc tránh để một đường truyền hay một thiết bị bị quá tải.

Trong mạng, router là thiết bị quyết định gói tin đi theo đường nào. Khi giữa hai điểm có nhiều đường, router có thể chọn ra một đường tốt nhất, hoặc chia lưu lượng ra nhiều đường có chi phí bằng nhau theo kỹ thuật định tuyến nhiều đường chi phí bằng nhau (Equal-Cost Multi-Path – ECMP) [[REF:4]] [[REF:10]]. Kỹ thuật này có sẵn trong nhân Linux và trong hầu hết router thương mại.

Khóa luận này tập trung vào việc router chọn đường để giảm độ trễ. Em dựng trên EVE-NG một mô hình mạng có hai đường đi dài ngắn khác nhau, sau đó đo độ trễ của người dùng trong ba trường hợp: mọi lưu lượng đi đường dài, mọi lưu lượng đi đường ngắn, và lưu lượng được chia ra cả hai đường.

**2. Ý nghĩa khoa học và thực tiễn của đề tài**

Về mặt khoa học, đề tài đo riêng được hai phần của độ trễ: phần do đường đi dài hay ngắn, và phần do gói phải xếp hàng khi đường quá tải. Từ số liệu có thể thấy phần nào lớn hơn, và mỗi cách chọn đường làm giảm phần nào.

Về mặt thực tiễn, toàn bộ phần thực nghiệm có thể chạy lại từ đầu bằng các chương trình C và script đi kèm, từ dựng mô hình trên EVE-NG tới đo đạc và vẽ biểu đồ. Bộ công cụ này có thể dùng để minh họa trong các học phần mạng máy tính, hoặc làm điểm xuất phát cho các thử nghiệm khác về định tuyến và chất lượng đường truyền.
