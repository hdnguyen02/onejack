#!/bin/sh
# R2: router giữa của đường 1. eth1 = tới R1, eth2 = tới R3.
# Cách dùng: sh r2.sh [fifo|fqcodel] [1|2]   (tham số 2 không dùng, R2 luôn chỉ có một đường)
set -e
QUEUE="${1:-fifo}"
TC_RATE="${TC_RATE:-10mbit}"

# Giống hệt r1.sh: link giới hạn 10 Mbit/s, hàng đợi fifo hoặc fq_codel.
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
for i in eth1 eth2; do ip link set "$i" up; done
ip addr replace 10.0.12.2/24 dev eth1
ip addr replace 10.0.23.2/24 dev eth2
ip route replace 10.0.1.0/24 via 10.0.12.1
ip route replace 10.0.3.0/24 via 10.0.23.3
sysctl -qw net.ipv4.ip_forward=1

link_queue eth1
link_queue eth2
