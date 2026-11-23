# Kiến thức cốt lõi của đồ án

**Đề tài:** Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu.

File này gom lại những gì cần nắm để tự trình bày và trả lời câu hỏi: tư tưởng, khái niệm, mô hình, code quan trọng, kết quả. Muốn đọc giải thích khái niệm chi tiết hơn thì xem [CONCEPTS.md](CONCEPTS.md), cách chạy xem [README.md](README.md).

---

## 1. Tư tưởng đồ án

### 1.1. Vấn đề

- Kẻ tấn công gửi dồn dập truy vấn rác (UDP flood) tới server.
- Cách phản ứng thường gặp: chặn ở router **gần server** (R3). Server được bảo vệ.
- Nhưng rác đã đi hết đường R1 → R2 → R3 trước khi bị chặn. Các link trên đường đi vẫn đầy rác, người dùng thật đi chung đường vẫn bị chậm.

> Chặn gần nạn nhân bảo vệ được **server**, nhưng không bảo vệ được **mạng**.

### 1.2. Mâu thuẫn cần giải quyết

| | Ở gần server (R3) | Ở cửa vào (R1) |
|---|---|---|
| Biết ai là kẻ tấn công? | **Có**: thấy rõ ai đang dồn truy vấn vào server | **Không**: thấy lưu lượng đi nhiều nơi, không biết cái nào xấu |
| Chặn ở đây có giải phóng mạng? | **Không**: rác đã đi hết đường | **Có**: rác bị vứt trước khi vào nút cổ chai |

**Nơi phát hiện tốt nhất và nơi chặn tốt nhất không trùng nhau.**

### 1.3. Lời giải: các node cộng tác

R3 phát hiện → tự chặn → **gửi cảnh báo** `BLOCK <ip> R3` cho R1, R2 → R1 chặn ngay ở cửa vào → mạng thông thoáng lại.

Thông tin cần chia sẻ chỉ là một gói tin vài chục byte, mất vài mili giây.

### 1.4. Ba lượt thử nghiệm để chứng minh

| Lượt | Mô tả | Vai trò |
|---|---|---|
| **off** | Chỉ R3 tự chặn, không hợp tác | Mốc so sánh |
| **on** | R3 gửi cảnh báo qua **mạng điều khiển riêng** 10.0.99.0/24 | Hợp tác, kênh cảnh báo tách khỏi đường bị flood |
| **inband** | R3 gửi cảnh báo **chung đường dữ liệu** R3 → R2 → R1, gói được **đánh dấu ưu tiên (QoS)** | Hợp tác, giống thực tế hơn (router ở xa nhau, không có switch chung) |

---

## 2. Khái niệm cần biết

### 2.1. Mạng cơ bản

| Khái niệm | Hiểu ngắn gọn |
|---|---|
| IP, subnet `/24` | Địa chỉ của node; `10.0.1.0/24` = 256 địa chỉ `10.0.1.0` → `10.0.1.255` |
| UDP | Gửi "bắn rồi quên", không bắt tay, không gửi lại. Dễ dùng để flood. Đồ án dùng UDP |
| Port | Phân biệt chương trình: truy vấn cổng **9000**, cảnh báo cổng **9999** |
| Router, `ip_forward` | Máy Linux bật `ip_forward=1` là chuyển tiếp gói được |
| Route tĩnh | "Muốn tới mạng X thì đi qua Y", ví dụ R1: `10.0.3.0/24 via 10.0.12.2` |

### 2.2. Đo hiệu năng

| Chỉ số | Ý nghĩa trong đồ án |
|---|---|
| **RTT** | Thời gian gửi truy vấn → nhận trả lời. **Thước đo chính** của trải nghiệm người dùng |
| **Throughput** | Lưu lượng thực tế trên link R1 → R2 (Mbit/s). Cho thấy rác có còn chiếm đường không |
| **Packet loss** | % truy vấn quá 1 giây không có trả lời |
| **Nút cổ chai** | Link R1–R2, R2–R3 bị giới hạn 10 Mbit/s bằng `tc` để mô phỏng link yếu |
| **Hàng đợi** | Gói tới nhanh hơn link truyền được thì phải xếp hàng → trễ. Đầy thì vứt → mất gói |

