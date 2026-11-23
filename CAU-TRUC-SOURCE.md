# Cấu trúc mã nguồn `src/`

Tóm lại: **4 chương trình**, mỗi chương trình là một file có hàm `main()`. Ngoài ra có **6 module dùng chung** mà 4 chương trình đó gọi tới.

- Mục 1–4: đọc hiểu code (file nào làm gì, gọi nhau thế nào).
- Mục 5: mô hình mạng và cấu hình (IP, route, QoS, cổng, tham số từng lượt).

---

## 1. Toàn cảnh: chương trình nào chạy ở đâu

```
                         ┌──────────────── mạng dữ liệu ─────────────────┐
  ┌──────────┐                                                            ┌──────────┐
  │ Attacker │  attacker.c ─── flood "Q..." ──▶                           │  Server  │
  └──────────┘                                    R1 ── R2 ── R3 ───────▶ │ server.c │
  ┌──────────┐                                    │     │     │           └──────────┘
  │  Client  │  client.c ──── "Q seq ts" ─────▶   │     │     │   ◀── "A seq ts" trả lời
  └──────────┘                                    │     │     │
                                               guard.c  guard.c  guard.c
                                               (nghe)   (nghe)   (phát hiện + gửi cảnh báo)
                                                  ▲     ▲     │
                                                  └─────┴─────┘  "BLOCK 10.0.1.10 R3"
```

| Chương trình | File | Chạy ở node | Một câu mô tả |
|---|---|---|---|
| `server` | [src/server.c](src/server.c) | Server | Nhận `Q <seq> <ts>`, trả lại `A <seq> <ts>` |
| `client` | [src/client.c](src/client.c) | Client | Gửi 20 truy vấn/giây, đo RTT và % mất gói |
| `attacker` | [src/attacker.c](src/attacker.c) | Attacker | Flood 5000 gói/giây × 1000 byte |
| `guard` | [src/guard.c](src/guard.c) | R1, R2, R3 | Phát hiện IP xấu, chặn bằng iptables, gửi/nhận cảnh báo |

---

## 2. Chương trình nào dùng module nào

```
  server.c ───┐
  client.c ───┼──▶ proto       (gói Q/A, cổng, hằng 0xB8)  ← cả 4 chương trình dùng
  attacker.c ─┤
  guard.c ────┘

  client.c ──────▶ stats       (tính RTT, % mất gói)

  guard.c ───────┬──▶ ratecount   (đếm gói theo IP)
                 ├──▶ blocklist   (đã chặn / whitelist)
                 ├──▶ alert       (gói BLOCK <ip> <node>)
                 └──▶ firewall ──▶ lệnh iptables
```

| | proto | stats | ratecount | blocklist | alert | firewall |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `server.c` | ✔ | | | | | |
| `client.c` | ✔ | ✔ | | | | |
| `attacker.c` | ✔ | | | | | |
| `guard.c` | ✔ | | ✔ | ✔ | ✔ | ✔ |

**4 trong 6 module chỉ phục vụ `guard`**, vì `guard` là phần trọng tâm của đồ án.

---

## 3. Từng file làm gì

Mỗi module gồm 2 file: `.h` khai báo "có những hàm gì" (giống interface), `.c` viết phần thân hàm.

### 3.1. Bốn chương trình

#### `server.c` — máy chủ bị tấn công
- Mở socket UDP cổng 9000, bộ đệm nhận 4 MB để chịu flood.
- Vòng lặp: `poll()` → đọc tới 1000 gói → gói nào hợp lệ là `Q` thì trả lời `A`.
- Mỗi giây in số gói nhận được, tách theo IP nguồn.

#### `client.c` — người dùng thật
- Gửi `Q <seq> <thời điểm>` đều đặn 20 gói/giây.
- Nhận `A`, nhờ `stats` tính RTT.
- Mỗi giây in và ghi CSV: `t, gửi, nhận, % mất, RTT trung bình`.
- Cờ `-Q`: đánh dấu gói ưu tiên (TOS `0xB8`), chỉ dùng để kiểm chứng QoS.

