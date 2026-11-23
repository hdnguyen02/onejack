# Kịch bản trình bày đồ án với giảng viên

**Đề tài:** Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu.

**Thời lượng gợi ý:** khoảng 20 phút trình bày + demo, sau đó hỏi đáp.

| Phần | Nội dung | Thời gian |
|---|---|---|
| 1 | Mở đầu, đặt vấn đề | 2 phút |
| 2 | Ý tưởng giải pháp | 2 phút |
| 3 | Mô hình mạng và môi trường | 3 phút |
| 4 | Thiết kế và code chính | 4 phút |
| 5 | Demo trực tiếp | 5 phút |
| 6 | Kết quả đo | 2 phút |
| 7 | Hạn chế, hướng phát triển, kết luận | 2 phút |
| 8 | Hỏi đáp | tùy giảng viên |

Mỗi slide bên dưới có: **Trên slide** (nội dung hiển thị) và **Lời nói** (gợi ý nói, không cần thuộc nguyên văn).

---

## Chuẩn bị trước giờ trình bày (10 phút trước)

- [ ] Bật máy ảo EVE, `ssh root@<EVE_IP>`, `cd /root/onejack`, chạy `scripts/lab-up.sh` → thấy **SẴN SÀNG**.
- [ ] Mở sẵn trang web EVE (`http://<EVE_IP>`), lab `collab-defense`, để chỉ sơ đồ.
- [ ] Phóng to chữ terminal (Ctrl + Shift + +).
- [ ] Mở sẵn biểu đồ [results/eve-v2/rtt.png](results/eve-v2/rtt.png) và [results/eve-v2/link.png](results/eve-v2/link.png) phòng khi demo lỗi.
- [ ] Mở sẵn [src/guard.c](src/guard.c) trong editor, đặt sẵn ở hàm `check_rates`.
- [ ] Tắt thông báo, đóng ứng dụng nặng.

---

## Phần 1. Mở đầu, đặt vấn đề (2 phút)

### Slide 1 — Trang bìa

**Trên slide:** tên đề tài, họ tên sinh viên, MSSV, giảng viên hướng dẫn.

**Lời nói:**
> Em chào thầy/cô. Em là ..., hôm nay em trình bày đề tài "Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu". Bài trình bày gồm: vấn đề, ý tưởng giải pháp, mô hình, phần hiện thực, demo trực tiếp trên EVE-NG và kết quả đo.

### Slide 2 — Vấn đề: tấn công làm nghẽn mạng

**Trên slide:**
- Kẻ tấn công gửi dồn dập truy vấn rác (UDP flood) tới server.
- Cách phổ biến: chặn ở router **gần server**.
- Hình: [report/figures/victim_vs_edge.png](report/figures/victim_vs_edge.png) (chặn gần nạn nhân vs chặn ở cửa vào).

**Lời nói:**
> Khi bị flood, cách phản ứng thường gặp là chặn ở router hoặc firewall đứng ngay trước server. Cách này bảo vệ được server. Nhưng lúc gói rác bị chặn thì nó đã đi hết các đường truyền ở giữa rồi. Những đường đó vẫn bị chiếm băng thông, và người dùng thật đi chung đường vẫn bị chậm.
>
> Nói gọn: **chặn gần nạn nhân bảo vệ được server, nhưng không bảo vệ được mạng.** Đề tài của em giải quyết đúng chỗ này.

### Slide 3 — Mâu thuẫn cốt lõi

**Trên slide:**

| | R3 (gần server) | R1 (cửa vào) |
|---|---|---|
| Biết ai tấn công? | Có | Không |
| Chặn có giải phóng mạng? | Không | Có |

**Lời nói:**
> Router gần server thấy rõ ai đang dồn truy vấn vào server, nên phát hiện tốt nhất. Còn router ở cửa vào thì chặn hiệu quả nhất, vì rác bị vứt trước khi vào mạng. Nhưng router cửa vào lại không biết lưu lượng nào là xấu, nhất là khi nó thuộc một đơn vị khác, ví dụ nhà mạng. **Nơi phát hiện và nơi chặn tốt nhất không trùng nhau**, nên cần một cơ chế đưa thông tin từ chỗ này sang chỗ kia.

