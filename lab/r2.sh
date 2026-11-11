#!/bin/sh
# R2: eth1 = tới R1, eth2 = tới R3, eth3 = mạng điều khiển.
set -e
TC_RATE="${TC_RATE:-10mbit}"
ip link set lo up
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.12.2/24 dev eth1
ip addr replace 10.0.23.2/24 dev eth2
ip addr replace 10.0.99.2/24 dev eth3
ip route replace 10.0.1.0/24 via 10.0.12.1
ip route replace 10.0.3.0/24 via 10.0.23.3
sysctl -qw net.ipv4.ip_forward=1
# Nút cổ chai có chủ đích trên link R2 -> R3.
tc qdisc replace dev eth2 root tbf rate "$TC_RATE" burst 32kbit latency 400ms
