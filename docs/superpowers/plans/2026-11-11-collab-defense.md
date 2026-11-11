# Demo cộng tác chặn truy vấn xấu: Kế hoạch triển khai

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng một lab EVE-NG có 6 node Linux. Trong đó, các router chạy chương trình C `guard` để phát hiện flood UDP, rồi gửi cảnh báo cho nhau để chặn kẻ tấn công ngay ở cửa vào. Demo chạy trực tiếp trước lớp thành 2 lượt (không hợp tác / có hợp tác) và so sánh số liệu.

**Architecture:** Bốn chương trình C biên dịch tĩnh trên host: `server`, `client`, `attacker`, `guard`. Các phần logic thuần (giao thức, đếm tốc độ, danh sách chặn, gói cảnh báo, thống kê) tách thành module riêng để unit test trên host. Trước khi đưa lên EVE-NG, toàn bộ hệ thống được chạy thử trên host bằng **network namespace** có cùng topology. Cách này giúp test end-to-end và chỉnh số liệu sớm, đồng thời làm phương án dự phòng nếu EVE-NG gặp trục trặc. Cuối cùng các binary được đẩy vào lab EVE-NG, và mọi thao tác điều khiển (bật lab, chạy demo, reset) đều qua script trên host dùng SSH.

**Tech Stack:** C11 (gcc, chỉ dùng libc và socket Linux), GNU make, bash, iproute2 (`ip`, `tc`), iptables, tmux, gnuplot. EVE-NG Community chạy trên KVM/libvirt. Node dùng Alpine Linux.

**Spec:** `docs/superpowers/specs/2026-11-11-collab-defense-design.md`

## Global Constraints

- Ngôn ngữ C11, chạy trên Linux, không dùng thư viện ngoài. Build bằng `gcc -static` (`-O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE`). Không dùng `getaddrinfo`/`gethostbyname` (để binary tĩnh chạy được trên Alpine), chỉ dùng `inet_pton`/`inet_ntop`.
- Style code: **luôn có `{ }`** cho if/for/while, kể cả khi thân chỉ có 1 dòng (theo style cá nhân của người dùng). Viết đơn giản, dễ đọc, comment tiếng Việt ở những đoạn quan trọng.
- Cổng truy vấn: UDP **9000**. Cổng cảnh báo: UDP **9999**.
- Định dạng truy vấn `Q <seq> <timestamp_us>`, trả lời `A <seq> <timestamp_us>`, cảnh báo `BLOCK <ip> <tên_node>`.
- Thông số mặc định: client 20 gói/s, attacker 5000 gói/s × 1000 byte, ngưỡng phát hiện 200 gói/s, nút cổ chai `tc` 10 Mbit/s trên link R1→R2 và R2→R3.
- Địa chỉ: Attacker 10.0.1.10, Client 10.0.1.20, R1 10.0.1.1 / 10.0.12.1, R2 10.0.12.2 / 10.0.23.2, R3 10.0.23.3 / 10.0.3.1, Server 10.0.3.10. Mạng điều khiển: R1 10.0.99.1, R2 10.0.99.2, R3 10.0.99.3.
- Kịch bản mỗi lượt: 60 giây, attacker bắt đầu ở giây thứ 15.
- Máy ảo EVE-NG: 4 vCPU, **6GB RAM**, đĩa 60GB, CPU `host-passthrough`. Mỗi node Alpine 256MB.
- Lệnh cần `sudo` trên host: Claude đưa lệnh, người dùng tự chạy bằng `! <lệnh>`. Các lệnh còn lại Claude tự chạy.
- Thư mục `onejack` không phải git repo, nên **bỏ qua mọi bước commit**. Nếu người dùng muốn dùng git thì `git init` ở Task 1.

## Review Focus

