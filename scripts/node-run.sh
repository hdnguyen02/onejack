#!/bin/bash
# Chạy một lệnh trên một node của lab.
#   LAB=netns (mặc định): chạy trong network namespace trên host (cần root)
#   LAB=eve             : SSH vào node EVE-NG theo IP trong lab/nodes.conf
# Cách dùng: node-run.sh <node> <lệnh...>
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LAB="${LAB:-netns}"
node="$1"
shift

if [ "$LAB" = "netns" ]; then
    exec ip netns exec "$node" sh -c "$*"
fi

ip=$(awk -v n="$node" '$1 == n { print $2 }' "$ROOT/lab/nodes.conf")
if [ -z "$ip" ] || [ "$ip" = "0.0.0.0" ]; then
    echo "node-run: chưa có IP quản lý cho '$node' trong lab/nodes.conf" >&2
    exit 1
fi
exec ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR "root@$ip" "$*"