**Vì sao client trễ ~400 ms mà không mất gói?** Hàng đợi giới hạn theo **byte** (500 KB). Gói rác 1000 byte bị vứt khi hàng gần đầy, còn truy vấn của client chỉ vài chục byte nên vẫn chen vào được, nhưng phải chờ cả hàng 500 KB truyền hết ở 10 Mbit/s ≈ 400 ms.

### 2.3. Tấn công

| Khái niệm | Trong đồ án |
|---|---|
| DoS / DDoS | Làm quá tải để người dùng thật không dùng được. Đồ án mô phỏng **1** máy tấn công |
| UDP flood | 5000 gói/s × 1000 byte ≈ **40 Mbit/s**, gấp 4 lần nút cổ chai |
| Truy vấn xấu | Gói rác cũng bắt đầu bằng `Q` như truy vấn thật → **không phân biệt được bằng nội dung**, phải phân biệt bằng **hành vi** (tần suất) |

### 2.4. Phát hiện và chặn

| Khái niệm | Trong đồ án |
|---|---|
| Phát hiện theo ngưỡng | Đếm gói/giây theo IP nguồn, vượt **200 gói/s** thì coi là tấn công (client thật chỉ 20 gói/s) |
| False positive | Chặn nhầm người dùng thật. Tránh bằng ngưỡng cách xa + **whitelist** (server, client, mạng điều khiển) |
| iptables, chain | Tường lửa Linux. Đồ án tạo chain riêng `GUARD` gắn vào `FORWARD` (gói đi xuyên router) |
| Raw socket `AF_PACKET` | Đọc **mọi gói** đi qua một card mạng, kể cả gói không gửi cho mình |

### 2.5. Cộng tác và QoS — trọng tâm

| Khái niệm | Ý nghĩa |
|---|---|
| **Collaborative defense** | Các node chia sẻ thông tin kẻ tấn công thay vì mỗi node tự lo |
| **Edge / upstream filtering** | Chặn ở node gần nguồn tấn công nhất (R1) → không tốn băng thông phía sau |
| **Control plane / data plane** | Data plane chở dữ liệu thật; control plane chở thông tin điều khiển (cảnh báo) |
| **Out-of-band** (lượt on) | Cảnh báo đi mạng riêng, không bị flood ảnh hưởng |
| **In-band** (lượt inband) | Cảnh báo đi chung đường dữ liệu → cần QoS để không kẹt sau rác |
| **QoS, DSCP EF, TOS `0xB8`** | Đánh dấu gói ưu tiên trong header IP. DSCP EF = 46, dịch trái 2 bit = `0xB8`. Router đưa gói có dấu vào **làn ưu tiên**, luôn được gửi trước |
| **Trust boundary** | Router cửa vào xóa dấu ưu tiên của gói từ ngoài vào, để kẻ tấn công không tự đánh dấu. Đồ án **chưa** làm |

### 2.6. Ngoài thực tế

- **RTBH** (Remotely Triggered Black Hole): ra lệnh từ xa để router biên vứt lưu lượng tới địa chỉ bị tấn công.
- **BGP FlowSpec**: router của nhà mạng trao đổi quy tắc lọc chi tiết và tự áp dụng.
- **BCP 38**: router cửa vào loại gói có IP nguồn giả.

Đồ án là phiên bản thu nhỏ của cùng ý tưởng: **đưa thông tin từ nơi thấy tới nơi chặn hiệu quả nhất.**

---

## 3. Mô hình mạng