#### `attacker.c` — kẻ tấn công
- Gói bắt đầu bằng `Q` giống truy vấn thật, phần sau đệm `xxx...` cho đủ 1000 byte.
- Mỗi vòng tính số gói lẽ ra đã phải gửi tới lúc này, gửi bù phần còn thiếu, rồi ngủ 1 ms. Nhờ vậy giữ đúng 5000 gói/giây.

#### `guard.c` — chương trình trên router (trọng tâm)
Một vòng lặp `poll()` chờ cùng lúc 2 nguồn:

```
                    ┌────────────── vòng lặp poll() mỗi 50 ms ──────────────┐
                    │                                                         │
  raw socket ──────▶│ handle_packet(): gói UDP tới cổng 9000? → rc_add(IP)   │  (ratecount)
  (AF_PACKET)       │                                                         │
                    │                                                         │
  socket cảnh báo ─▶│ handle_alert(): alert_parse → bl_allowed_to_block      │  (alert, blocklist)
  (UDP 9999)        │                 → bl_add → fw_block                     │  (firewall)
                    │                                                         │
  mỗi 1 giây ──────▶│ check_rates(): rc_over(>200 gói/s)                      │  (ratecount)
                    │   → bl_allowed_to_block → bl_add → fw_block             │  (blocklist, firewall)
                    │   → send_alerts() gửi "BLOCK ip R3" tới các peer        │  (alert)
                    └─────────────────────────────────────────────────────────┘
  Ctrl+C ──────────▶ fw_cleanup(): xóa sạch rule iptables rồi thoát             (firewall)
```

Cùng một file, chạy với tham số khác nhau thì đóng vai trò khác nhau:

| Router | Tham số | Vai trò |
|---|---|---|
| R3 | `-d -i eth1 -P <R1> -P <R2>` (+ `-Q` ở lượt inband) | Phát hiện + chặn + gửi cảnh báo |
| R1, R2 | `-l -b <ip>` | Nghe cảnh báo + chặn |

### 3.2. Sáu module dùng chung

| Module | Hàm chính | Tác dụng |
|---|---|---|
| **proto** ([.h](src/proto.h) / [.c](src/proto.c)) | `proto_format`, `proto_parse`, `now_us` | "Ngôn ngữ chung" của truy vấn: tạo và đọc gói `Q`/`A`. Chứa hằng số cổng 9000 (truy vấn), 9999 (cảnh báo), `TOS_PRIORITY = 0xB8` |
| **stats** ([.h](src/stats.h) / [.c](src/stats.c)) | `stats_on_send`, `stats_on_reply`, `stats_tick` | Sổ ghi của client: bảng vòng 4096 ô lưu "gói số mấy gửi lúc nào" để tính RTT. Quá 1 giây chưa có trả lời thì tính là mất |
| **ratecount** ([.h](src/ratecount.h) / [.c](src/ratecount.c)) | `rc_add`, `rc_over`, `rc_reset` | Bộ đếm của guard: mỗi IP gửi bao nhiêu gói trong giây này, IP nào vượt ngưỡng |
| **blocklist** ([.h](src/blocklist.h) / [.c](src/blocklist.c)) | `bl_add`, `bl_allowed_to_block`, `bl_whitelist` | Trí nhớ của guard: IP nào đã chặn (để không chặn trùng), IP nào cấm chặn (whitelist + mạng điều khiển 10.0.99.0/24) |
| **alert** ([.h](src/alert.h) / [.c](src/alert.c)) | `alert_format`, `alert_parse` | "Ngôn ngữ chung" của cảnh báo: tạo và kiểm tra chặt gói `BLOCK <ip> <node>` |
| **firewall** ([.h](src/firewall.h) / [.c](src/firewall.c)) | `fw_init`, `fw_block`, `fw_cleanup` | Tay chân của guard: gọi `iptables` bằng `fork` + `execvp` để tạo chain GUARD, chặn IP, dọn dẹp |

---

## 4. Một gói tấn công đi qua code như thế nào (lượt có hợp tác)

