#!/bin/bash
# Dừng mọi tiến trình demo trên mọi node và xóa chain iptables GUARD.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/node-run.sh"

for n in r1 r2 r3; do
    "$RUN" "$n" "pkill -INT -x guard" >/dev/null 2>&1
done
sleep 1
for n in attacker client r1 r2 r3 server; do
    "$RUN" "$n" "pkill -x guard; pkill -x server; pkill -x client; pkill -x attacker; pkill -f linkmon.sh" >/dev/null 2>&1
done
for n in r1 r2 r3; do
    "$RUN" "$n" "iptables -D FORWARD -j GUARD; iptables -F GUARD; iptables -X GUARD" >/dev/null 2>&1
done
true
