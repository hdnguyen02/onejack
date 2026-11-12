#!/bin/bash
# Dừng mọi tiến trình demo trên mọi node và xóa chain iptables GUARD.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/node-run.sh"
LAB="${LAB:-netns}"
NODES="attacker client r1 r2 r3 server"

if [ "$LAB" = "netns" ]; then
    # Mini-lab: chỉ dừng tiến trình nằm trong namespace của lab,
    # không dừng nhầm chương trình trùng tên đang chạy trên máy.
    for n in r1 r2 r3; do
        for pid in $(ip netns pids "$n" 2>/dev/null); do
            if [ "$(cat /proc/"$pid"/comm 2>/dev/null)" = "guard" ]; then
                kill -INT "$pid" 2>/dev/null
            fi
        done
    done
    sleep 1
    for n in $NODES; do
        for pid in $(ip netns pids "$n" 2>/dev/null); do
            kill "$pid" 2>/dev/null
        done
    done
else
    # EVE-NG: mỗi node là một máy ảo riêng nên dừng theo tên là an toàn.
    # Node Alpine dùng busybox: pkill -x không khớp tên chạy bằng đường dẫn
    # (/root/guard), nên dùng killall.
    for n in r1 r2 r3; do
        "$RUN" "$n" "killall -INT guard" >/dev/null 2>&1
    done
    sleep 1
    for n in $NODES; do
        "$RUN" "$n" "killall guard server client attacker; pkill -f linkmon.sh" >/dev/null 2>&1
    done
fi

for n in r1 r2 r3; do
    "$RUN" "$n" "iptables -D FORWARD -j GUARD; iptables -F GUARD; iptables -X GUARD" >/dev/null 2>&1
done
true
