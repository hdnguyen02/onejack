#!/bin/bash
# Dừng mọi chương trình đo đạc (server, client, loadgen, linkmon) trên mọi node.
DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$DIR/node-run.sh"
LAB="${LAB:-netns}"
NODES="loadgen client r1 r2 r3 server"

if [ "$LAB" = "netns" ]; then
    # Mini-lab: chỉ dừng tiến trình nằm trong namespace của lab,
    # không dừng nhầm chương trình trùng tên đang chạy trên máy.
    for n in $NODES; do
        for pid in $(ip netns pids "$n" 2>/dev/null); do
            kill "$pid" 2>/dev/null
        done
    done
else
    # EVE-NG: mỗi node là một máy ảo riêng nên dừng theo tên là an toàn.
    # Node Alpine dùng busybox: pkill -x không khớp tên chạy bằng đường dẫn
    # (/root/server), nên dùng killall.
    for n in $NODES; do
        "$RUN" "$n" "killall server client loadgen; pkill -f linkmon.sh" >/dev/null 2>&1
    done
fi
true