1. **Còn rule iptables hoặc tiến trình sót lại từ lượt trước** (guard bị kill -9, hoặc chạy lượt 2 ngay sau lượt 1): lượt sau phải bắt đầu sạch. → `guard` dùng chain riêng `GUARD`, khi khởi động thì flush chain này. `reset.sh` kill tiến trình và xóa chain. Test nằm ở Task 4 và Task 5.
2. **Cảnh báo sai định dạng hoặc chứa chuỗi độc hại** (ví dụ `BLOCK 1.2.3.4;rm -rf /`): không được chặn bừa, không được chạy lệnh shell. → `alert_parse` kiểm tra IP bằng `inet_pton`, firewall gọi `execvp` chứ không dùng `system()`. Test ở Task 3.
3. **Không bao giờ được chặn IP của chính mạng điều khiển hoặc của server** (dù cảnh báo có gửi tới). → `guard` từ chối chặn IP trong 10.0.99.0/24 và IP truyền qua `-W` (whitelist). Test ở Task 3.
4. **Trả lời tới muộn** (sau 1 giây timeout) hoặc trả lời bị lặp: client không được đếm hai lần, và % mất gói không được vượt 100. Test ở Task 2.
5. **Bảng đếm theo IP bị đầy** (có nhiều IP nguồn): không crash, IP mới bị bỏ qua. Test ở Task 3.

---

## File Structure

```
onejack/
  Makefile                      build 4 binary tĩnh vào build/, `make test` chạy unit test
  src/proto.{c,h}               định dạng/parse truy vấn và trả lời, hàm now_us()
  src/stats.{c,h}               thống kê theo giây của client (gửi/nhận/mất/RTT)
  src/ratecount.{c,h}           đếm số gói theo IP nguồn trong 1 giây
  src/blocklist.{c,h}           tập IP đã chặn + whitelist + kiểm tra mạng điều khiển
  src/alert.{c,h}               định dạng/parse gói cảnh báo BLOCK
  src/firewall.{c,h}            gọi iptables qua execvp (chain GUARD), có chế độ dry-run
  src/server.c src/client.c src/attacker.c src/guard.c   các chương trình chính
  tests/test_*.c                unit test bằng assert, mỗi file một module
  lab/nodes.conf                tên node → IP quản lý (SSH) và interface
  lab/r1.sh r2.sh r3.sh server.sh client.sh attacker.sh   cấu hình IP/route/tc cho từng node
  lab/netns-up.sh netns-down.sh dựng/xóa topology bằng network namespace trên host
  scripts/node-run.sh           chạy một lệnh trên node (backend: netns hoặc ssh)
  scripts/lab-up.sh             cấu hình mọi node + health check → "SẴN SÀNG"
  scripts/demo.sh               `demo.sh off|on`: chạy một lượt 60s, thu CSV về results/
  scripts/reset.sh              dừng mọi tiến trình, xóa chain GUARD
  scripts/linkmon.sh            ghi byte/s của một interface mỗi giây ra CSV
  scripts/tmux-demo.sh          màn hình chia ô cho buổi trình bày
  scripts/plot.sh               vẽ PNG + in bảng tóm tắt từ CSV
  results/                      CSV/PNG của hai lượt
  README.md                     hướng dẫn đầy đủ + checklist trước giờ trình bày
```

Định dạng CSV:
- `client_<mode>.csv`: `t,sent,recv,loss_pct,rtt_avg_ms`
- `link_<mode>.csv`: `t,bytes_per_s`
- `events_<mode>.log`: các dòng log của guard có kèm thời gian (để tính thời gian từ lúc tấn công tới lúc R1 chặn)

---

### Task 0: Cài EVE-NG trên KVM (chạy song song với Task 1–5)

Task này chủ yếu là chờ tải file, nên chạy trước và để tải ngầm trong lúc viết code.

**Files:** không có. Ghi lại các bước đã chạy để đưa vào README ở Task 8.

- [ ] **Step 1:** Người dùng chạy: `! sudo apt-get update && sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients virtinst virt-manager bridge-utils tmux gnuplot sshpass`, sau đó `! sudo usermod -aG libvirt,kvm $USER` (cần đăng xuất rồi đăng nhập lại, hoặc dùng `sg libvirt`).
- [ ] **Step 2:** Tải ISO EVE-NG Community bản mới nhất (dựa trên Ubuntu 22.04) từ trang chính thức eve-ng.net vào `~/Downloads/`. Nếu link tải cần thao tác trên trình duyệt thì hướng dẫn người dùng tự tải. Kiểm tra: dung lượng file đúng như trang công bố.
- [ ] **Step 3:** Người dùng chạy `! sudo virt-install --name eve-ng --memory 6144 --vcpus 4 --cpu host-passthrough --disk size=60,format=qcow2 --cdrom ~/Downloads/<iso> --network network=default --os-variant ubuntu22.04 --graphics vnc`. Sau đó cài theo trình hướng dẫn của ISO (qua virt-manager). Ghi lại mật khẩu root của EVE.
- [ ] **Step 4:** Lấy IP của máy ảo EVE bằng `virsh -c qemu:///system domifaddr eve-ng`. Copy SSH key của host vào EVE (`ssh-copy-id root@<ip>`, người dùng nhập mật khẩu).
- [ ] **Step 5 (kiểm tra):** `ssh root@<eve-ip> 'grep -c vmx /proc/cpuinfo; ls /dev/kvm'` trả về số > 0 và `/dev/kvm` tồn tại. Mở `http://<eve-ip>` trên trình duyệt, đăng nhập bằng admin/eve, vào được giao diện.

