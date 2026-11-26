#!/bin/bash
# Màn hình demo trực tiếp: chia tmux thành 4 ô cập nhật mỗi giây.
#   ┌──────────────────────────────┬──────────────────────────────┐
#   │ Client: RTT, jitter, mất gói │ Server: thông lượng nhận     │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ R1: Mbit/s trên đường 1, 2   │ demo.sh đang chạy, sự kiện   │
#   └──────────────────────────────┴──────────────────────────────┘
# Cách dùng: tmux-demo.sh base|fqcodel|multipath|combined   (thoát: gõ exit ở ô demo)
set -u
MODE="${1:-}"
if [ "$MODE" = "base" ]; then
    TITLE="LƯỢT BASE: 1 đường, hàng đợi FIFO (mốc so sánh)"
elif [ "$MODE" = "fqcodel" ]; then
    TITLE="LƯỢT FQCODEL: 1 đường, hàng đợi fq_codel (giảm độ trễ)"
elif [ "$MODE" = "multipath" ]; then
    TITLE="LƯỢT MULTIPATH: 2 đường, hàng đợi FIFO (tăng băng thông)"
elif [ "$MODE" = "combined" ]; then
    TITLE="LƯỢT COMBINED: 2 đường + fq_codel"
else
    echo "Cách dùng: $0 base|fqcodel|multipath|combined" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/results"
SESSION="demo-$MODE"
mkdir -p "$OUT"
# Xóa kết quả cũ để các ô không hiện số liệu của lần trước.
rm -f "$OUT"/*_"$MODE".*
touch "$OUT/client_$MODE.log" "$OUT/server_$MODE.csv" "$OUT/link_$MODE.csv"

CLIENT_CMD="echo '== CLIENT: độ trễ (RTT), jitter, mất gói mỗi giây =='; tail -n +1 -F '$OUT/client_$MODE.log' 2>/dev/null"
SERVER_CMD="echo '== SERVER: thông lượng nhận được (tổng của mọi đường) =='; tail -n +1 -F '$OUT/server_$MODE.csv' 2>/dev/null | awk -F, '\$1 ~ /^[0-9]+\$/ { printf \"t=%2d  %6.2f Mbit/s\n\", \$1, \$3; fflush() }'"
LINK_CMD="echo '== R1: lưu lượng ra từng đường (mỗi đường tối đa 10 Mbit/s) =='; tail -n +1 -F '$OUT/link_$MODE.csv' 2>/dev/null | awk -F, '\$1 ~ /^[0-9]+\$/ { printf \"t=%2d  đường 1: %6.2f   đường 2: %6.2f Mbit/s\n\", \$1, \$2 * 8 / 1000000, \$3 * 8 / 1000000; fflush() }'"
DEMO_CMD="echo '$TITLE'; echo; LAB=\${LAB:-eve} '$ROOT/scripts/demo.sh' $MODE; echo; echo 'Xong. Gõ exit để đóng màn hình demo.'; exec bash"

tmux kill-session -t "$SESSION" 2>/dev/null
tmux new-session -d -s "$SESSION" -x "$(tput cols 2>/dev/null || echo 200)" -y "$(tput lines 2>/dev/null || echo 50)" "$CLIENT_CMD"
tmux split-window -h -t "$SESSION" "$SERVER_CMD"
tmux split-window -v -t "$SESSION:0.0" "$LINK_CMD"
tmux split-window -v -t "$SESSION:0.2" "$DEMO_CMD"
tmux select-pane -t "$SESSION:0.3"
if [ -t 1 ]; then
    tmux attach -t "$SESSION"
else
    echo "Đã mở màn hình demo trong tmux, xem bằng: tmux attach -t $SESSION"
fi
