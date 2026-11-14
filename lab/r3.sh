#!/bin/sh
# R3: eth1 = tới R2 (guard phát hiện trên interface này), eth2 = tới Server, eth3 = mạng điều khiển.
set -e
TC_RATE="${TC_RATE:-10mbit}"
# Nút cổ chai 10 Mbit/s có 2 làn (QoS): gói đánh dấu ưu tiên (TOS 0xB8, DSCP EF)
# đi làn 1 và luôn được gửi trước, mọi gói khác đi làn 2.
# Mỗi làn chứa tối đa 500KB, tức khoảng 400 ms ở 10 Mbit/s.
bottleneck() {
    tc qdisc del dev "$1" root 2>/dev/null || true
    tc qdisc add dev "$1" root handle 1: tbf rate "$TC_RATE" burst 32kbit latency 400ms
    tc qdisc add dev "$1" parent 1:1 handle 10: prio bands 2 priomap 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
    tc qdisc add dev "$1" parent 10:1 handle 101: bfifo limit 500000
    tc qdisc add dev "$1" parent 10:2 handle 102: bfifo limit 500000
    tc filter add dev "$1" parent 10: protocol ip prio 1 u32 match ip dsfield 0xb8 0xfc flowid 10:1
}
ip link set lo up
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.23.3/24 dev eth1
ip addr replace 10.0.3.1/24 dev eth2
ip addr replace 10.0.99.3/24 dev eth3
ip route replace 10.0.1.0/24 via 10.0.23.2
ip route replace 10.0.12.0/24 via 10.0.23.2
sysctl -qw net.ipv4.ip_forward=1
# Link R3 -> R2: chiều cảnh báo đi chung đường.
bottleneck eth1