### Task 1: Khung dự án, Makefile, module giao thức

**Files:**
- Create: `Makefile`, `src/proto.h`, `src/proto.c`, `tests/test_proto.c`

**Interfaces:**
- Produces:
  - `uint64_t now_us(void);` (dùng `CLOCK_MONOTONIC`)
  - `int proto_format(char *buf, size_t cap, char kind, uint32_t seq, uint64_t ts_us);` trả về độ dài, `kind` là `'Q'` hoặc `'A'`
  - `int proto_parse(const char *buf, size_t len, char *kind, uint32_t *seq, uint64_t *ts_us);` trả về 0 nếu hợp lệ, -1 nếu sai
  - `#define QUERY_PORT 9000`, `#define ALERT_PORT 9999`
  - Makefile: target `all` (ra `build/server build/client build/attacker build/guard`), `test` (build và chạy mọi `tests/test_*.c` liên kết với `src/*.c` trừ các file có `main`), `clean`.

- [ ] **Step 1:** Viết `tests/test_proto.c`:
  - `format('Q', 7, 123456)` ra đúng `"Q 7 123456"`, parse lại được đúng kind/seq/ts.
  - Parse thành công khi phía sau có đệm thêm byte (gói attacker 1000 byte: `"Q 1 5"` rồi tới các byte `'x'`).
  - Parse trả về -1 với: `""`, `"Z 1 2"`, `"Q abc 2"`, `"Q 1"`.
- [ ] **Step 2:** Chạy `make test`. Kết quả mong đợi: FAIL (chưa có `proto.c`).
- [ ] **Step 3:** Cài đặt `src/proto.c` (parse bằng `sscanf` có giới hạn độ dài, copy vào buffer có ký tự kết thúc chuỗi trước khi parse) và viết Makefile.
- [ ] **Step 4:** Chạy `make test`. Kết quả mong đợi: `test_proto: OK`.

### Task 2: server, client, attacker

**Files:**
- Create: `src/stats.h`, `src/stats.c`, `tests/test_stats.c`, `src/server.c`, `src/client.c`, `src/attacker.c`

**Interfaces:**
- Consumes: `proto_format`, `proto_parse`, `now_us`, `QUERY_PORT` (Task 1)
- Produces:
  - `struct stats` có bảng vòng 4096 slot theo `seq % 4096` để lưu thời điểm gửi và trạng thái đã nhận
  - `void stats_init(struct stats *s);`
  - `void stats_on_send(struct stats *s, uint32_t seq, uint64_t t_us);`
  - `void stats_on_reply(struct stats *s, uint32_t seq, uint64_t t_us);` bỏ qua nếu trả lời bị lặp, hoặc tới sau timeout 1.000.000 µs
  - `void stats_tick(struct stats *s, uint64_t now, struct stats_row *out);` với `struct stats_row { uint32_t sent, recv; double loss_pct, rtt_avg_ms; }`. Hàm này tổng kết theo giây: truy vấn đã quá 1 giây mà chưa có trả lời thì tính là mất.
  - CLI:
    - `server [-p port]`: mỗi giây in `[server] t=<s> recv=<n> replied=<n> top=<ip>:<n>,...`
    - `client -s <ip> [-p 9000] [-r 20] [-d 60] [-o file.csv]`: mỗi giây in một dòng và ghi một dòng CSV `t,sent,recv,loss_pct,rtt_avg_ms`
    - `attacker -s <ip> [-p 9000] [-r 5000] [-l 1000] [-d 45]`: giữ đúng tốc độ bằng cách gửi theo lô mỗi 1ms