---

## Phần 2. Ý tưởng giải pháp (2 phút)

### Slide 4 — Các node cộng tác

**Trên slide:**
- R3 phát hiện → tự chặn → gửi cảnh báo `BLOCK 10.0.1.10 R3` cho R1, R2.
- R1 chặn ngay ở cửa vào → rác không vào mạng nữa.
- Hình: [report/figures/sequence.png](report/figures/sequence.png).

**Lời nói:**
> Giải pháp là cho các router hợp tác. R3 phát hiện kẻ tấn công thì không chỉ tự chặn mà còn gửi một gói cảnh báo vài chục byte cho R1 và R2. R1 nhận được thì chặn luôn ở cửa vào. Ý tưởng này ngoài thực tế đã được dùng ở quy mô Internet, như RTBH và BGP FlowSpec của các nhà mạng. Đồ án của em dựng một phiên bản thu nhỏ để đo được lợi ích cụ thể.

### Slide 5 — Ba lượt thử nghiệm

**Trên slide:**

| Lượt | Cách xử lý |
|---|---|
| off | Chỉ R3 tự chặn (mốc so sánh) |
| on | Hợp tác, cảnh báo đi mạng điều khiển riêng |
| inband | Hợp tác, cảnh báo đi chung đường dữ liệu + ưu tiên QoS |

**Lời nói:**
> Để chứng minh, em so sánh ba lượt với cùng một kịch bản tấn công. Lượt off là mốc. Lượt on cho cảnh báo đi một mạng điều khiển riêng, giống mạng quản lý của nhà mạng. Lượt inband thì bỏ mạng riêng, cho cảnh báo đi chung đường với dữ liệu, vì ngoài thực tế các router ở xa nhau, không phải lúc nào cũng có đường riêng. Để cảnh báo không bị kẹt sau đống rác, gói cảnh báo được đánh dấu ưu tiên bằng QoS.

---

## Phần 3. Mô hình mạng và môi trường (3 phút)

### Slide 6 — Sơ đồ mạng

**Trên slide:** hình [report/figures/topology.png](report/figures/topology.png) hoặc sơ đồ ASCII:

```
 Attacker 10.0.1.10 ─┐
                     ├─ R1 ══10Mbit══ R2 ══10Mbit══ R3 ── Server 10.0.3.10
 Client   10.0.1.20 ─┘   │             │              │
                         └──── mạng điều khiển 10.0.99.0/24 ────┘
```

**Lời nói:**
> Mô hình có 6 node. Attacker và client cùng nằm sau R1. Ba router nối thành một đường thẳng, server nằm sau R3. Hai link giữa các router bị giới hạn 10 Mbit/s để tạo nút cổ chai, vì link ảo trong máy tính quá nhanh, không giới hạn thì sẽ không thấy nghẽn. Ba router còn nối chung mạng điều khiển 10.0.99.0/24, dùng cho lượt on.
>
> Client gửi 20 truy vấn/giây. Attacker gửi 5000 gói/giây, mỗi gói 1000 byte, khoảng 40 Mbit/s, gấp bốn lần nút cổ chai.

**(Chuyển sang trình duyệt, chỉ lab `collab-defense` trên giao diện EVE-NG.)**

### Slide 7 — Hàng đợi 2 làn (QoS)

**Trên slide:** hình [report/figures/two_lane_queue.png](report/figures/two_lane_queue.png).
- Làn 1: gói có TOS `0xB8` (DSCP EF) → luôn gửi trước.
- Làn 2: mọi gói khác.
- Mỗi làn tối đa 500 KB ≈ 400 ms ở 10 Mbit/s.

**Lời nói:**
> Trên mỗi link giữa router, em cấu hình bằng `tc` một hàng đợi hai làn. Gói nào có byte TOS bằng 0xB8, tức DSCP EF, thì đi làn ưu tiên, giống xe cứu thương được chen lên đầu khi kẹt xe. Gói cảnh báo ở lượt inband mang dấu này.

