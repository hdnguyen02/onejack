# Thiết kế: Demo cải thiện hiệu năng mạng nhờ các node cộng tác chặn truy vấn xấu

- Ngày: 2026-11-11
- Hạn nộp: 2026-11-15 (còn 4 ngày)
- Trạng thái: đã duyệt (2026-11-11)

Ký hiệu: **[Người dùng]** là điều người dùng đã nói hoặc đồng ý. **[Lựa chọn của Claude]** là quyết định mình tự đưa ra, người dùng có thể đổi.

## 1. Mục đích và lý do

Đề tài môn học: *"Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu"*. Đề yêu cầu lập trình một ứng dụng demo thể hiện vấn đề, viết bằng C trên Linux, và chạy trên EVE-NG. Đề không kèm tài liệu tham khảo. **[Người dùng]**

Ý tưởng demo **[Người dùng đồng ý]**: một máy tấn công gửi truy vấn dồn dập (flood) tới server. Node gần server phát hiện ra nó, rồi **báo cho các node khác** trên đường đi để chặn kẻ tấn công **ngay ở cửa vào mạng**. Nhờ vậy lưu lượng xấu không chiếm đường truyền bên trong nữa, và client thật không còn bị chậm.

Demo chạy hai lượt để so sánh **[Người dùng đồng ý]**:

1. **Không hợp tác:** chỉ node cạnh server chặn. Gói xấu vẫn đi qua R1 và R2, làm nghẽn đường truyền chung, nên client thật bị trễ và mất gói.
2. **Có hợp tác:** node cạnh server phát cảnh báo, R1 chặn ngay từ đầu. Đường truyền thông thoáng, client thật trở lại bình thường.

Người xem là giảng viên và cả lớp, nên kết quả phải **nhìn thấy được** qua log hoặc số liệu theo từng giây, và cuối cùng có bảng hoặc biểu đồ so sánh hai lượt. **[Lựa chọn của Claude, người dùng đồng ý với mô hình]**

## 2. Mục tiêu, ngoài phạm vi, điều tuyệt đối tránh

**Mục tiêu**
- Lab trong EVE-NG chạy ổn định trên laptop của người dùng.
- Bốn chương trình C: `server`, `client`, `attacker`, `guard`.
- Hai lượt demo cho ra số liệu khác biệt rõ ràng: độ trễ và tỉ lệ mất gói của client, lưu lượng xấu trên các link bên trong.
- README hướng dẫn cài đặt, dựng lab và chạy demo từng bước, để người dùng tự làm lại và tự trình bày được.

**Ngoài phạm vi**
- Không làm hệ thống chống DDoS thật: không xử lý IP giả mạo, botnet nhiều nguồn, hay tấn công tầng thấp.
- Không xác thực hay mã hóa gói cảnh báo giữa các node. Phần này chỉ ghi vào mục "hạn chế / hướng phát triển".
- Không có GUI, không hỗ trợ IPv6.
- Không viết báo cáo Word, trừ khi người dùng yêu cầu sau.

**Điều tuyệt đối tránh** (dù chạy được nhưng vẫn coi là thất bại)
- Hai lượt demo cho ra số liệu gần giống nhau, khiến người xem không thấy được lợi ích của việc hợp tác.
- Lab quá nặng, làm laptop treo hoặc demo bị giật ngay lúc trình bày.
- Code hoặc mô hình quá phức tạp, người dùng không tự giải thích lại được trước giảng viên.

## 3. Ràng buộc