- [ ] **Step 1:** Viết `tests/test_stats.c`:
  - Gửi seq 1..20, nhận cả 20 với RTT 5ms → `sent=20 recv=20 loss_pct=0 rtt_avg_ms≈5.0`.
  - Gửi 10, chỉ nhận 5 → sau khi qua 1 giây timeout thì `loss_pct=50`.
  - Một trả lời tới sau 1.5 giây → không được tính là nhận, `loss_pct=100` cho truy vấn đó.
  - Trả lời bị lặp cho cùng một seq → `recv` chỉ tăng 1.
  - `loss_pct` không bao giờ lớn hơn 100.
- [ ] **Step 2:** Chạy `make test`. Kết quả mong đợi: `test_stats` FAIL.
- [ ] **Step 3:** Cài đặt `src/stats.c`, sau đó viết `server.c`, `client.c` (một socket UDP, dùng `poll` với timeout 1ms, vừa gửi theo nhịp vừa nhận), và `attacker.c`.
- [ ] **Step 4:** Chạy `make test && make`. Kết quả mong đợi: mọi test OK, có đủ 4 binary (`guard.c` lúc này chỉ là stub `main` trả về 0).
- [ ] **Step 5 (thử trên loopback):** Chạy `build/server &`, rồi `build/client -s 127.0.0.1 -d 5 -o /tmp/c.csv`. Kết quả mong đợi: 5 dòng, `loss_pct=0`, RTT dưới 1ms, file CSV có header và 5 dòng dữ liệu. Chạy tiếp `build/attacker -s 127.0.0.1 -d 3`, server phải in `top=127.0.0.1:~5000`.

### Task 3: Các module logic của guard

**Files:**
- Create: `src/ratecount.{c,h}`, `src/blocklist.{c,h}`, `src/alert.{c,h}`, `src/firewall.{c,h}`, `tests/test_ratecount.c`, `tests/test_blocklist.c`, `tests/test_alert.c`, `tests/test_firewall.c`

**Interfaces:**
- Produces:
  - `#define RC_MAX 256`
  - `void rc_init(struct ratecount *rc);`
  - `void rc_add(struct ratecount *rc, uint32_t ip);` (ip theo network byte order). Khi bảng đã đủ `RC_MAX` IP thì IP mới bị bỏ qua.
  - `int rc_over(const struct ratecount *rc, uint32_t threshold, uint32_t *ips, uint32_t *counts, int cap);` trả về số IP có `count > threshold`
  - `void rc_reset(struct ratecount *rc);` (gọi mỗi giây)
  - `void bl_init(struct blocklist *bl);`
  - `int bl_whitelist(struct blocklist *bl, uint32_t ip);`
  - `int bl_allowed_to_block(const struct blocklist *bl, uint32_t ip);` trả về 0 nếu IP thuộc 10.0.99.0/24 hoặc có trong whitelist
  - `int bl_add(struct blocklist *bl, uint32_t ip);` trả về 1 nếu IP mới được thêm, 0 nếu đã có. Tối đa 256 IP.
  - `int alert_format(char *buf, size_t cap, uint32_t ip, const char *node);` ra `"BLOCK 10.0.1.10 R3"`
  - `int alert_parse(const char *buf, size_t len, uint32_t *ip, char *node, size_t node_cap);` trả về 0 hoặc -1. IP phải qua được `inet_pton`, tên node chỉ gồm `[A-Za-z0-9_-]` và dài tối đa 15 ký tự, sau tên node không được còn ký tự nào khác.
  - `void fw_set_dry_run(int on);` (ở chế độ dry-run thì chỉ ghi lại argv vào buffer nội bộ, không thực thi)
  - `const char *fw_last_cmd(void);`
  - `int fw_init(void);` → `iptables -N GUARD` (bỏ qua lỗi nếu chain đã tồn tại), `iptables -F GUARD`, `iptables -C FORWARD -j GUARD || iptables -I FORWARD 1 -j GUARD`
  - `int fw_block(uint32_t ip);` → `iptables -A GUARD -s <ip> -j DROP`
  - `int fw_cleanup(void);` → `-D FORWARD -j GUARD`, `-F GUARD`, `-X GUARD`
  - Mọi lệnh iptables đều chạy bằng `fork` + `execvp("iptables", argv)`, **không dùng `system()`**.

