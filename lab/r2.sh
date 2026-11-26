#!/bin/sh
# R2: router trung gian của đường dài. eth1 = tới R1, eth2 = tới R3.
# Cách dùng: sh r2.sh   (R2 luôn chuyển tiếp giống nhau, tham số nếu có thì bỏ qua)
set -e
LINK_DELAY="${LINK_DELAY:-10ms}"
LINK_RATE="${LINK_RATE:-10mbit}"

# Giống r1.sh: mỗi link độ trễ 10 ms, băng thông 10 Mbit/s.
link() {
    tc qdisc del dev "$1" root 2>/dev/null || true
    tc qdisc add dev "$1" root handle 1: netem delay "$LINK_DELAY"
    tc qdisc add dev "$1" parent 1:1 handle 10: tbf rate "$LINK_RATE" burst 32kbit latency 400ms
}

ip link set lo up
for i in eth1 eth2; do ip link set "$i" up; done
ip addr replace 10.0.12.2/24 dev eth1
ip addr replace 10.0.23.2/24 dev eth2
ip route replace 10.0.1.0/24 via 10.0.12.1
ip route replace 10.0.3.0/24 via 10.0.23.3
sysctl -qw net.ipv4.ip_forward=1

link eth1
link eth2