```
 Attacker 10.0.1.10 ─┐
                     ├─ R1 ══10Mbit══ R2 ══10Mbit══ R3 ── Server 10.0.3.10
 Client   10.0.1.20 ─┘   │             │              │
                         └──── mạng điều khiển 10.0.99.0/24 ────┘
```

### 3.1. Các node

| Node | IP dữ liệu | IP điều khiển | Vai trò |
|---|---|---|---|
| Attacker | 10.0.1.10 | | Chạy `attacker`, flood UDP |
| Client | 10.0.1.20 | | Chạy `client`, người dùng thật, đo RTT |
| R1 | 10.0.1.1, 10.0.12.1 | 10.0.99.1 | Router cửa vào, **nghe cảnh báo** |
| R2 | 10.0.12.2, 10.0.23.2 | 10.0.99.2 | Router giữa, **nghe cảnh báo** |
| R3 | 10.0.23.3, 10.0.3.1 | 10.0.99.3 | Router gần server, **phát hiện + gửi cảnh báo** |
| Server | 10.0.3.10 | | Chạy `server`, trả lời truy vấn cổng 9000 |

Mỗi node còn có `eth0` thuộc mạng quản lý MGMT 172.30.0.0/24 để script SSH vào điều khiển. `eth1` trở đi là mạng dữ liệu.

### 3.2. Đường đi của gói

| Loại gói | Đường đi | Ghi chú |
|---|---|---|
| Truy vấn client | Client → R1 → R2 → R3 → Server | Chung đường với rác |
| Rác attacker | Attacker → R1 → R2 → R3 → Server | Làm nghẽn link R1→R2, R2→R3 |
| Cảnh báo lượt on | R3 → switch 10.0.99.0/24 → R1, R2 | Đường riêng |
| Cảnh báo lượt inband | R3 → R2 (10.0.23.2), R3 → R2 → R1 (10.0.12.1) | Ngược chiều rác, có dấu EF |

### 3.3. Hàng đợi 2 làn trên link giữa router

```
                 ┌──────────── tbf: giới hạn 10 Mbit/s ────────────┐
 gói đi ra  ──▶  │  prio ─┬─ làn 1 (TOS 0xB8)  bfifo 500KB  ─▶ ưu tiên│ ──▶ dây
                 │        └─ làn 2 (mọi gói khác) bfifo 500KB        │
                 └──────────────────────────────────────────────────┘
```

- `tbf`: giới hạn tốc độ → tạo nút cổ chai.
- `prio bands 2`: 2 làn, làn 1 luôn được gửi trước, làn 2 chỉ được gửi khi làn 1 trống.
- `priomap 1 1 ... 1`: mặc định mọi gói vào làn 2.
- `u32 match ip dsfield 0xb8 0xfc`: gói có DSCP = EF vào làn 1.

### 3.4. Môi trường

- **EVE-NG** Community chạy trong máy ảo (KVM trên Ubuntu hoặc VMware trên Windows), 6 node **Alpine Linux** (nhẹ, 256MB RAM/node) → ảo hóa lồng nhau.
- Chương trình C biên dịch **tĩnh** (`gcc -static`) một lần, chép thẳng sang node, không cần cài gì thêm.
- **Dự phòng:** cùng mô hình dựng bằng **network namespace** + veth trên một máy Linux (`lab/netns-up.sh`).

---

## 4. Code quan trọng

### 4.1. Bản đồ mã nguồn

