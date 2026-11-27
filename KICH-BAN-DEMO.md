# Kịch bản trình bày và demo

**Đề tài:** Cải thiện hiệu năng mạng: giảm độ trễ bằng cách chọn đường và phân phối tải giữa các router.

**Thời lượng gợi ý:** khoảng 15 phút trình bày và demo, sau đó hỏi đáp.

| Phần | Nội dung | Thời gian |
|---|---|---|
| 1 | Vấn đề: độ trễ và nguyên nhân | 2 phút |
| 2 | Mô hình mạng | 2 phút |
| 3 | Demo 3 lượt: đo trước, đổi cách chọn đường, đo lại | 7 phút |
| 4 | Kết quả và kết luận | 3 phút |
| 5 | Hỏi đáp | tùy giảng viên |

---

## Chuẩn bị (10 phút trước giờ)

- [ ] Bật máy ảo EVE, `ssh root@<EVE_IP>`, `cd /root/onejack`, chạy `scripts/lab-up.sh`, thấy **SẴN SÀNG**.
- [ ] Mở web EVE (`http://<EVE_IP>`), vào lab **net-perf** để chỉ sơ đồ.
- [ ] Phóng to chữ terminal (Ctrl + Shift + +).
- [ ] Mở sẵn biểu đồ trong `results/eve/` (`rtt.png`, `rtt_low.png`, `paths.png`) phòng khi demo trực tiếp gặp sự cố.

---

## Phần 1. Vấn đề (2 phút)

**Nói:**

> Với gọi video, chơi game, điều người dùng cảm nhận rõ nhất là độ trễ: gửi đi bao lâu thì có phản hồi. Độ trễ của một gói tin gồm hai phần chính:
> - **Thời gian đi đường:** đường càng dài, đi qua càng nhiều router thì càng lâu.
> - **Thời gian xếp hàng:** khi lưu lượng vượt băng thông của đường truyền, gói phải chờ trong hàng đợi của router. Phần này có thể lên tới hàng trăm mili giây.
>
> Router chỉ làm hai việc: chọn đường và chuyển tiếp. Đề tài của em giảm độ trễ bằng cách thay đổi **cách router chọn đường**, không thêm thiết bị, không tăng băng thông.

---

## Phần 2. Mô hình mạng (2 phút)

**Chỉ trên web EVE** (lab `net-perf`):

```
               ┌──── R2 ────┐      ← đường dài: 2 đoạn, qua R2
 Client ── R1 ─┤            ├─ R3 ── Server
 Loadgen ──    └────────────┘      ← đường ngắn: 1 đoạn
```

**Nói:**

> - **Client** là người dùng cần phản hồi nhanh, gửi 20 truy vấn nhỏ mỗi giây và đo RTT.
> - **Loadgen** là máy đang tải dữ liệu lớn, gửi 12 Mbit/s chia thành 32 luồng.
> - Giữa R1 và R3 có hai đường. Mỗi đoạn dây có độ trễ 10 ms (giả lập khoảng cách) và băng thông 10 Mbit/s.
> - Tải 12 Mbit/s lớn hơn một đường (10) nhưng nhỏ hơn hai đường cộng lại (20).
>
> Em chạy 3 lượt, chỉ khác cách R1 và R3 chọn đường. Mỗi lượt 60 giây, loadgen bắt đầu tải ở giây 15, nên mỗi lượt có cả lúc mạng rảnh và lúc mạng đông.

---

## Phần 3. Demo (7 phút)

Màn hình demo có 4 ô. Giới thiệu nhanh trước khi chạy:

| Ô | Hiển thị | Chú ý nhìn |
|---|---|---|
| Trên trái | RTT, jitter của client mỗi giây | **Ô quan trọng nhất** |
| Dưới trái | Lưu lượng R1 gửi ra đường dài và đường ngắn | Đường nào đang chở tải |
| Trên phải | Thông lượng server nhận được | Có nhận đủ 12 Mbit/s không |
| Dưới phải | Tiến trình: đường đi đang dùng, lúc bắt đầu tải | |

### Lượt 1: base, mọi lưu lượng đi đường dài (đo trước khi tối ưu)

```
scripts/tmux-demo.sh base
```

**Nói trong lúc chạy:**

> - Trước giây 15: RTT khoảng **44 ms**, đúng bằng 4 lần đi qua đoạn dây 10 ms (đi 2 đoạn, về 2 đoạn).
> - Giây 15 loadgen bắt đầu tải: RTT tăng vọt lên khoảng **450 ms**. Ô dưới trái: đường dài chạy kín 10 Mbit/s, đường ngắn **bỏ trống**. Ô trên phải: server chỉ nhận khoảng 9,6 trên 12 Mbit/s, phần còn lại bị bỏ vì hàng đợi đầy.
> - 400 ms tăng thêm đó chính là thời gian xếp hàng.

Chạy xong gõ `exit`.