- [ ] **Step 1:** Viết 4 file test:
  - **ratecount:** thêm 300 gói từ A và 20 gói từ B, gọi `rc_over(…,200,…)` → trả về 1 IP là A, count 300. Thêm 300 IP khác nhau → không crash, bảng có đúng 256 IP. Sau `rc_reset` → `rc_over` trả về 0.
  - **blocklist:** `bl_add(A)` → 1, gọi lần nữa → 0. `bl_allowed_to_block(10.0.99.2)` → 0. Sau khi whitelist 10.0.3.10 thì IP này → 0. IP 10.0.1.10 → 1.
  - **alert:** format/parse khớp nhau. Parse trả về -1 với: `"BLOCK 1.2.3.4;rm -rf / R3"`, `"BLOCK 999.1.1.1 R3"`, `"BLOCK 1.2.3.4"`, `"BLOCK 1.2.3.4 R3 extra"`, `"HELLO 1.2.3.4 R3"`, tên node dài 40 ký tự.
  - **firewall (dry-run):** `fw_block(10.0.1.10)` → `fw_last_cmd()` là `"iptables -A GUARD -s 10.0.1.10 -j DROP"`.
- [ ] **Step 2:** Chạy `make test`. Kết quả mong đợi: 4 test mới FAIL.
- [ ] **Step 3:** Cài đặt 4 module. Dùng mảng tĩnh và tìm kiếm tuyến tính (tối đa 256 phần tử, không cần hash).
- [ ] **Step 4:** Chạy `make test`. Kết quả mong đợi: tất cả OK.

### Task 4: Chương trình guard

**Files:**
- Modify: `src/guard.c` (thay phần stub)

**Interfaces:**
- Consumes: mọi module ở Task 3, `ALERT_PORT`, `QUERY_PORT`
- Produces: CLI `guard -n <tên> [-i <iface>] [-d] [-t 200] [-l] [-b <ctrl_ip>] [-P <peer_ip>]... [-W <ip>]...`
  - `-d`: bật phát hiện, bắt gói bằng `AF_PACKET` trên `-i`, đếm gói IPv4/UDP có dport 9000 theo IP nguồn
  - `-l`: nghe cảnh báo trên `<ctrl_ip>:9999`
  - `-P`: danh sách peer để gửi cảnh báo. Có `-P` nghĩa là bật chế độ hợp tác, không có nghĩa là không hợp tác.
  - `-W`: whitelist
  - Log in ra stdout, mỗi dòng flush ngay, định dạng `HH:MM:SS.mmm [<tên>] …`:
    - `PHÁT HIỆN <ip> (<n> gói/s) → CHẶN` kèm `, gửi cảnh báo tới <peer,...>` nếu có peer
    - `NHẬN cảnh báo từ <node> → CHẶN <ip>`
    - `BỎ QUA cảnh báo không hợp lệ` / `BỎ QUA <ip> (whitelist)` / `ĐÃ CHẶN <ip> từ trước`

- [ ] **Step 1:** Cài đặt vòng lặp chính bằng `poll()` trên 2 socket (raw socket nếu có `-d`, UDP nếu có `-l`), cộng một timer mỗi 1 giây để gọi `rc_over` rồi `rc_reset`. Khi khởi động gọi `fw_init()`. Bắt SIGINT/SIGTERM bằng một cờ để thoát vòng lặp rồi gọi `fw_cleanup()`. Nếu chạy không phải root thì báo lỗi rõ ràng và thoát với mã 1.
- [ ] **Step 2 (kiểm tra cơ bản, không cần root):** Chạy `build/guard -n X -d -i lo`. Kết quả mong đợi: in `guard cần quyền root` và thoát với mã 1.
- [ ] **Step 3:** Kiểm tra end-to-end ở Task 5 (cần namespace).

### Task 5: Mini-lab bằng network namespace trên host (test end-to-end và chỉnh số liệu)

**Files:**
- Create: `lab/netns-up.sh`, `lab/netns-down.sh`, `lab/r1.sh`, `lab/r2.sh`, `lab/r3.sh`, `lab/server.sh`, `lab/client.sh`, `lab/attacker.sh`, `lab/nodes.conf`, `scripts/node-run.sh`, `scripts/linkmon.sh`, `scripts/reset.sh`, `scripts/demo.sh`

