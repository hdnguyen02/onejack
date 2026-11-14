#!/bin/bash
# Màn hình demo trực tiếp: chia tmux thành các ô cập nhật mỗi giây.
#   ┌──────────────────────────────┬──────────────────────────────┐
#   │ Client: RTT, % mất gói       │ Sự kiện: phát hiện, cảnh báo │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ Link R1 -> R2 (Mbit/s)       │ demo.sh <off|on> đang chạy   │
#   └──────────────────────────────┴──────────────────────────────┘
# Cách dùng: tmux-demo.sh off|on|inband   (thoát: Ctrl+B rồi D, hoặc gõ exit ở ô demo)
set -u
MODE="${1:-}"
if [ "$MODE" != "off" ] && [ "$MODE" != "on" ] && [ "$MODE" != "inband" ]; then
    echo "Cách dùng: $0 off|on|inband" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/results"
SESSION="demo-$MODE"
mkdir -p "$OUT"
# Xóa kết quả cũ để các ô không hiện số liệu của lần trước.
rm -f "$OUT"/*_"$MODE".*
touch "$OUT/client_$MODE.log" "$OUT/events_$MODE.log" "$OUT/link_$MODE.csv"

if [ "$MODE" = "on" ]; then
    TITLE="LƯỢT ON: CÓ HỢP TÁC (R3 báo R1, R2 qua mạng điều khiển riêng)"
elif [ "$MODE" = "inband" ]; then
    TITLE="LƯỢT INBAND: CÓ HỢP TÁC (cảnh báo đi chung đường, ưu tiên QoS)"
else
    TITLE="LƯỢT OFF: KHÔNG HỢP TÁC (chỉ R3 tự chặn)"
fi

CLIENT_CMD="echo '== CLIENT: độ trễ (RTT) và mất gói mỗi giây =='; tail -n +1 -F '$OUT/client_$MODE.log' 2>/dev/null"
EVENTS_CMD="echo '== SỰ KIỆN: phát hiện, cảnh báo, chặn =='; tail -n +1 -F '$OUT/events_$MODE.log' 2>/dev/null"
LINK_CMD="echo '== LINK R1 -> R2 (trần 10 Mbit/s) =='; tail -n +1 -F '$OUT/link_$MODE.csv' 2>/dev/null | awk -F, '\$1 ~ /^[0-9]+\$/ { printf \"t=%2d  %6.2f Mbit/s\n\", \$1, \$2 * 8 / 1000000; fflush() }'"
DEMO_CMD="echo '$TITLE'; echo; LAB=\${LAB:-eve} '$ROOT/scripts/demo.sh' $MODE; echo; echo 'Xong. Gõ exit để đóng màn hình demo.'; exec bash"

tmux kill-session -t "$SESSION" 2>/dev/null
tmux new-session -d -s "$SESSION" -x "$(tput cols 2>/dev/null || echo 200)" -y "$(tput lines 2>/dev/null || echo 50)" "$CLIENT_CMD"
tmux split-window -h -t "$SESSION" "$EVENTS_CMD"
tmux split-window -v -t "$SESSION:0.0" "$LINK_CMD"
tmux split-window -v -t "$SESSION:0.2" "$DEMO_CMD"
tmux select-pane -t "$SESSION:0.3"
if [ -t 1 ]; then
    tmux attach -t "$SESSION"
else
    echo "Đã mở màn hình demo trong tmux, xem bằng: tmux attach -t $SESSION"
fi
