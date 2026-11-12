#!/bin/bash
# Chạy một lượt demo và thu số liệu về results/.
#   demo.sh off : không hợp tác (chỉ R3 tự phát hiện và chặn)
#   demo.sh on  : có hợp tác (R3 phát hiện, báo cho R1/R2 chặn theo)
# Backend chọn bằng biến LAB=netns|eve (xem node-run.sh).
set -u

# ---- Thông số demo (chỉnh ở đây) ----
DURATION=60          # tổng thời gian một lượt (giây)
ATTACK_AT=15         # giây bắt đầu tấn công
CLIENT_RATE=20       # gói/s của client thật
ATTACK_RATE=5000     # gói/s của attacker
ATTACK_SIZE=1000     # byte mỗi gói tấn công
THRESHOLD=200        # ngưỡng phát hiện (gói/s)
# -------------------------------------

MODE="${1:-}"
if [ "$MODE" != "off" ] && [ "$MODE" != "on" ]; then
    echo "Cách dùng: $0 off|on" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/scripts/node-run.sh"
OUT="$ROOT/results"
LAB="${LAB:-netns}"
export LAB
mkdir -p "$OUT"

if [ "$LAB" = "netns" ]; then
    BIN="$ROOT/build"
    LINKMON="$ROOT/scripts/linkmon.sh"
else
    BIN="/root"
    LINKMON="/root/linkmon.sh"
fi

WHITE="-W 10.0.3.10 -W 10.0.1.20"
EVENTS="$OUT/events_$MODE.log"

stamp() {
    date +%H:%M:%S.%3N
}

# Đóng dấu giờ lại bằng đồng hồ của máy chạy demo.sh, vì đồng hồ các node EVE
# lệch nhau tới cả giây. Bỏ giờ do guard tự in (chữ đầu dòng), thay bằng giờ ở đây.
restamp() {
    while IFS= read -r line; do
        echo "$(stamp) ${line#* }"
    done
}

"$ROOT/scripts/reset.sh"
: > "$EVENTS"

echo "=== Lượt '$MODE' bắt đầu (LAB=$LAB) ==="

"$RUN" server "$BIN/server" > "$OUT/server_$MODE.log" 2>&1 &

if [ "$MODE" = "on" ]; then
    "$RUN" r3 "$BIN/guard -n R3 -d -i eth1 -t $THRESHOLD $WHITE -P 10.0.99.1 -P 10.0.99.2" 2>&1 | restamp >> "$EVENTS" &
    "$RUN" r1 "$BIN/guard -n R1 -l -b 10.0.99.1 $WHITE" 2>&1 | restamp >> "$EVENTS" &
    "$RUN" r2 "$BIN/guard -n R2 -l -b 10.0.99.2 $WHITE" 2>&1 | restamp >> "$EVENTS" &
else
    "$RUN" r3 "$BIN/guard -n R3 -d -i eth1 -t $THRESHOLD $WHITE" 2>&1 | restamp >> "$EVENTS" &
fi
sleep 2

"$RUN" r1 "sh $LINKMON eth2 $DURATION" > "$OUT/link_$MODE.csv" 2>/dev/null &
# CSV của client ghi ra stderr để thu về được cả khi chạy qua SSH.
"$RUN" client "$BIN/client -s 10.0.3.10 -r $CLIENT_RATE -d $DURATION -o /dev/stderr" \
    > "$OUT/client_$MODE.log" 2> "$OUT/client_$MODE.csv" &
CLIENT_PID=$!

sleep "$ATTACK_AT"
echo "$(stamp) [demo] BẮT ĐẦU TẤN CÔNG" >> "$EVENTS"
"$RUN" attacker "$BIN/attacker -s 10.0.3.10 -r $ATTACK_RATE -l $ATTACK_SIZE -d $((DURATION - ATTACK_AT))" \
    > "$OUT/attacker_$MODE.log" 2>&1 &

wait "$CLIENT_PID"
sleep 1
"$ROOT/scripts/reset.sh"
sleep 1
wait 2>/dev/null

# Chạy bằng sudo thì trả quyền sở hữu file kết quả cho người dùng.
if [ -n "${SUDO_USER:-}" ]; then
    chown -R "$SUDO_USER:" "$OUT"
fi

echo "=== Lượt '$MODE' xong. Kết quả trong results/*_$MODE.* ==="
grep -E "PHÁT HIỆN|NHẬN|BẮT ĐẦU" "$EVENTS"