- Ngôn ngữ C, chạy trên Linux. Môi trường là EVE-NG. **[Người dùng]**
- Máy host: Ubuntu 22.04 chạy trên máy thật, i5-1135G7 (4 nhân, 8 luồng), 15GB RAM (bình thường chỉ trống khoảng 5,7GB), ổ cứng trống 324GB, KVM đã bật nested = Y. Trên máy có VirtualBox nhưng sẽ không dùng.
- Chưa cài EVE-NG hay image nào. **[Người dùng]**
- Toàn bộ dự án nằm trong `/home/devnguyenho/Desktop/onejack/`, thư mục này không phải git repo. **[Người dùng]**
- **Cách phân công khi cài đặt và chạy lab** **[Người dùng]**: Claude đưa ra từng lệnh, người dùng tự chạy các lệnh cần `sudo` (gõ `! <lệnh>` ngay trong phiên để kết quả hiện lại cho Claude). Những lệnh không cần `sudo` thì Claude tự chạy, gồm build code, kiểm tra, và SSH vào các node khi đã có mạng quản lý. Claude tự dựng lab, chạy thử và chỉnh các con số. Script chạy demo cuối cùng chỉ cần một lệnh.
- Thời gian 4 ngày. Lịch dự kiến: N1 cài EVE-NG và dựng lab, N2 viết code C, N3 chạy thử và đo đạc, N4 dự phòng và chuẩn bị trình bày. **[Lựa chọn của Claude]**

## 4. Hạ tầng

**[Lựa chọn của Claude]**
- **EVE-NG Community Edition** cài thành máy ảo trên **KVM/QEMU** (dùng virt-manager hoặc virt-install), cấp 4 vCPU, 6 đến 8GB RAM, ổ đĩa khoảng 60GB, bật nested virtualization (CPU mode `host-passthrough`). Người dùng truy cập giao diện web EVE-NG từ trình duyệt trên host.
- Node trong lab: **một image Linux nhẹ dùng chung cho mọi node** (Alpine hoặc Debian/Ubuntu cloud dạng qcow2), mỗi node 256 đến 512MB RAM. Image cần có `iproute2` (lệnh `ip`, `tc`) và `iptables`. Người build chọn distro cụ thể.
- **Ngân sách RAM:** mặc định cấp **6GB** cho máy ảo EVE-NG, không dùng 8GB. Ưu tiên Alpine, mỗi node 256MB, tổng 6 node khoảng 1,5GB. Trước khi chạy lab, người dùng tắt bớt app nặng để còn trống ít nhất khoảng 7GB. Nếu đã làm vậy mà vẫn thiếu thì giảm xuống 4GB và hạ tốc độ flood (chỉ cần vẫn lớn hơn băng thông nút cổ chai `tc` là được). **[Lựa chọn của Claude]**
- Chương trình C được **biên dịch tĩnh trên host** (`gcc -static`) rồi copy vào node, như vậy node không cần cài gcc. Nếu dùng Alpine (musl) mà biên dịch tĩnh glibc gặp lỗi, người build có thể biên dịch ngay trong node. Cách copy vào node (scp qua mạng quản lý của EVE, hoặc đóng sẵn vào image) do người build quyết định.

## 5. Topology và địa chỉ IP

**[Lựa chọn của Claude]**

```
 Attacker 10.0.1.10 ─┐
                     ├─(sw LAN1 10.0.1.0/24)─ R1 ── 10.0.12.0/24 ── R2 ── 10.0.23.0/24 ── R3 ─(10.0.3.0/24)─ Server 10.0.3.10
 Client   10.0.1.20 ─┘                        .1                    .2/.2               .3/.3        .1

 Mạng điều khiển (riêng, chỉ dùng để gửi cảnh báo): R1 10.0.99.1, R2 10.0.99.2, R3 10.0.99.3  (sw CTRL 10.0.99.0/24)
```

- R1, R2, R3 là node Linux bật `ip_forward` và cấu hình route tĩnh. Attacker và Client dùng R1 làm gateway, Server dùng R3 làm gateway.
- Cảnh báo đi trên **mạng điều khiển riêng** để không bị chính đợt flood làm nghẽn và mất gói. Khi trình bày cần giải thích đây là chủ ý thiết kế (giống mạng out-of-band trong thực tế).
- **Tạo nút cổ chai có chủ đích:** dùng `tc` giới hạn băng thông link R1–R2 và R2–R3 khoảng **10 Mbit/s**. Lưu lượng flood lớn hơn mức này nhiều, nên ở lượt "không hợp tác" client chắc chắn bị ảnh hưởng. Nếu không có giới hạn này, link ảo trong EVE quá nhanh, hai lượt sẽ ra số liệu gần giống nhau (vi phạm "điều tuyệt đối tránh" số 1).
- Mỗi node có một script cấu hình riêng (đặt IP, route, `tc`, `ip_forward`) để dựng lại lab nhanh.

