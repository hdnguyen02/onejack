#!/bin/sh
# R1: router đầu vào. eth1 = LAN1 (client, loadgen), eth2 = đường 1 (tới R2), eth3 = đường 2 (thẳng tới R3).
# Cách dùng: sh r1.sh [fifo|fqcodel] [1|2]
#   tham số 1: kiểu hàng đợi trên các link giữa router (mặc định fifo)
#   tham số 2: số đường R1 dùng để tới server (mặc định 1)
set -e
QUEUE="${1:-fifo}"
PATHS="${2:-1}"
TC_RATE="${TC_RATE:-10mbit}"

# Mỗi link giữa hai router giới hạn 10 Mbit/s để tạo đường truyền có băng thông hữu hạn.
#   fifo   : một hàng đợi chung chứa tối đa 500KB (khoảng 400 ms ở 10 Mbit/s), đầy thì vứt gói mới.
#   fqcodel: thay hàng đợi chung bằng fq_codel: chia gói theo từng luồng, gửi xoay vòng giữa các luồng,
#            và chủ động vứt bớt gói khi gói phải chờ quá lâu (mục tiêu 5 ms), nên hàng đợi luôn ngắn.
link_queue() {
    tc qdisc del dev "$1" root 2>/dev/null || true
    if [ "$QUEUE" = "fqcodel" ]; then
        tc qdisc add dev "$1" root handle 1: tbf rate "$TC_RATE" burst 32kbit latency 400ms
        tc qdisc add dev "$1" parent 1:1 handle 10: fq_codel
    else
        tc qdisc add dev "$1" root handle 1: tbf rate "$TC_RATE" burst 32kbit latency 400ms
    fi
}

ip link set lo up
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.1.1/24 dev eth1
ip addr replace 10.0.12.1/24 dev eth2
ip addr replace 10.0.13.1/24 dev eth3
sysctl -qw net.ipv4.ip_forward=1
# Khi có nhiều đường, chọn đường theo IP + cổng nguồn/đích của từng luồng,
# để các luồng khác nhau đi các đường khác nhau, còn gói của cùng một luồng vẫn đi cùng một đường.
sysctl -qw net.ipv4.fib_multipath_hash_policy=1

ip route replace 10.0.23.0/24 via 10.0.12.2
if [ "$PATHS" = "2" ]; then
    # Hai đường cùng chi phí tới mạng server: qua R2 và thẳng tới R3.
    ip route replace 10.0.3.0/24 nexthop via 10.0.12.2 weight 1 nexthop via 10.0.13.3 weight 1
else
    ip route replace 10.0.3.0/24 via 10.0.12.2
fi

link_queue eth2
link_queue eth3
