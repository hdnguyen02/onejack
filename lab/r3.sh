#!/bin/sh
# R3: eth1 = tới R2 (guard phát hiện trên interface này), eth2 = tới Server, eth3 = mạng điều khiển.
set -e
ip link set lo up
for i in eth1 eth2 eth3; do ip link set "$i" up; done
ip addr replace 10.0.23.3/24 dev eth1
ip addr replace 10.0.3.1/24 dev eth2
ip addr replace 10.0.99.3/24 dev eth3
ip route replace 10.0.1.0/24 via 10.0.23.2
ip route replace 10.0.12.0/24 via 10.0.23.2
sysctl -qw net.ipv4.ip_forward=1