## 6. Các chương trình C

**[Lựa chọn của Claude]** Chỉ dùng thư viện chuẩn và socket API của Linux, không dùng thư viện ngoài. Code viết đơn giản, dễ giải thích, có comment tiếng Việt ở các đoạn quan trọng.

**Giao thức truy vấn:** UDP, cổng **9000**.
- Truy vấn: `Q <seq> <timestamp_us>`. Client gửi gói nhỏ. Attacker đệm thêm payload cho gói to khoảng 1000 byte.
- Trả lời: server gửi ngược lại `A <seq> <timestamp_us>` y nguyên, để client tự tính RTT.

**`server`**: nhận truy vấn, trả lời, mỗi giây in ra một dòng gồm số truy vấn nhận được và số đã trả lời, tách riêng theo từng IP nguồn.

**`client`**: gửi đều khoảng 20 truy vấn mỗi giây. Mỗi giây in một dòng: đã gửi, đã nhận, % mất gói, RTT trung bình (ms). Đồng thời ghi ra file CSV để vẽ biểu đồ. Truy vấn nào sau 1 giây chưa có trả lời thì tính là mất.

**`attacker`**: flood UDP tới server, tốc độ chỉnh được qua tham số (mặc định khoảng 5000 gói/s × 1000 byte, tức khoảng 40 Mbit/s, gấp 4 lần nút cổ chai).

**`guard`**: chạy trên R1, R2, R3, có hai vai trò bật/tắt bằng tham số:
- **Phát hiện** (chỉ bật trên R3, node bảo vệ server): dùng raw socket `AF_PACKET` trên cổng nhận, đếm số gói UDP tới cổng 9000 của từng IP nguồn trong mỗi giây. IP nào vượt **ngưỡng 200 gói/s** thì bị chặn tại chỗ bằng `iptables -I FORWARD -s <ip> -j DROP`. Nếu bật chế độ hợp tác thì gửi thêm cảnh báo tới các node cùng nhóm.
- **Nghe cảnh báo** (chỉ bật ở chế độ hợp tác): lắng nghe UDP cổng **9999** trên mạng điều khiển. Nhận cảnh báo thì chặn IP đó bằng iptables y như trên.
- Gói cảnh báo dạng văn bản: `BLOCK <ip> <tên_node_gửi>`. Danh sách các node nhận lấy từ tham số dòng lệnh. Node gửi cảnh báo trực tiếp tới tất cả các node khác (mạng nhỏ nên không cần chuyển tiếp nhiều chặng). IP nào đã chặn rồi thì bỏ qua cảnh báo lặp lại.
- Mỗi sự kiện in một dòng log dễ đọc, kèm thời gian, ví dụ: `[R3] PHÁT HIỆN 10.0.1.10 (5123 gói/s) → CHẶN, gửi cảnh báo tới R1,R2` và `[R1] NHẬN cảnh báo từ R3 → CHẶN 10.0.1.10`.
- Khi thoát (Ctrl+C) thì xóa hết các rule iptables mình đã thêm, để chạy lượt sau từ trạng thái sạch.
- Ghi chú: `AF_PACKET` bắt gói trước netfilter nên R3 vẫn "thấy" gói của IP đã bị chặn. Đây không phải lỗi, chỉ cần không chặn lặp lại.

**Ngưỡng:** client gửi 20 gói/s, attacker gửi 5000 gói/s, ngưỡng đặt ở 200 gói/s. Khoảng cách giữa hai bên rất xa nên không có báo nhầm.

**Build:** một `Makefile` duy nhất, build cả bốn chương trình dạng tĩnh.

## 7. Kịch bản demo và đo đạc

**[Lựa chọn của Claude]** Mỗi lượt chạy khoảng 60 giây:
- giây 0–15: chỉ client chạy, ghi lại mức nền
- giây 15: bật attacker
- giây 15–60: quan sát