### Lượt 2: short, mọi lưu lượng đi đường ngắn

```
scripts/tmux-demo.sh short
```

**Nói:**

> - Trước giây 15: RTT chỉ khoảng **22 ms**, giảm một nửa, vì đường ngắn chỉ có một đoạn dây và không qua R2.
> - Nhưng khi có tải: RTT vẫn lên khoảng **420 ms**. Lý do là 12 Mbit/s vẫn dồn vào một đường 10 Mbit/s. Đường ngắn chỉ tiết kiệm được khoảng 20 ms, quá nhỏ so với 400 ms xếp hàng.
> - Kết luận: **đường ngắn chỉ có lợi khi mạng thông thoáng.**

### Lượt 3: balance, chia tải ra hai đường

```
scripts/tmux-demo.sh balance
```

**Nói:**

> - R1 chia 32 luồng ra hai đường. Ô dưới trái: mỗi đường khoảng **6 Mbit/s**, đều dưới 10, không đường nào bị đầy.
> - Ô trên trái: khi có tải, RTT vẫn khoảng **33 ms**, gần như không đổi so với lúc chưa có tải. So với 456 ms của lượt base là **giảm khoảng 93%**.
> - Ô trên phải: server nhận đủ **12 Mbit/s**, không mất gì.
> - RTT lúc chưa tải khoảng 33 ms, nằm giữa 22 và 44, vì chiều đi và chiều về của client có thể đi hai đường khác nhau.

### Vẽ biểu đồ so sánh

```
scripts/plot.sh
```

Chỉ vào bảng in ra và các biểu đồ `rtt.png`, `rtt_low.png`, `paths.png`.

**Nếu demo trực tiếp gặp sự cố:** chuyển sang biểu đồ có sẵn trong `results/eve/` và nói: *"Đây là kết quả một lần chạy đủ 3 lượt trên chính lab này."*

---

## Phần 4. Kết quả và kết luận (3 phút)

| Lượt | RTT chưa tải | RTT có tải | Server nhận |
|---|---|---|---|
| base: đường dài | 43,9 ms | 455,9 ms | 9,6 / 12 Mbit/s |
| short: đường ngắn | 22,4 ms | 421,6 ms | 9,6 / 12 Mbit/s |
| balance: chia tải | 32,6 ms | 32,9 ms | 12,0 / 12 Mbit/s |

**Nói:**

> Hai cách chọn đường tác động vào hai phần khác nhau của độ trễ:
> - **Đường ngắn** giảm thời gian đi đường, chỉ có tác dụng khi mạng thông thoáng.
> - **Phân phối tải** bỏ được thời gian xếp hàng, là phần lớn nhất khi mạng đông.
>
> Cả hai chỉ cần đổi bảng định tuyến của router, không thêm thiết bị, không tăng băng thông.
>
> Hạn chế: đường đi đang cấu hình tĩnh, router chưa tự biết đường nào đang tắc để đổi. Hướng phát triển là dùng định tuyến động như OSPF, hoặc cho router đo độ trễ từng đường rồi tự chọn.

---

## Phần 5. Câu hỏi có thể gặp

| Câu hỏi | Ý trả lời |
|---|---|
| Độ trễ 10 ms mỗi đoạn dây ở đâu ra? | Giả lập khoảng cách giữa các router bằng `tc netem`. Không có nó, các máy ảo trên cùng laptop chênh nhau chưa tới 1 ms, không đo được khác biệt giữa đường dài và đường ngắn |
| Router chia tải thế nào? | Theo từng luồng: tính hàm băm trên IP và cổng nguồn/đích, mỗi luồng đi một đường cố định nên gói không bị đảo thứ tự (ECMP) |
| Sao loadgen dùng 32 luồng? | Hàm băm chỉ chia đều khi có nhiều luồng. Với 8 luồng từng bị chia lệch 6/2. Mạng thật có rất nhiều luồng nên cũng chia gần đều |
| Sao client không mất gói? | Hàng đợi giới hạn theo byte: gói tải 1000 byte bị bỏ khi đầy, truy vấn nhỏ của client vẫn vào được nhưng phải chờ |
| Sao không chỉ dùng đường ngắn cho tất cả? | Lượt short chứng minh: khi tải vượt một đường thì vẫn tắc, độ trễ vẫn 420 ms |
| Khác gì "tăng công suất thiết bị"? | Không thêm dây, không tăng băng thông, không đổi thiết bị. Hai đường có sẵn từ đầu, chỉ đổi cách router chọn đường |
| Sao dùng UDP mà không dùng TCP? | UDP gửi đúng tốc độ cấu hình nên các lượt có điều kiện giống nhau. TCP tự giảm tốc khi tắc, kết quả khó so sánh. Đây là một hạn chế đã nêu |
| Router cấu hình bằng gì? | Mỗi router một tệp `lab/r1.sh`, đổi lượt chỉ là đổi một dòng `ip route` |