```
attacker.c                 gửi "Q 1 0 xxxxx..." 5000 lần/giây
    │
    ▼
R3: guard.c  handle_packet()         đọc header IP: UDP, cổng 9000, IP nguồn 10.0.1.10
    │        └─ ratecount: rc_add()  đếm +1 cho 10.0.1.10
    │
    ▼  (hết 1 giây)
R3: guard.c  check_rates()
    │        ├─ ratecount: rc_over()            10.0.1.10 gửi 400 gói/s > 200 → xấu
    │        ├─ blocklist: bl_allowed_to_block() không nằm trong whitelist → được chặn
    │        ├─ blocklist: bl_add()             chưa chặn lần nào → ghi nhớ
    │        ├─ firewall:  fw_block()           iptables -A GUARD -s 10.0.1.10 -j DROP
    │        └─ send_alerts() + alert: alert_format()  gửi "BLOCK 10.0.1.10 R3" tới R1, R2
    │
    ▼  (vài mili giây sau)
R1: guard.c  handle_alert()
             ├─ alert:     alert_parse()        đúng định dạng, IP hợp lệ
             ├─ blocklist: bl_allowed_to_block()
             ├─ blocklist: bl_add()
             └─ firewall:  fw_block()           R1 chặn 10.0.1.10 ngay ở cửa vào
```

Từ lúc này gói của attacker bị vứt ngay ở R1, link R1 → R2 → R3 thông thoáng trở lại.

---

## 5. Mô hình mạng và cấu hình

### 5.1. Sơ đồ có ghi tên card mạng

```
                    LAN1 10.0.1.0/24          R1R2 10.0.12.0/24        R2R3 10.0.23.0/24       R3SRV 10.0.3.0/24
 ┌──────────┐ eth1                   eth1┌────┐eth2      eth1┌────┐eth2      eth1┌────┐eth2      eth1┌────────┐
 │ Attacker ├──.10──┐            ┌──.1──┤ R1 ├──.1──══════──.2──┤ R2 ├──.2──══════──.3──┤ R3 ├──.1──────.10──┤ Server │
 └──────────┘       ├── switch ──┘      └─┬──┘   10 Mbit/s     └─┬──┘   10 Mbit/s     └─┬──┘                └────────┘
 ┌──────────┐ eth1  │                     │eth3                   │eth3                  │eth3
 │  Client  ├──.20──┘                     .1                      .2                     .3
 └──────────┘                             └───────────── CTRL 10.0.99.0/24 ──────────────┘
                                                    (mạng điều khiển, chỉ dùng ở lượt on)

 Mọi node còn có eth0 nối mạng quản lý MGMT 172.30.0.0/24 (không vẽ), để máy EVE SSH vào điều khiển.
```

**Đọc sơ đồ:**
- Đi từ trái sang phải là chiều của **truy vấn và rác**: Attacker/Client → R1 → R2 → R3 → Server.
- Hai đoạn `══════` là **nút cổ chai 10 Mbit/s**. Attacker gửi khoảng 40 Mbit/s, gấp 4 lần, nên tắc ở đây.
- Đường CTRL bên dưới là kênh cảnh báo riêng của lượt **on**. Ở lượt **inband**, cảnh báo đi ngược lại trên chính đường dữ liệu: R3 → R2 → R1.

### 5.2. Bảng IP từng node, từng card mạng

| Node | Card | IP | Thuộc mạng | Ghi chú |
|---|---|---|---|---|
| Attacker | eth1 | 10.0.1.10/24 | LAN1 | gateway 10.0.1.1 (R1) |
| Client | eth1 | 10.0.1.20/24 | LAN1 | gateway 10.0.1.1 (R1) |
| R1 | eth1 | 10.0.1.1/24 | LAN1 | cửa vào, phía attacker/client |
| R1 | eth2 | 10.0.12.1/24 | R1R2 | **nút cổ chai R1 → R2**; IP nghe cảnh báo ở lượt inband |
| R1 | eth3 | 10.0.99.1/24 | CTRL | IP nghe cảnh báo ở lượt on |
| R2 | eth1 | 10.0.12.2/24 | R1R2 | nút cổ chai R2 → R1 (chiều cảnh báo inband) |
| R2 | eth2 | 10.0.23.2/24 | R2R3 | **nút cổ chai R2 → R3**; IP nghe cảnh báo ở lượt inband |
| R2 | eth3 | 10.0.99.2/24 | CTRL | IP nghe cảnh báo ở lượt on |
| R3 | eth1 | 10.0.23.3/24 | R2R3 | **guard bắt gói ở đây**; nút cổ chai R3 → R2 |
| R3 | eth2 | 10.0.3.1/24 | R3SRV | gateway của server |
| R3 | eth3 | 10.0.99.3/24 | CTRL | |
| Server | eth1 | 10.0.3.10/24 | R3SRV | gateway 10.0.3.1 (R3), nghe UDP 9000 |