| File | Vai trò |
|---|---|
| [src/guard.c](src/guard.c) | **Trái tim của đồ án**: phát hiện, chặn, gửi/nhận cảnh báo. Chạy trên R1, R2, R3 |
| [src/ratecount.c](src/ratecount.c) | Đếm gói theo IP nguồn trong 1 giây |
| [src/blocklist.c](src/blocklist.c) | Danh sách đã chặn + whitelist, không bao giờ chặn mạng điều khiển |
| [src/alert.c](src/alert.c) | Tạo / kiểm tra gói cảnh báo `BLOCK <ip> <node>` |
| [src/firewall.c](src/firewall.c) | Gọi `iptables` qua `fork` + `execvp` |
| [src/proto.c](src/proto.c) | Giao thức truy vấn `Q <seq> <ts>` / trả lời `A <seq> <ts>` |
| [src/stats.c](src/stats.c) | Client tính RTT và mất gói bằng bảng vòng 4096 ô |
| [src/server.c](src/server.c), [src/client.c](src/client.c), [src/attacker.c](src/attacker.c) | 3 chương trình còn lại |
| [lab/r1.sh](lab/r1.sh), [lab/r2.sh](lab/r2.sh), [lab/r3.sh](lab/r3.sh) | IP, route, `tc` (nút cổ chai + QoS) của từng router |
| [scripts/demo.sh](scripts/demo.sh) | Chạy một lượt off / on / inband, thu số liệu |
| [scripts/qos-check.sh](scripts/qos-check.sh) | Chứng minh làn ưu tiên hoạt động |
| [scripts/node-run.sh](scripts/node-run.sh) | Chạy lệnh trên node (SSH với EVE, `ip netns exec` với netns) |

### 4.2. Vòng lặp chính của guard — [src/guard.c:331-386](src/guard.c#L331-L386)

Một luồng duy nhất, dùng `poll()` chờ 2 socket cùng lúc (raw socket bắt gói + socket cảnh báo), mỗi giây kiểm tra ngưỡng một lần.

```c
while (!stop) {
    // pfd gồm raw_fd (nếu -d) và alert_fd (nếu -l)
    int r = poll(pfd, (nfds_t)nfds, 50);            // chờ tối đa 50 ms

    if (r > 0 && raw_idx >= 0 && (pfd[raw_idx].revents & POLLIN)) {
        // đọc tối đa 2000 gói
        if (from.sll_pkttype == PACKET_OUTGOING) {  // bỏ gói chính mình gửi ra
            continue;
        }
        handle_packet(pkt, n);                      // đếm theo IP nguồn
    }
    if (r > 0 && alert_idx >= 0 && (pfd[alert_idx].revents & POLLIN)) {
        handle_alert();                             // nhận cảnh báo → chặn
    }
    if (now >= next_tick) {                         // mỗi 1 giây
        check_rates(threshold);                     // vượt ngưỡng → chặn + cảnh báo
    }
}
fw_cleanup();                                       // Ctrl+C → xóa sạch rule
```

### 4.3. Bắt và đếm gói — [src/guard.c:141-164](src/guard.c#L141-L164)

Đọc thẳng các byte của header IP/UDP:

```c
if ((pkt[0] >> 4) != 4) { return; }                 // byte 0, 4 bit cao = version → chỉ IPv4
int ihl = (pkt[0] & 0x0F) * 4;                       // 4 bit thấp = độ dài header (đơn vị 4 byte)
if (pkt[9] != IPPROTO_UDP) { return; }               // byte 9 = protocol
uint16_t dport = (pkt[ihl + 2] << 8) | pkt[ihl + 3]; // cổng đích UDP
if (dport != QUERY_PORT) { return; }                 // chỉ đếm truy vấn cổng 9000
memcpy(&src, pkt + 12, sizeof(src));                 // byte 12-15 = IP nguồn
rc_add(&rc, src);
```

