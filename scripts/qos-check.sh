#!/bin/bash
# Kiểm chứng làn ưu tiên (QoS) của router: cho attacker làm nghẽn đường R1 -> R2 -> R3
# (không bật guard nên không ai chặn), rồi đo RTT của:
#   1. truy vấn thường: phải xếp hàng sau đống rác, chậm khoảng 400 ms
#   2. truy vấn đánh dấu ưu tiên (client -Q): đi làn ưu tiên, nhanh như lúc bình thường
# Cảnh báo ở lượt "inband" được đánh dấu y như truy vấn ưu tiên này.
# Cách dùng: qos-check.sh   (LAB=eve mặc định, LAB=netns cho mini-lab)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/scripts/node-run.sh"
LAB="${LAB:-eve}"
export LAB
if [ "$LAB" = "netns" ]; then
    BIN="$ROOT/build"
else
    BIN="/root"
fi
MEASURE=5   # số giây đo cho mỗi loại truy vấn

# avg_rtt: đọc các dòng "[client] ... rtt=  2.00 ms", trả về RTT trung bình.
avg_rtt() {
    awk '{ for (i = 1; i <= NF; i++) if ($i ~ /^rtt=/) { v = substr($i, 5); if (v == "") v = $(i + 1); s += v; n++ } }
         END { if (n) printf "%.2f", s / n; else printf "-" }'
}

"$ROOT/scripts/reset.sh"
"$RUN" server "$BIN/server" > /dev/null 2>&1 &
sleep 1

echo "Attacker bắt đầu làm nghẽn đường (không bật guard)..."
"$RUN" attacker "$BIN/attacker -s 10.0.3.10 -r 5000 -l 1000 -d $((MEASURE * 2 + 6))" > /dev/null 2>&1 &
sleep 3

echo "Đo truy vấn thường trong $MEASURE giây..."
normal=$("$RUN" client "$BIN/client -s 10.0.3.10 -r 20 -d $MEASURE" 2>/dev/null | avg_rtt)

echo "Đo truy vấn ưu tiên (QoS) trong $MEASURE giây..."
priority=$("$RUN" client "$BIN/client -s 10.0.3.10 -r 20 -d $MEASURE -Q" 2>/dev/null | avg_rtt)

"$ROOT/scripts/reset.sh"
wait 2>/dev/null

echo
echo "Khi đường đang nghẽn:"
echo "  RTT truy vấn thường:   $normal ms"
echo "  RTT truy vấn ưu tiên:  $priority ms"