### 5.3. Bảng các mạng

| Mạng | Dải địa chỉ | Nối những node nào | Dùng để |
|---|---|---|---|
| LAN1 | 10.0.1.0/24 | Attacker, Client, R1 | Mạng người dùng, nơi tấn công xuất phát |
| R1R2 | 10.0.12.0/24 | R1, R2 | Đường dữ liệu, giới hạn 10 Mbit/s |
| R2R3 | 10.0.23.0/24 | R2, R3 | Đường dữ liệu, giới hạn 10 Mbit/s |
| R3SRV | 10.0.3.0/24 | R3, Server | Mạng của server |
| CTRL | 10.0.99.0/24 | R1, R2, R3 | Kênh cảnh báo riêng (lượt on). Guard không bao giờ chặn IP thuộc dải này |
| MGMT | 172.30.0.0/24 | máy EVE (.1) + 6 node | Quản lý, SSH. Không tham gia thí nghiệm |

### 5.4. Bảng định tuyến (route tĩnh)

Mỗi router chỉ tự biết 3 mạng nối trực tiếp với nó. Mạng ở xa phải khai báo tay.

| Node | Đích | Đi qua (next hop) | Ý nghĩa |
|---|---|---|---|
| Attacker, Client | mọi nơi (default) | 10.0.1.1 | Gửi hết cho R1 |
| R1 | 10.0.23.0/24, 10.0.3.0/24 | 10.0.12.2 (R2) | Muốn tới server thì đưa cho R2 |
| R2 | 10.0.1.0/24 | 10.0.12.1 (R1) | Chiều về phía client |
| R2 | 10.0.3.0/24 | 10.0.23.3 (R3) | Chiều tới server |
| R3 | 10.0.1.0/24, 10.0.12.0/24 | 10.0.23.2 (R2) | Trả lời về client đi qua R2 |
| Server | mọi nơi (default) | 10.0.3.1 | Gửi hết cho R3 |

Ba router đều bật `net.ipv4.ip_forward=1` để chuyển tiếp gói.

### 5.5. Nút cổ chai và QoS đặt ở card nào

`tc` chỉ tác động lên gói **đi ra** khỏi một card, nên mỗi chiều của link phải cấu hình ở card phía gửi.

| Router | Card | Chiều | Vì sao cần |
|---|---|---|---|
| R1 | eth2 | R1 → R2 | Chiều tấn công: rác bị nghẽn ở đây đầu tiên |
| R2 | eth2 | R2 → R3 | Chiều tấn công |
| R2 | eth1 | R2 → R1 | Chiều cảnh báo inband (R3 → R2 → **R1**) |
| R3 | eth1 | R3 → R2 | Chiều cảnh báo inband |

Mỗi card trên có cùng cấu hình:

| Thông số | Giá trị | Ý nghĩa |
|---|---|---|
| Tốc độ (`tbf rate`) | 10 Mbit/s | Tạo nút cổ chai |
| Số làn (`prio bands`) | 2 | Làn 1 luôn được gửi trước làn 2 |
| Điều kiện vào làn 1 | byte TOS = `0xB8` (DSCP EF) | Gói cảnh báo inband, truy vấn `client -Q` |
| Làn mặc định | làn 2 | Mọi gói khác, kể cả rác |
| Dung lượng mỗi làn (`bfifo limit`) | 500 000 byte | Đầy thì vứt gói mới; xếp đầy mất khoảng 400 ms để truyền hết |

### 5.6. Cổng UDP và định dạng gói

