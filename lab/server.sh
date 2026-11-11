#!/bin/sh
# Server: eth1 nối R3.
set -e
ip link set lo up
ip link set eth1 up
ip addr replace 10.0.3.10/24 dev eth1
ip route replace default via 10.0.3.1
