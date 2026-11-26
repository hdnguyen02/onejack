#!/bin/sh
# R3: router phía server. eth1 = đường dài (tới R2), eth2 = tới Server, eth3 = đường ngắn (thẳng tới R1).
# Cách dùng: sh r3.sh [long|short|balance]   (chiều về server -> client, giống r1.sh)
set -e
ROUTE="${1:-long}"
LINK_DELAY="${LINK_DELAY:-10ms}"
LINK_RATE="${LINK_RATE:-10mbit}"

# Giống r1.sh: mỗi link độ trễ 10 ms, băng thông 10 Mbit/s.
link() {
    tc qdisc del dev "$1" root 2>/dev/null || true
    tc qdisc add dev "$1" root handle 1: netem delay "$LINK_DELAY"
    tc qdisc add dev "$1" parent 1:1 handle 10: tbf rate "$LINK_RATE" burst 32kbit latency 400ms
}

ip link set lo up
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.23.3/24 dev eth1
ip addr replace 10.0.3.1/24 dev eth2
ip addr replace 10.0.13.3/24 dev eth3
sysctl -qw net.ipv4.ip_forward=1
sysctl -qw net.ipv4.fib_multipath_hash_policy=1

ip route replace 10.0.12.0/24 via 10.0.23.2
if [ "$ROUTE" = "short" ]; then
    ip route replace 10.0.1.0/24 via 10.0.13.1
elif [ "$ROUTE" = "balance" ]; then
    ip route replace 10.0.1.0/24 nexthop via 10.0.23.2 weight 1 nexthop via 10.0.13.1 weight 1
else
    ip route replace 10.0.1.0/24 via 10.0.23.2
fi

link eth1
link eth3