### Slide 8 — Môi trường thử nghiệm

**Trên slide:**
- EVE-NG Community trong máy ảo, 6 node Alpine Linux.
- Lab tạo tự động qua REST API của EVE-NG (`lab/eve-create-lab.sh`).
- Chương trình C biên dịch tĩnh, chép thẳng sang node.
- Dự phòng: cùng mô hình bằng network namespace.

**Lời nói:**
> Toàn bộ chạy trong EVE-NG. Thay vì kéo thả bằng tay, em viết script tạo image Alpine và tạo lab qua API, nên lab dựng lại được giống hệt chỉ bằng một lệnh. Trước mỗi lần demo, script `lab-up.sh` cấu hình và kiểm tra toàn bộ, in ra "SẴN SÀNG" thì mới chạy.

---

## Phần 4. Thiết kế và code chính (4 phút)

### Slide 9 — Bốn chương trình C

**Trên slide:**

| Chương trình | Chạy ở | Nhiệm vụ |
|---|---|---|
| `server` | Server | Trả lời truy vấn `Q <seq> <ts>` bằng `A <seq> <ts>` |
| `client` | Client | 20 truy vấn/s, đo RTT và mất gói |
| `attacker` | Attacker | Flood 5000 gói/s × 1000 byte |
| `guard` | R1, R2, R3 | Phát hiện, chặn, gửi và nhận cảnh báo |

**Lời nói:**
> Em viết bốn chương trình C. Điểm đáng chú ý: gói của attacker cũng bắt đầu bằng "Q" như truy vấn thật, nên không thể phân biệt bằng nội dung. Hệ thống buộc phải phân biệt bằng hành vi, tức là số gói mỗi giây, giống tình huống thực tế. Phần trọng tâm là `guard`.

### Slide 10 — Guard: luồng xử lý

**Trên slide:** hình [report/figures/guard_flow.png](report/figures/guard_flow.png).

**Lời nói:**
> Guard chạy một vòng lặp `poll()` duy nhất, chờ cùng lúc hai nguồn: raw socket bắt gói, và socket nhận cảnh báo. Mỗi giây, guard xem IP nào vượt 200 gói/giây thì chặn bằng iptables và gửi cảnh báo. Cùng một chương trình, khác tham số dòng lệnh thì đóng vai trò khác: R3 chạy với `-d` để phát hiện và `-P` để gửi cảnh báo, R1 và R2 chạy với `-l` để nghe.

### Slide 11 — Code: phát hiện (mở editor)