**Lượt 1, không hợp tác:** `guard` trên R3 chỉ bật phát hiện. R1 và R2 không chạy guard.
**Lượt 2, có hợp tác:** `guard` trên R3 bật phát hiện và gửi cảnh báo. R1 và R2 chạy guard ở chế độ nghe cảnh báo.

**Số liệu ghi lại cho mỗi lượt:**
- Từ client: RTT trung bình và % mất gói theo từng giây (file CSV).
- Lưu lượng trên link R1→R2 (byte/s, lấy từ `/proc/net/dev` hoặc `ip -s link` mỗi giây). Ở lượt 2, con số này phải giảm về gần mức nền.
- Thời gian từ lúc bắt đầu tấn công tới lúc R1 chặn (ở lượt 2).

**Kết quả mong đợi:** lượt 1 thì client bị mất gói và trễ cao kéo dài, link R1–R2 bị bão hòa. Lượt 2 thì chỉ trong khoảng 1–2 giây sau khi tấn công, R1 đã chặn, client trở lại bình thường, link R1–R2 hết nghẽn.

**Demo chạy trực tiếp trước lớp trên laptop này** **[Người dùng]**. Vì vậy cần có thêm:
- **Script khởi động một lệnh:** bật lab, cấu hình mọi node, kiểm tra đường đi Client → Server (health check) và báo "SẴN SÀNG" hoặc chỉ ra chỗ lỗi.
- **Script chạy từng lượt** (`demo off` / `demo on`): tự bật các chương trình trên đúng node, theo kịch bản thời gian ở trên, rồi thu số liệu về host.
- **Script reset:** xóa rule iptables, dừng mọi tiến trình, để chạy lại ngay lượt khác mà không phải khởi động lại lab.
- **Màn hình trình bày:** chia cửa sổ (tmux hoặc nhiều terminal) để lớp thấy cùng lúc log của client, log của guard trên R1/R3, và lưu lượng trên link R1–R2. **[Lựa chọn của Claude]**
- **Phương án dự phòng:** quay sẵn video màn hình của hai lượt chạy thành công, cùng file CSV/PNG, để dùng khi laptop trục trặc lúc trình bày.
- **Checklist trước giờ trình bày** trong README: tắt app nặng, bật lab sớm 10 phút, chạy health check.

**Trình bày:** một script nhỏ trên host vẽ biểu đồ từ file CSV (gnuplot hoặc Python, người build chọn), xuất ảnh PNG để đưa vào slide hay báo cáo. Ngoài ra có một bảng tóm tắt gồm RTT trung bình, % mất gói, và lưu lượng trung bình trên link R1–R2 trong giai đoạn bị tấn công của từng lượt.

## 8. Sản phẩm bàn giao

```
onejack/
  docs/superpowers/specs/   bản thiết kế này
  src/                      server.c client.c attacker.c guard.c Makefile
  lab/                      script cấu hình cho từng node (r1.sh, r2.sh, ...), file topology EVE-NG (.unl) nếu xuất được
  scripts/                  script chạy demo, thu số liệu, vẽ biểu đồ
  results/                  CSV và PNG của hai lượt
  README.md                 hướng dẫn: cài EVE-NG trên KVM → nạp image → dựng lab → build → chạy 2 lượt → xem kết quả
```

## 9. Phần để lại cho người build

- Phiên bản EVE-NG CE cụ thể và cách cài (ISO hay OVF chuyển sang KVM).
- Distro Linux cụ thể cho node, và cách đưa binary vào node.
- Tên interface trong node và cách nối dây cụ thể trong giao diện EVE-NG.
- Công cụ vẽ biểu đồ.
- Tinh chỉnh các con số (ngưỡng, tốc độ flood, băng thông `tc`) nếu khi chạy thật hai lượt chưa khác nhau rõ. Mọi con số ở trên chỉ là điểm xuất phát.
- Những bước người dùng phải tự làm tay (đăng ký hoặc tải file EVE-NG, thao tác trên giao diện web) cần ghi rõ trong README. Người build không giả định là mình làm thay được các bước đó.
