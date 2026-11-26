#!/bin/bash
# Dựng topology giống hệt lab EVE-NG bằng network namespace trên host (cần root).
# Tên interface trong mỗi namespace giống EVE (eth1, eth2, eth3) để dùng chung lab/<node>.sh.
set -e
cd "$(dirname "$0")"
NODES="loadgen client r1 r2 r3 server"

for n in $NODES sw; do
    ip netns add "$n"
done

# Namespace "sw" chứa switch LAN1 (loadgen, client, R1).
ip netns exec sw ip link add br-lan1 type bridge
ip netns exec sw ip link set br-lan1 up

# Nối một interface của node vào switch.
plug() {   # plug <node> <ifname> <bridge>
    local peer="p-$1-$2"
    ip link add "$2" netns "$1" type veth peer name "$peer" netns sw
    ip netns exec sw ip link set "$peer" master "$3"
    ip netns exec sw ip link set "$peer" up
}

# Nối thẳng hai node với nhau.
wire() {   # wire <nodeA> <ifA> <nodeB> <ifB>
    ip link add "$2" netns "$1" type veth peer name "$4" netns "$3"
}

plug loadgen  eth1 br-lan1
plug client   eth1 br-lan1
plug r1       eth1 br-lan1
wire r1 eth2 r2 eth1
wire r2 eth2 r3 eth1
wire r3 eth2 server eth1
# Đường 2: nối thẳng R1 với R3.
wire r1 eth3 r3 eth3

for n in $NODES; do
    ip netns exec "$n" sh "./$n.sh"
done

echo "netns lab: đã dựng xong ($NODES)"