**Mở** [src/guard.c:141](src/guard.c#L141) — hàm `handle_packet`.

**Lời nói:**
> Raw socket `AF_PACKET` cho em thấy mọi gói đi vào card mạng của R3. Hàm này đọc thẳng các byte của header IP: byte 0 để biết IPv4 và độ dài header, byte 9 để biết là UDP, rồi lấy cổng đích. Nếu là truy vấn tới cổng 9000 thì lấy IP nguồn ở byte 12 để đếm.

**Mở** [src/guard.c:108](src/guard.c#L108) — hàm `check_rates`.

> Mỗi giây, hàm này lấy danh sách IP vượt ngưỡng. Với từng IP: kiểm tra whitelist để không chặn nhầm client và server, kiểm tra đã chặn chưa, gọi iptables, rồi gửi cảnh báo nếu đang ở chế độ hợp tác.

### Slide 12 — Code: cảnh báo, QoS và an toàn

**Mở lần lượt:**
- [src/guard.c:277-283](src/guard.c#L277-L283) — `setsockopt(IP_TOS, 0xB8)`:
  > Đánh dấu ưu tiên chỉ cần một lệnh `setsockopt` trên socket cảnh báo. Mọi gói gửi qua socket đó đều mang dấu EF.
- [src/alert.c:34](src/alert.c#L34) — `alert_parse`:
  > Cảnh báo đến từ mạng nên được kiểm tra chặt: đúng tiền tố, IP hợp lệ, tên node chỉ gồm ký tự cho phép.
- [src/firewall.c:25](src/firewall.c#L25) — hàm `run`:
  > Guard gọi iptables bằng `fork` và `execvp` với từng tham số riêng, không nối chuỗi rồi chạy qua shell, nên không thể bị chèn lệnh.
- [src/blocklist.c:21](src/blocklist.c#L21):
  > Guard không bao giờ chặn mạng điều khiển và các IP trong whitelist, kể cả khi cảnh báo yêu cầu.

---

## Phần 5. Demo trực tiếp (5 phút)

### Slide 13 — Màn hình demo

**Trên slide:** giải thích 4 ô của màn hình tmux.

| Vị trí | Hiển thị |
|---|---|
| Trên trái | RTT của client mỗi giây |
| Dưới trái | Lưu lượng link R1 → R2 |
| Trên phải | Sự kiện phát hiện, cảnh báo, chặn |
| Dưới phải | Tiến trình `demo.sh` |

**Lời nói:**
> Mỗi lượt chạy 60 giây, tấn công bắt đầu ở giây 15. Thầy/cô chú ý ô RTT bên trái trên và ô lưu lượng bên trái dưới.

### Demo lượt 1 — off

```
scripts/tmux-demo.sh off
```

**Lời nói trong lúc chạy:**
> - Trước giây 15: RTT khoảng 2 ms, link gần như trống.
> - Giây 15 tấn công bắt đầu. Chưa tới 1 giây sau, ô sự kiện hiện "R3 PHÁT HIỆN 10.0.1.10 → CHẶN". Server đã được bảo vệ.
> - Nhưng thầy/cô nhìn ô bên trái: link R1 → R2 vẫn **10 Mbit/s**, RTT của client lên **khoảng 400 ms** và giữ nguyên tới hết lượt. Rác vẫn chạy đầy đường R1 → R2 → R3, chỉ bị vứt ở R3.

Chạy xong gõ `exit`.

### Demo lượt 2 — on (hoặc inband, tùy thời gian)

```
scripts/tmux-demo.sh on
```

**Lời nói trong lúc chạy:**
> - Giây 15 tấn công. R3 phát hiện, và ngay sau đó ô sự kiện hiện thêm "R2 NHẬN cảnh báo → CHẶN", "R1 NHẬN cảnh báo → CHẶN", chỉ cách R3 vài mili giây.
> - Link R1 → R2 tụt từ 10 Mbit/s về gần 0. RTT tăng vọt đúng 1 giây rồi trở về khoảng 2 ms.
> - Đây chính là "cải thiện hiệu năng mạng": rác bị chặn ở cửa vào, cả mạng phía sau thông thoáng lại.

Nếu còn thời gian, chạy `scripts/tmux-demo.sh inband`:
> Lượt này không dùng mạng riêng, cảnh báo đi chung đường và được ưu tiên. Kết quả gần như giống hệt lượt on.

**Nếu demo trực tiếp gặp sự cố:** chuyển ngay sang biểu đồ đã chuẩn bị và nói:
> Đây là kết quả của một lần chạy đầy đủ ba lượt trên chính lab này.

---

## Phần 6. Kết quả đo (2 phút)

### Slide 14 — Bảng kết quả

**Trên slide:**

| Lượt | RTT client | Mất gói | Link R1 → R2 |
|---|---|---|---|
| off | **403 ms** | 0% | **10 Mbit/s** |
| on | **6,9 ms** | 0% | **0,18 Mbit/s** |
| inband | **7,2 ms** | 0% | **0,19 Mbit/s** |

- R3 phát hiện sau khoảng 0,5–0,6 giây.
- R1 chặn khoảng 5 ms sau khi R3 phát hiện.
- Chỉ IP của attacker bị chặn trên cả ba router.

**Lời nói:**
> Số liệu là trung bình từ lúc bị tấn công tới hết lượt. Không hợp tác, RTT gấp hơn 100 lần bình thường và link bị chiếm toàn bộ. Có hợp tác, lưu lượng link giảm khoảng 98%, RTT giảm khoảng 98%. Con số 6,9 ms cao hơn 2 ms vì tính cả giây đầu tiên trước khi kịp phát hiện.
>
> Client không mất gói ở cả ba lượt vì hàng đợi giới hạn theo byte: gói rác lớn bị vứt, còn truy vấn nhỏ vẫn vào được hàng nhưng phải chờ khoảng 400 ms. Với ứng dụng thật như gọi điện hay game, trễ 400 ms đã là không dùng được.

### Slide 15 — Biểu đồ

**Trên slide:** [results/eve-v2/rtt.png](results/eve-v2/rtt.png) và [results/eve-v2/link.png](results/eve-v2/link.png).

**Lời nói:**
> Biểu đồ cho thấy rõ: đường off nằm ở 400 ms và 10 Mbit/s tới hết lượt, còn hai đường on và inband chỉ nhô lên đúng một giây rồi về lại mức bình thường.

### Slide 16 — Kiểm chứng QoS

**Trên slide:**

| Khi đường đang nghẽn | RTT |
|---|---|
| Truy vấn thường | ~400 ms |
| Truy vấn đánh dấu ưu tiên | ~2–3 ms |

Bộ đếm `tc` trên R1: làn ưu tiên vứt **0** gói, làn thường vứt ~56.000 gói.

**Lời nói:**
> Ở lượt inband, cảnh báo đi ngược chiều với rác nên chiều đó không nghẽn. Vì vậy em đo riêng để chứng minh QoS có tác dụng khi đường thật sự nghẽn: cho attacker làm nghẽn đường, không bật guard, rồi gửi truy vấn thường và truy vấn có dấu ưu tiên trên cùng con đường. Truy vấn có dấu chỉ mất vài mili giây thay vì 400. Gói cảnh báo được đánh dấu giống hệt, nên vẫn tới nơi ngay cả khi đường nghẽn.

---

## Phần 7. Hạn chế, hướng phát triển, kết luận (2 phút)

### Slide 17 — Hạn chế và hướng phát triển

**Trên slide:**

| Hạn chế | Hướng phát triển |
|---|---|
| Cảnh báo chưa xác thực | Ký HMAC + thời điểm gửi |
| Không chống IP giả mạo | Lọc cổng vào theo BCP 38 |
| Chỉ 1 attacker | Nhiều attacker, nhiều nhánh mạng |
| Chặn vĩnh viễn | Tự gỡ chặn sau TTL |
| QoS tin dấu do người gửi đặt | Trust boundary ở router cửa vào |

**Lời nói:**
> Hệ thống hiện có một số giới hạn. Quan trọng nhất là cảnh báo chưa được xác thực: ai gửi được gói `BLOCK` tới cổng 9999 đều có thể khiến mạng chặn nhầm. Hướng xử lý là ký cảnh báo bằng HMAC. Thứ hai, phát hiện dựa trên IP nguồn nên chưa chống được giả mạo địa chỉ. Ngoài ra, các số liệu đo trong lab ảo, nên con số tuyệt đối sẽ khác mạng thật, nhưng xu hướng so sánh giữa các phương án vẫn có giá trị.

### Slide 18 — Kết luận

**Trên slide:**
- Chặn đơn lẻ gần server: bảo vệ server, **không** bảo vệ mạng.
- Chia sẻ một quyết định chặn giữa các router: mạng hồi phục trong khoảng 1 giây.
- Cảnh báo chỉ vài chục byte, lan truyền trong vài mili giây, đi chung đường vẫn được nhờ QoS.

**Lời nói:**
> Kết luận lại, cả ba lượt đều bảo vệ được server, nhưng chỉ khi các router chia sẻ quyết định chặn thì đường truyền mới được giải phóng và người dùng thật mới không bị ảnh hưởng. Toàn bộ hệ thống, từ mã nguồn, cấu hình mạng đến script đo đạc, đều tái hiện được bằng script. Em xin cảm ơn thầy/cô đã lắng nghe, em sẵn sàng nhận câu hỏi.

---

## Phần 8. Chuẩn bị hỏi đáp

| Câu hỏi có thể gặp | Ý trả lời |
|---|---|
| Sao không chặn ở R1 từ đầu? | R1 không biết lưu lượng nào xấu; R1 có thể thuộc nhà mạng, không biết sức chịu tải của server. Với DDoS, mỗi nguồn qua R1 gửi ít, chỉ khi dồn về gần nạn nhân mới lộ. |
| Cải thiện hiệu năng ở đâu? | RTT client 403 → ~2 ms; link R1 → R2 10 → 0,18 Mbit/s. |
| Sao trễ mà không mất gói? | Hàng đợi giới hạn theo byte (500 KB); truy vấn nhỏ vẫn vào được, chờ ~400 ms. |
| Sao giới hạn 10 Mbit/s? | Mô phỏng nút cổ chai; link ảo quá nhanh sẽ không thấy nghẽn. |
| Ngưỡng 200 gói/s chọn thế nào? | Cách xa client thật (20 gói/s) để không chặn nhầm, thấp hơn nhiều so với attacker (5000 gói/s). Kèm whitelist. |
| Tại sao R3 phát hiện mất ~0,5 giây? | Guard tổng kết theo chu kỳ 1 giây, nên phát hiện xảy ra ở cuối chu kỳ đang chạy khi tấn công bắt đầu. |
| `AF_PACKET` vẫn thấy gói sau khi đã chặn? | Đúng, raw socket bắt gói trước iptables; `blocklist` đảm bảo không chặn và không gửi cảnh báo lặp lại. |
| Router ở xa nhau thì sao nối chung switch? | Đó là lý do có lượt inband. Ngoài thực tế: mạng quản lý out-of-band, VPN, hoặc BGP FlowSpec. |
| Sao không dùng QoS để bảo vệ luôn client? | Dấu ưu tiên chỉ dành cho gói của hệ thống; nếu ai cũng tự đánh dấu được thì attacker cũng làm vậy. Chặn vẫn là giải pháp gốc. |
| Kẻ xấu giả cảnh báo? | Hạn chế số 1. Whitelist chỉ bảo vệ vài IP cố định. Hướng sửa: HMAC + timestamp chống phát lại. |
| Attacker tự đánh dấu EF? | Chen được làn ưu tiên. Cần trust boundary: R1 xóa DSCP trên gói từ ngoài vào. |
| R3 có phải là server không? | Không, R3 là router/firewall riêng đứng trước server, thuộc tổ chức sở hữu server; R1 thường do bên khác quản lý. |
| Sao dùng `fork + execvp` thay `system()`? | Không đi qua shell nên không thể chèn lệnh qua chuỗi IP. |
| Thời điểm 5 ms đo chính xác không? | Mốc thời gian gán khi log về máy chạy `demo.sh` qua SSH (đồng hồ các node lệch nhau), nên chỉ phản ánh bậc độ lớn vài ms. |
| Kiểm thử thế nào? | 25 ca unit test cho 6 module (`make test`); 4 chương trình chính kiểm tra bằng chạy trên mô hình. |
| Có gặp khó khăn gì khi làm? | `pkill` của BusyBox trên Alpine khác Ubuntu → đổi sang `killall`; script đọc MAC để đặt IP quản lý cho node; đồng hồ các node lệch → gán lại thời điểm log tại máy điều khiển. |

**Mẹo khi trả lời:**
- Câu nào liên quan hạn chế thì chủ động thừa nhận và nêu ngay hướng xử lý.
- Câu hỏi về code thì mở đúng file, chỉ đúng dòng (xem mục 4 của [KIEN-THUC-DO-AN.md](KIEN-THUC-DO-AN.md)).
- Câu hỏi về số liệu thì mở [results/eve-v2-report/](results/eve-v2-report/) (log sự kiện, bảng iptables, kết quả qos-check).
