#!/bin/bash
# Chạy một lượt đo và thu số liệu về results/.
#   demo.sh base      : 1 đường, hàng đợi fifo       (mốc so sánh)
#   demo.sh fqcodel   : 1 đường, hàng đợi fq_codel   (giảm độ trễ)
#   demo.sh multipath : 2 đường, hàng đợi fifo       (tăng băng thông)
#   demo.sh combined  : 2 đường, hàng đợi fq_codel   (cả hai)
# Backend chọn bằng biến LAB=netns|eve (xem node-run.sh).
set -u

# ---- Thông số thí nghiệm (chỉnh ở đây) ----
DURATION=60          # tổng thời gian một lượt (giây)
LOAD_AT=15           # giây bắt đầu có tải nặng
CLIENT_RATE=20       # truy vấn/giây của client
LOAD_RATE=5000       # gói/giây của loadgen
LOAD_SIZE=1000       # byte mỗi gói tải (5000 × 1000 byte ≈ 40 Mbit/s)
LOAD_FLOWS=8         # số luồng tải song song
# -------------------------------------------

MODE="${1:-}"
if [ "$MODE" = "base" ]; then
    QUEUE=fifo
    PATHS=1
elif [ "$MODE" = "fqcodel" ]; then
    QUEUE=fqcodel
    PATHS=1
elif [ "$MODE" = "multipath" ]; then
    QUEUE=fifo
    PATHS=2
elif [ "$MODE" = "combined" ]; then
    QUEUE=fqcodel
    PATHS=2
else
    echo "Cách dùng: $0 base|fqcodel|multipath|combined" >&2
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
    CONF="$ROOT/lab"
    LINKMON="$ROOT/scripts/linkmon.sh"
else
    BIN="/root"
    CONF="/root"
    LINKMON="/root/linkmon.sh"
fi

EVENTS="$OUT/events_$MODE.log"

stamp() {
    date +%H:%M:%S.%3N
}

# Ghi sự kiện vào log và in ra màn hình.
event() {
    echo "$(stamp) $*" | tee -a "$EVENTS"
}

"$ROOT/scripts/reset.sh"
: > "$EVENTS"

echo "=== Lượt '$MODE' bắt đầu: $PATHS đường, hàng đợi $QUEUE (LAB=$LAB) ==="

# Cấu hình lại 3 router theo lượt này.
for r in r1 r2 r3; do
    if ! "$RUN" "$r" "sh $CONF/$r.sh $QUEUE $PATHS" > /dev/null 2>&1; then
        echo "LỖI: không cấu hình được $r" >&2
        exit 1
    fi
done
event "[demo] router: $PATHS đường, hàng đợi $QUEUE"
event "[R1] đường tới server: $("$RUN" r1 "ip route show 10.0.3.0/24" 2>/dev/null | tr '\n' ' ' | tr -s ' ')"
event "[R1] hàng đợi eth2: $("$RUN" r1 "tc qdisc show dev eth2" 2>/dev/null | awk '{ print $2 }' | tr '\n' ' ')"

# CSV của server và client ghi ra stderr để thu về được cả khi chạy qua SSH.
"$RUN" server "$BIN/server -o /dev/stderr" > "$OUT/server_$MODE.log" 2> "$OUT/server_$MODE.csv" &
"$RUN" r1 "sh $LINKMON $DURATION eth2 eth3" > "$OUT/link_$MODE.csv" 2>/dev/null &
"$RUN" client "$BIN/client -s 10.0.3.10 -r $CLIENT_RATE -d $DURATION -o /dev/stderr" \
    > "$OUT/client_$MODE.log" 2> "$OUT/client_$MODE.csv" &
CLIENT_PID=$!
event "[demo] client bắt đầu gửi $CLIENT_RATE truy vấn/giây"

sleep "$LOAD_AT"
event "[demo] BẮT ĐẦU TẢI NẶNG: $LOAD_FLOWS luồng, $LOAD_RATE gói/s × $LOAD_SIZE byte"
"$RUN" loadgen "$BIN/loadgen -s 10.0.3.10 -r $LOAD_RATE -l $LOAD_SIZE -f $LOAD_FLOWS -d $((DURATION - LOAD_AT))" \
    > "$OUT/loadgen_$MODE.log" 2>&1 &

wait "$CLIENT_PID"
sleep 1
"$ROOT/scripts/reset.sh"
sleep 1
wait 2>/dev/null
event "[demo] kết thúc lượt"

# Chạy bằng sudo thì trả quyền sở hữu file kết quả cho người dùng.
if [ -n "${SUDO_USER:-}" ]; then
    chown -R "$SUDO_USER:" "$OUT"
fi

echo "=== Lượt '$MODE' xong. Kết quả trong results/*_$MODE.* ==="