Raw socket mở ở [src/guard.c:299](src/guard.c#L299): `socket(AF_PACKET, SOCK_DGRAM, htons(ETH_P_IP))`. `SOCK_DGRAM` nghĩa là kernel đã bỏ header Ethernet, ta nhận ngay gói IP.

### 4.4. Phát hiện → chặn → cảnh báo — [src/guard.c:108-138](src/guard.c#L108-L138)

```c
int n = rc_over(&rc, threshold, ips, counts, RC_MAX);   // IP nào > 200 gói/s
for (...) {
    if (!bl_allowed_to_block(&bl, ips[i])) { continue; } // whitelist → bỏ qua
    if (bl_add(&bl, ips[i]) == 0) { continue; }          // đã chặn rồi → bỏ qua
    fw_block(ips[i]);                                     // iptables -A GUARD -s ip -j DROP
    if (peer_count > 0) {
        send_alerts(ips[i], ...);                         // gửi "BLOCK ip R3" tới từng peer
    }
}
rc_reset(&rc);                                            // bắt đầu giây mới
```

- Có `-P` (có peer) = chế độ hợp tác. Không có `-P` = lượt off.
- Vì sao "đã chặn rồi" mà vẫn thấy gói? `AF_PACKET` bắt gói **trước** iptables, nên R3 vẫn đếm được gói của attacker dù đã chặn.

### 4.5. Nhận cảnh báo — [src/guard.c:166-196](src/guard.c#L166-L196)

`recvfrom` → `alert_parse` (sai định dạng thì bỏ) → kiểm tra whitelist → `bl_add` (trùng thì bỏ) → `fw_block`. In log `NHẬN cảnh báo từ R3 → CHẶN 10.0.1.10`.

### 4.6. Đánh dấu ưu tiên QoS — [src/guard.c:276-283](src/guard.c#L276-L283)

Chỉ một dòng, khi có cờ `-Q`:

```c
int tos = TOS_PRIORITY;   // 0xB8, định nghĩa ở src/proto.h
setsockopt(alert_fd, IPPROTO_IP, IP_TOS, &tos, sizeof(tos));
```

Mọi gói gửi qua socket này đều mang byte TOS = `0xB8` → router đưa vào làn 1. [src/client.c](src/client.c) có cờ `-Q` tương tự, chỉ dùng trong `qos-check.sh`.

### 4.7. Kiểm tra cảnh báo nhận từ mạng — [src/alert.c:34-80](src/alert.c#L34-L80)

Dữ liệu từ mạng không được tin: phải bắt đầu đúng `BLOCK `, IP phải hợp lệ theo `inet_pton`, tên node chỉ gồm `[A-Za-z0-9_-]`, tối đa 15 ký tự, không có gì thừa phía sau.

### 4.8. Không bao giờ chặn nhầm — [src/blocklist.c:21-34](src/blocklist.c#L21-L34)

```c
uint32_t host = ntohl(ip);
if ((host & 0xFFFFFF00u) == 0x0A006300u) {   // 10.0.99.0/24: mạng điều khiển
    return 0;
}
// + duyệt whitelist (-W)
```

Nếu không có bước này, một cảnh báo giả có thể bắt các router chặn lẫn nhau.

### 4.9. Gọi iptables an toàn — [src/firewall.c:25-59](src/firewall.c#L25-L59)

```c
pid_t pid = fork();
if (pid == 0) {
    execvp(argv[0], argv);   // argv = {"iptables","-A","GUARD","-s",ip,"-j","DROP",NULL}
    _exit(127);
}
waitpid(pid, &status, 0);
```

Không dùng `system("iptables ... " + ip)` vì nối chuỗi rồi chạy qua shell có thể bị **chèn lệnh**. Mỗi tham số là một phần tử riêng nên không thể chèn.

Các bước iptables:
- `fw_init` ([src/firewall.c:61](src/firewall.c#L61)): `-N GUARD`, `-F GUARD`, `-I FORWARD 1 -j GUARD`.
- `fw_block` ([src/firewall.c:81](src/firewall.c#L81)): `-A GUARD -s <ip> -j DROP`.
- `fw_cleanup` ([src/firewall.c:94](src/firewall.c#L94)): gỡ `GUARD` khỏi `FORWARD`, `-F`, `-X` → mạng trở về như cũ.

### 4.10. Client đo RTT — [src/stats.c](src/stats.c)

- Bảng vòng 4096 ô, vị trí = `seq % 4096`.
- Gửi: ghi thời điểm gửi vào ô. Nhận: tìm ô theo `seq`, RTT = bây giờ − lúc gửi.
- Quá 1 giây chưa có trả lời → tính là mất. Trả lời muộn, trùng hoặc `seq` lạ → bỏ qua.
- Dùng đồng hồ **của chính client** (`CLOCK_MONOTONIC`), không phụ thuộc đồng hồ server.

### 4.11. Attacker giữ đúng tốc độ — [src/attacker.c](src/attacker.c)

Mỗi vòng tính "đến giờ này lẽ ra phải gửi bao nhiêu gói" rồi **gửi bù** phần thiếu, sau đó ngủ 1 ms. Nhờ vậy tốc độ trung bình đúng 5000 gói/s dù `nanosleep` không chính xác.

### 4.12. Cấu hình QoS — [lab/r1.sh:8-15](lab/r1.sh#L8-L15)

```sh
tc qdisc add dev "$1" root handle 1: tbf rate 10mbit burst 32kbit latency 400ms
tc qdisc add dev "$1" parent 1:1 handle 10: prio bands 2 priomap 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
tc qdisc add dev "$1" parent 10:1 handle 101: bfifo limit 500000
tc qdisc add dev "$1" parent 10:2 handle 102: bfifo limit 500000
tc filter add dev "$1" parent 10: protocol ip prio 1 u32 match ip dsfield 0xb8 0xfc flowid 10:1
```

Áp lên: R1 `eth2` (R1→R2), R2 `eth2` (R2→R3) và `eth1` (R2→R1), R3 `eth1` (R3→R2).

### 4.13. Ba lượt khác nhau ở đâu — [scripts/demo.sh:62-74](scripts/demo.sh#L62-L74)

```sh
# on: peer là IP mạng điều khiển
guard -n R3 -d -i eth1 -t 200 $WHITE -P 10.0.99.1 -P 10.0.99.2
guard -n R1 -l -b 10.0.99.1 $WHITE

# inband: peer là IP dữ liệu, có -Q
guard -n R3 -d -i eth1 -t 200 $WHITE -P 10.0.12.1 -P 10.0.23.2 -Q
guard -n R1 -l -b 10.0.12.1 $WHITE

# off: R3 không có -P, R1 R2 không chạy guard
guard -n R3 -d -i eth1 -t 200 $WHITE
```

**Cùng một chương trình `guard`, khác tham số → khác vai trò.**

### 4.14. Đo lưu lượng link — [scripts/linkmon.sh](scripts/linkmon.sh)

Mỗi giây đọc `/sys/class/net/eth2/statistics/tx_bytes` trên R1, lấy hiệu so với giây trước.

---

## 5. Kết quả cần nhớ

Trung bình từ lúc bị tấn công (giây 16) tới hết lượt (giây 60), lab EVE-NG:

| Lượt | RTT client | Mất gói | Link R1 → R2 |
|---|---|---|---|
| Bình thường (trước tấn công) | ~2 ms | 0% | rất nhỏ |
| **off** | **403 ms** | 0% | **10 Mbit/s** (đầy rác) |
| **on** | **6,9 ms** (sau 1 giây về ~2 ms) | 0% | **0,18 Mbit/s** |
| **inband** | **7,2 ms** (sau 1 giây về ~2 ms) | 0% | **0,19 Mbit/s** |

- R3 phát hiện **~0,5–0,6 giây** sau khi bắt đầu tấn công (chu kỳ đếm 1 giây).
- R1 chặn **vài ms** (~5 ms) sau khi R3 phát hiện, ở cả on lẫn inband.
- RTT trung bình on/inband > 2 ms vì tính cả giây đầu tiên trước khi kịp phát hiện.
- Log thật ([results/eve-v2-report/events_on.log](results/eve-v2-report/events_on.log)):
  ```
  09:32:57.944 [demo] BẮT ĐẦU TẤN CÔNG
  09:32:58.439 [R3] PHÁT HIỆN 10.0.1.10 (398 gói/s) → CHẶN, gửi cảnh báo tới 10.0.99.1,10.0.99.2
  09:32:58.442 [R2] NHẬN cảnh báo từ R3 → CHẶN 10.0.1.10
  09:32:58.446 [R1] NHẬN cảnh báo từ R3 → CHẶN 10.0.1.10
  ```
- Chỉ IP attacker bị chặn ([results/eve-v2-report/iptables-on.txt](results/eve-v2-report/iptables-on.txt)): `-A GUARD -s 10.0.1.10/32 -j DROP`.

**Kiểm chứng QoS** (đường nghẽn, không bật guard — [results/eve-v2-report/qos-check-eve.txt](results/eve-v2-report/qos-check-eve.txt)):

| Truy vấn | RTT |
|---|---|
| Thường | ~400 ms |
| Đánh dấu ưu tiên (giống gói cảnh báo) | ~2–3 ms |

Bộ đếm `tc` trên R1: làn ưu tiên gửi 100 gói, **0 gói bị vứt**; làn thường vứt ~56.000 gói.

**Unit test:** 25 ca trong 6 bộ ([tests/](tests/)), chạy `make test`, đều đạt.

---

## 6. Hạn chế và hướng phát triển

| Hạn chế | Hướng phát triển |
|---|---|
| Cảnh báo chưa xác thực → có thể giả cảnh báo | Ký HMAC + timestamp chống phát lại |
| Không chống IP giả mạo | Lọc cổng vào theo BCP 38, phát hiện theo hành vi |
| Chỉ 1 attacker | Mở rộng nhiều attacker, nhiều nhánh |
| Chặn vĩnh viễn | Tự gỡ chặn sau TTL |
| Gửi cảnh báo tới mọi router (cấu hình tay) | Lan truyền theo đường đi thực tế của gói |
| Mạng điều khiển lượt on là switch chung | Lượt inband đã giải quyết; thực tế có thể dùng VPN, out-of-band |
| QoS tin dấu ưu tiên do người gửi đặt | Trust boundary: R1 xóa DSCP của gói từ ngoài vào |
| Số liệu đo trong lab ảo | Con số tuyệt đối khác mạng thật, xu hướng so sánh vẫn đúng |

---

## 7. Tự kiểm tra: trả lời được những câu này là nắm đồ án

1. Vì sao không chặn ngay ở R1 từ đầu? → R1 không biết ai xấu.
2. "Cải thiện hiệu năng" đo bằng gì? → RTT client và lưu lượng link R1 → R2.
3. Vì sao client trễ mà không mất gói? → hàng đợi giới hạn theo byte.
4. Vì sao phải giới hạn link 10 Mbit/s? → link ảo quá nhanh, không thấy nghẽn.
5. `AF_PACKET` khác socket UDP thường thế nào? → thấy mọi gói qua card mạng, không chỉ gói gửi cho mình.
6. Vì sao bỏ gói `PACKET_OUTGOING`? → không đếm gói chính router gửi ra.
7. Vì sao `fork + execvp` thay vì `system()`? → chống chèn lệnh.
8. `0xB8` từ đâu ra? → DSCP EF = 46, `46 << 2 = 184 = 0xB8`.
9. Lượt inband khác on chỗ nào trong code? → chỉ khác IP của `-P`/`-b` và thêm `-Q`.
10. Nếu kẻ tấn công cũng đánh dấu EF? → chen được làn 1; cần trust boundary.
11. Nếu ai đó gửi `BLOCK 10.0.1.20 X` giả? → client nằm trong whitelist nên không bị chặn, nhưng IP khác thì bị → cần HMAC.
12. Vì sao kết quả inband gần như trùng on? → cảnh báo đi ngược chiều rác, chiều đó không nghẽn; muốn chứng minh QoS phải đo riêng bằng `qos-check.sh`.