| Gói | Cổng | Nội dung | Gửi từ → tới |
|---|---|---|---|
| Truy vấn | 9000 | `Q <seq> <thời điểm>` (~20 byte) | Client → Server |
| Rác | 9000 | `Q <seq> 0 xxxx...` (1000 byte) | Attacker → Server |
| Trả lời | cổng của bên gửi | `A <seq> <thời điểm>` | Server → Client |
| Cảnh báo | 9999 | `BLOCK <ip> <node>` | R3 → R1, R2 |

### 5.7. Thông số thí nghiệm

| Thông số | Giá trị | Đặt ở đâu |
|---|---|---|
| Thời gian một lượt | 60 giây | `DURATION` trong `scripts/demo.sh` |
| Bắt đầu tấn công | giây 15 | `ATTACK_AT` |
| Tốc độ client | 20 gói/s | `CLIENT_RATE` |
| Tốc độ attacker | 5000 gói/s × 1000 byte ≈ 40 Mbit/s | `ATTACK_RATE`, `ATTACK_SIZE` |
| Ngưỡng phát hiện | 200 gói/s | `THRESHOLD` (tham số `-t` của guard) |
| Whitelist | 10.0.3.10 (server), 10.0.1.20 (client) | tham số `-W` của guard |

### 5.8. Tham số guard ở từng lượt

| Lượt | R3 | R1 | R2 |
|---|---|---|---|
| **off** | `-d -i eth1 -t 200` | không chạy | không chạy |
| **on** | `-d -i eth1 -t 200 -P 10.0.99.1 -P 10.0.99.2` | `-l -b 10.0.99.1` | `-l -b 10.0.99.2` |
| **inband** | `-d -i eth1 -t 200 -P 10.0.12.1 -P 10.0.23.2 -Q` | `-l -b 10.0.12.1` | `-l -b 10.0.23.2` |

Cả 3 router đều thêm `-W 10.0.3.10 -W 10.0.1.20`. Giữa **on** và **inband** chỉ khác 2 chỗ: IP nhận cảnh báo (mạng CTRL hay mạng dữ liệu), và cờ `-Q` để đánh dấu ưu tiên.

### 5.9. Vì sao mô hình được thiết kế như vậy

| Lựa chọn | Lý do |
|---|---|
| 3 router xếp thẳng hàng | Đủ để thấy khác biệt giữa chặn **ở cửa vào** (R1) và chặn **gần server** (R3). R2 ở giữa làm rõ là rác chiếm **nhiều** link chứ không chỉ một |
| Attacker và client chung LAN1 | Hai bên đi chung đường, nên rác làm nghẽn thì client chịu ảnh hưởng. Đó chính là điều cần chứng minh |
| R3 làm nhiệm vụ phát hiện | Mọi lưu lượng tới server đều đi qua R3, nên R3 thấy rõ nhất ai đang dồn truy vấn |
| Giới hạn 10 Mbit/s | Card ảo quá nhanh, không giới hạn thì không thấy nghẽn |
| Hàng đợi giới hạn theo byte | Gói rác lớn bị vứt, truy vấn nhỏ vẫn vào được nhưng phải chờ ~400 ms. Vì vậy client **trễ** nhưng không **mất gói** |
| Mạng CTRL riêng (lượt on) | Kênh cảnh báo không bị flood ảnh hưởng, giống mạng quản lý của nhà mạng |
| Không dùng CTRL (lượt inband) | Giống thực tế hơn khi các router ở xa nhau, dùng QoS để cảnh báo không bị kẹt |
| `eth0` luôn là MGMT | Mạng quản lý tách hẳn khỏi thí nghiệm, SSH điều khiển không ảnh hưởng số đo |

---

## 6. Câu trả lời ngắn khi được hỏi "sao nhiều file vậy?"

> 4 file có `main` là 4 chương trình. 6 module còn lại là các phần dùng chung, chủ yếu phục vụ `guard`. Tách ra để không viết lặp code (cả 4 chương trình cùng dùng `proto`), để `guard.c` chỉ còn luồng chính dễ đọc, và để kiểm thử được từng phần riêng.
