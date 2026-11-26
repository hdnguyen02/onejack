#!/bin/sh
# R3: router phía server. eth1 = đường 1 (tới R2), eth2 = tới Server, eth3 = đường 2 (thẳng tới R1).
# Cách dùng: sh r3.sh [fifo|fqcodel] [1|2]
set -e
QUEUE="${1:-fifo}"
PATHS="${2:-1}"
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
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.23.3/24 dev eth1
ip addr replace 10.0.3.1/24 dev eth2
ip addr replace 10.0.13.3/24 dev eth3
sysctl -qw net.ipv4.ip_forward=1
sysctl -qw net.ipv4.fib_multipath_hash_policy=1

ip route replace 10.0.12.0/24 via 10.0.23.2
if [ "$PATHS" = "2" ]; then
    # Chiều về (server -> client) cũng chia ra hai đường.
    ip route replace 10.0.1.0/24 nexthop via 10.0.23.2 weight 1 nexthop via 10.0.13.1 weight 1
else
    ip route replace 10.0.1.0/24 via 10.0.23.2
fi

link_queue eth1
link_queue eth3
