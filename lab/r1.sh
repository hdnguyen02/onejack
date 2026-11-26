#!/bin/sh
# R1: router đầu vào. eth1 = LAN1 (client, loadgen), eth2 = đường dài (qua R2), eth3 = đường ngắn (thẳng tới R3).
# Cách dùng: sh r1.sh [long|short|balance]   (mặc định long)
#   long   : mọi gói tới server đi đường dài R1 -> R2 -> R3
#   short  : mọi gói tới server đi đường ngắn R1 -> R3
#   balance: chia các luồng ra cả hai đường
set -e
ROUTE="${1:-long}"
LINK_DELAY="${LINK_DELAY:-10ms}"
LINK_RATE="${LINK_RATE:-10mbit}"

# Mỗi link giữa hai router: độ trễ truyền 10 ms (mô phỏng khoảng cách) và băng thông 10 Mbit/s.
# Hàng đợi chứa tối đa 500KB (khoảng 400 ms ở 10 Mbit/s). Khi lưu lượng vượt 10 Mbit/s,
# gói phải xếp hàng chờ ở đây, đó là nguyên nhân độ trễ tăng khi đường bị tắc nghẽn.
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
# Khi chia tải, chọn đường theo IP + cổng nguồn/đích của từng luồng: các luồng khác nhau
# đi các đường khác nhau, còn gói của cùng một luồng luôn đi cùng một đường.
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