**Interfaces:**
- Consumes: 4 binary ở `build/`
- Produces:
  - Mỗi file `lab/<node>.sh` nhận tên interface làm tham số (để EVE và netns dùng chung): đặt IP, route mặc định / route tĩnh, `sysctl net.ipv4.ip_forward=1` trên router, `tc qdisc replace dev <if> root tbf rate 10mbit burst 32kbit latency 400ms` trên R1 (hướng R2) và R2 (hướng R3)
  - `scripts/node-run.sh <node> <lệnh…>`: backend chọn qua biến `LAB=netns|eve`. Với netns thì chạy `ip netns exec <node> …`, với eve thì `ssh root@<mgmt_ip từ nodes.conf> …`
  - `scripts/demo.sh off|on`: chạy reset → bật server → bật guard (R3 có `-d`, ở chế độ `on` thì R3 có thêm `-P 10.0.99.1 -P 10.0.99.2`, đồng thời R1/R2 chạy `-l`) → bật linkmon trên interface R1 hướng R2 → bật client 60s → `sleep 15` → bật attacker 45s → chờ xong → thu `results/client_<mode>.csv`, `results/link_<mode>.csv`, `results/events_<mode>.log`
  - Interface của R3 nối với R2 dùng làm `-i` cho phát hiện. Whitelist `-W 10.0.3.10 -W 10.0.1.20` trên mọi guard.

- [ ] **Step 1:** Viết `netns-up.sh`: tạo 6 namespace, các cặp veth theo topology, một bridge cho LAN1 (attacker + client + R1) và một bridge cho mạng điều khiển (R1/R2/R3), rồi gọi `lab/<node>.sh` bên trong từng namespace. Viết thêm `netns-down.sh` để xóa sạch.
- [ ] **Step 2:** Người dùng chạy `! sudo lab/netns-up.sh`. Kiểm tra: `! sudo ip netns exec client ping -c2 10.0.3.10` thông, `! sudo ip netns exec r1 ping -c2 10.0.99.3` thông.
- [ ] **Step 3:** Người dùng chạy `! sudo LAB=netns scripts/demo.sh off`. Kết quả mong đợi: trong `events_off.log` có dòng R3 `PHÁT HIỆN 10.0.1.10`. Trong `client_off.csv`, các giây 15–60 có `loss_pct` hoặc `rtt_avg_ms` cao hơn hẳn mức nền. Trong `link_off.csv`, các giây 15–60 có giá trị khoảng 1,2MB/s (bão hòa 10Mbit).
- [ ] **Step 4:** Người dùng chạy `! sudo LAB=netns scripts/demo.sh on`. Kết quả mong đợi: trong `events_on.log` có R1 `NHẬN cảnh báo từ R3 → CHẶN 10.0.1.10` trong vòng 2 giây sau khi tấn công bắt đầu. Sau thời điểm đó, `client_on.csv` trở về mức nền và `link_on.csv` giảm về mức nền.
- [ ] **Step 5 (Review Focus 1):** Chạy `demo.sh on` hai lần liên tiếp mà không reset bằng tay. Kết quả mong đợi: lần thứ hai cho kết quả giống lần đầu, và `! sudo ip netns exec r1 iptables -S GUARD` sau khi xong thì không còn rule nào sót lại.
- [ ] **Step 6 (chỉnh số liệu):** Nếu hai lượt chưa khác nhau rõ ràng (độ trễ trung bình của client trong giai đoạn tấn công chênh dưới 5 lần), chỉnh tốc độ attacker / `tc` / `latency` của tbf, rồi ghi các con số cuối cùng vào đầu file `scripts/demo.sh` dưới dạng biến.

### Task 6: Dựng lab trong EVE-NG

**Files:**
- Modify: `lab/nodes.conf` (điền IP quản lý thật và tên interface của EVE)

**Interfaces:**
- Consumes: Task 0 (EVE đã chạy), các file `lab/<node>.sh` và `build/*` từ Task 5
- Produces: 6 node Alpine, mỗi node có `eth0` nối Management (Cloud0) để nhận IP DHCP từ mạng libvirt, nhờ đó host SSH vào được. Data interfaces nối đúng theo topology trong spec. Có thêm một network "CTRL" cho R1/R2/R3.

- [ ] **Step 1:** Tạo image `linux-alpine-demo`: tải ISO Alpine "virt" vào thư mục `/opt/unetlab/addons/qemu/linux-alpine-demo/` trên EVE, tạo một node tạm, chạy `setup-alpine` (bật sshd, cho root đăng nhập bằng key), cài `iproute2 iptables tcpdump`, rồi `qemu-img commit` vào `virtioa.qcow2` và chạy `/opt/unetlab/wrappers/unl_wrapper -a fixpermissions`. Mình hướng dẫn các thao tác trên web UI, người dùng làm theo.
- [ ] **Step 2:** Tạo lab `collab-defense` trên web UI: 6 node từ image vừa tạo, mỗi node 256MB, nối dây theo topology, rồi khởi động. Xuất file lab ra `lab/collab-defense.unl` (copy từ `/opt/unetlab/labs/` trên EVE).
- [ ] **Step 3:** Điền `lab/nodes.conf`, đẩy key SSH vào từng node, rồi `scp` các file `build/*` và `lab/<node>.sh` vào `/root/` của mỗi node.
- [ ] **Step 4 (kiểm tra):** Chạy `LAB=eve scripts/node-run.sh client ping -c2 10.0.3.10` và `LAB=eve scripts/node-run.sh r1 ping -c2 10.0.99.3`. Cả hai đều thông.

