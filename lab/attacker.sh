#!/bin/sh
# Attacker: eth1 nối LAN1.
set -e
ip link set lo up
ip link set eth1 up
ip addr replace 10.0.1.10/24 dev eth1
ip route replace default via 10.0.1.1
