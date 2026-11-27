#! PHỤ LỤC

**A. Hướng dẫn chạy thực nghiệm**

Mọi lệnh dưới đây chạy trong máy ảo EVE-NG, thư mục `/root/onejack`. Hướng dẫn cài đặt đầy đủ nằm trong tệp `README.md` của mã nguồn.

```
make && make test                   # build 3 chương trình C và chạy kiểm thử đơn vị
bash lab/eve-make-image.sh          # tạo image Alpine cho node (chạy một lần)
bash lab/eve-create-lab.sh          # tạo lab net-perf 6 node (chạy một lần)
scripts/lab-up.sh                   # chuẩn bị lab, phải in SẴN SÀNG
scripts/tmux-demo.sh base           # mọi lưu lượng đi đường dài
scripts/tmux-demo.sh short          # mọi lưu lượng đi đường ngắn
scripts/tmux-demo.sh balance        # chia tải ra hai đường
scripts/plot.sh                     # bảng tóm tắt và biểu đồ
```

**B. Tệp cấu hình router R1**

Tệp `lab/r1.sh`, chạy trên R1 với tham số là kịch bản chọn đường (trích nguyên văn).

```
#!/bin/sh
# R1: router đầu vào. eth1 = LAN1 (client, loadgen), eth2 = đường dài (qua R2), eth3 = đường ngắn (thẳng tới R3).
# Cách dùng: sh r1.sh [long|short|balance]   (mặc định long)
set -e
ROUTE="${1:-long}"
LINK_DELAY="${LINK_DELAY:-10ms}"
LINK_RATE="${LINK_RATE:-10mbit}"

link() {
    tc qdisc del dev "$1" root 2>/dev/null || true
    tc qdisc add dev "$1" root handle 1: netem delay "$LINK_DELAY"
    tc qdisc add dev "$1" parent 1:1 handle 10: tbf rate "$LINK_RATE" burst 32kbit latency 400ms
}

ip link set lo up
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.1.1/24 dev eth1
ip addr replace 10.0.12.1/24 dev eth2
ip addr replace 10.0.13.1/24 dev eth3
sysctl -qw net.ipv4.ip_forward=1
sysctl -qw net.ipv4.fib_multipath_hash_policy=1

ip route replace 10.0.23.0/24 via 10.0.12.2
if [ "$ROUTE" = "short" ]; then
    ip route replace 10.0.3.0/24 via 10.0.13.3
elif [ "$ROUTE" = "balance" ]; then
    ip route replace 10.0.3.0/24 nexthop via 10.0.12.2 weight 1 nexthop via 10.0.13.3 weight 1
else
    ip route replace 10.0.3.0/24 via 10.0.12.2
fi

link eth2
link eth3
```

**C. Kế hoạch thực hiện**

Bảng: Kế hoạch thực hiện khóa luận
| Thời gian | Công việc | Kết quả |
|---|---|---|
| 11/11 – 14/11/2026 | Cài EVE-NG trên KVM; tạo image Alpine và lab bằng API; viết chương trình đo bằng C và các script điều khiển | Môi trường thử nghiệm và bộ công cụ đo chạy được |
| 26/11/2026 | Điều chỉnh hướng đề tài theo góp ý của giáo viên hướng dẫn: tập trung vào giảm độ trễ bằng cách chọn đường | Mô hình hai đường đi, ba kịch bản thử nghiệm |
| 26/11 – 27/11/2026 | Đo ba kịch bản trên EVE-NG; viết báo cáo | Bộ số liệu dùng trong báo cáo |
| [27/11 – 05/12/2026] | [Hoàn thiện báo cáo theo góp ý của giáo viên hướng dẫn] | [ ] |
| Trước 06/12/2026 | Nộp báo cáo cho giáo viên hướng dẫn | |
| 07/12 – 18/12/2026 | Bộ môn phản biện đánh giá đề tài | |
| 23/12/2026 | Báo cáo trước hội đồng | |

**D. Nhật ký làm việc**

Bảng: Nhật ký làm việc
| Ngày | Nội dung đã làm | Ghi chú |
|---|---|---|
| 11/11/2026 | Viết Makefile, bộ kiểm thử, module giao thức và thống kê; viết server, client; dựng mô hình rút gọn bằng network namespace | |
| 12/11/2026 | Cài KVM và EVE-NG; tạo image Alpine; tạo lab bằng REST API; sửa lỗi lượt thử nghiệm bị treo trên Alpine và lỗi trùng địa chỉ quản lý; viết script chuẩn bị lab, màn hình tmux, vẽ biểu đồ | Lab chạy ổn định trên EVE-NG |
| 26/11/2026 | Đổi mô hình sang hai đường đi; thêm độ trễ truyền cho đường truyền; viết loadgen nhiều luồng; thêm jitter cho client; viết ba kịch bản chọn đường và đo trên EVE-NG | Tăng số luồng tải để chia đều ra hai đường |
| 27/11/2026 | Sửa cách tính trung bình thông lượng; viết lại báo cáo | |
| [...] | [...] | [...] |