### Task 7: Điều phối buổi demo trực tiếp

**Files:**
- Create: `scripts/lab-up.sh`, `scripts/tmux-demo.sh`, `scripts/plot.sh`

**Interfaces:**
- Consumes: `node-run.sh`, `demo.sh`, `reset.sh`, `linkmon.sh`
- Produces:
  - `scripts/lab-up.sh`: chạy `lab/<node>.sh` trên từng node, sau đó health check gồm: client ping server, R1 ping 10.0.99.3, `build/client -d 3` nhận đủ, và RAM trống trên host (`free`) ≥ 1GB. Nếu đạt thì in `SẴN SÀNG`, nếu không thì in `LỖI: <bước nào>` và thoát với mã 1.
  - `scripts/tmux-demo.sh off|on`: mở tmux 4 ô, gồm log client, log guard R3, log guard R1, lưu lượng link R1→R2. Ô thứ 5 (hoặc cửa sổ chính) chạy `demo.sh <mode>`.
  - `scripts/plot.sh`: từ `results/*.csv` vẽ ra `results/rtt.png`, `results/loss.png`, `results/link.png` (mỗi hình có 2 đường off/on, có vạch dọc ở giây 15). In ra bảng tóm tắt gồm RTT trung bình, % mất gói, byte/s trung bình trên link trong giây 15–60 của từng lượt, và thời gian tới lúc R1 chặn.

- [ ] **Step 1:** Viết 3 script.
- [ ] **Step 2 (kiểm tra trên EVE):** Chạy lần lượt `scripts/lab-up.sh`, `scripts/tmux-demo.sh off`, `scripts/tmux-demo.sh on`, `scripts/plot.sh`. Kết quả mong đợi: in `SẴN SÀNG`, các ô tmux cập nhật mỗi giây, ra 3 file PNG, và bảng cho thấy lượt `on` có RTT và % mất gói thấp hơn hẳn lượt `off`.
- [ ] **Step 3:** Chỉnh lại số liệu trên EVE nếu cần (giống Task 5 Step 6). Môi trường EVE chậm hơn netns, nên có thể phải hạ tốc độ attacker xuống.

### Task 8: README, kết quả, phương án dự phòng

**Files:**
- Create: `README.md`, `results/` (CSV, PNG của lần chạy tốt nhất)

- [ ] **Step 1:** Viết `README.md` bằng tiếng Việt, gồm: giới thiệu ý tưởng, sơ đồ topology, cài EVE-NG (các lệnh thật đã chạy ở Task 0), tạo image Alpine, dựng lab, build, chạy demo, giải thích từng chương trình C (dành cho người dùng đọc trước khi trình bày), hạn chế và hướng phát triển (xác thực cảnh báo, IP giả mạo, tự gỡ chặn sau một thời gian), và cuối cùng là **checklist trước giờ trình bày**: tắt app nặng, `virsh start eve-ng` sớm 10 phút, start lab, chạy `scripts/lab-up.sh`, tập chạy `tmux-demo.sh off` một lần.
- [ ] **Step 2:** Người dùng quay màn hình hai lượt chạy thành công (gợi ý dùng `! sudo apt-get install -y simplescreenrecorder` hoặc công cụ có sẵn của Ubuntu là Ctrl+Shift+Alt+R). Lưu video vào `results/`.
- [ ] **Step 3 (kiểm tra cuối):** Tắt hết rồi làm lại đúng theo checklist trong README từ đầu, chạy lại cả hai lượt, và kiểm tra bảng tóm tắt lặp lại được kết quả.
- [ ] **Step 4:** Nếu đến cuối ngày thứ 3 mà EVE-NG vẫn chưa ổn thì báo người dùng. Phương án dự phòng là demo bằng netns (Task 5) trên chính host, kèm video.
