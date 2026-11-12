#!/bin/bash
# Vẽ biểu đồ so sánh hai lượt off/on và in bảng tóm tắt.
# Cách dùng: plot.sh [thư mục kết quả]   (mặc định: results/)
# Tạo ra: rtt.png, loss.png, link.png trong thư mục đó.
set -eu
# Dấu chấm thập phân, không theo locale tiếng Việt (dấu phẩy).
export LC_ALL=C
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${1:-$ROOT/results}"
ATTACK_AT=15

for f in client_off.csv client_on.csv link_off.csv link_on.csv; do
    if [ ! -f "$DIR/$f" ]; then
        echo "Thiếu $DIR/$f, chạy demo.sh off và demo.sh on trước." >&2
        exit 1
    fi
done

plot() {
    # plot <file png> <tiêu đề> <nhãn trục y> <file off> <file on> <biểu thức y của gnuplot> [khoảng trục y]
    gnuplot <<EOF
set terminal pngcairo size 1000,500 font "Sans,11"
set output "$DIR/$1"
set title "$2"
set xlabel "Thời gian (giây)"
set ylabel "$3"
set datafile separator ","
set key right center box opaque
set grid
set yrange ${7:-[0:*]}
set arrow from $ATTACK_AT, graph 0 to $ATTACK_AT, graph 1 nohead dashtype 2 linecolor rgb "#888888"
set label "bắt đầu tấn công" at $ATTACK_AT, graph 0.7 offset 1.5,0
plot "$DIR/$4" every ::1 using 1:($6) with lines linewidth 2 linecolor rgb "#d62728" title "off: không hợp tác", \
     "$DIR/$5" every ::1 using 1:($6) with lines linewidth 2 linecolor rgb "#2ca02c" title "on: có hợp tác"
EOF
}

plot rtt.png  "Độ trễ RTT của client"          "RTT (ms)"   client_off.csv client_on.csv '$5'
plot loss.png "Tỉ lệ mất gói của client"       "Mất gói (%)" client_off.csv client_on.csv '$4' '[0:100]'
plot link.png "Lưu lượng trên link R1 -> R2"   "Mbit/s"     link_off.csv   link_on.csv   '$2*8/1000000'

summary() {
    # summary <lượt>: trung bình RTT, % mất gói, Mbit/s trên link trong giây 16..60
    local m="$1"
    local client link
    client=$(awk -F, -v a="$ATTACK_AT" 'NR > 1 && $1 > a { r += $5; l += $4; n++ }
        END { if (n) printf "%10.2f %10.1f", r / n, l / n; else printf "%10s %10s", "-", "-" }' "$DIR/client_$m.csv")
    link=$(awk -F, -v a="$ATTACK_AT" 'NR > 1 && $1 > a { b += $2; n++ }
        END { if (n) printf "%10.2f", b / n * 8 / 1000000; else printf "%10s", "-" }' "$DIR/link_$m.csv")
    printf "%-6s %s %s\n" "$m" "$client" "$link"
}

echo
echo "Trung bình sau khi bị tấn công (giây $((ATTACK_AT + 1)) tới hết lượt):"
printf "%-6s %10s %10s %10s\n" "Lượt" "RTT (ms)" "Mất (%)" "Link Mbit/s"
summary off
summary on

# Thời gian từ lúc bắt đầu tấn công tới lúc R1 chặn (lượt on).
if [ -f "$DIR/events_on.log" ]; then
    awk '
        function sec(s,   p) { split(s, p, ":"); return p[1] * 3600 + p[2] * 60 + p[3] }
        /\[demo\] BẮT ĐẦU TẤN CÔNG/ { start = sec($1) }
        /\[R3\] PHÁT HIỆN/ && !det { det = sec($1) }
        /\[R1\] NHẬN/ && !blk { blk = sec($1) }
        END {
            if (start && det) printf "R3 phát hiện sau %.3f giây kể từ lúc tấn công\n", det - start
            if (det && blk) printf "R1 chặn sau %.3f giây kể từ lúc R3 phát hiện\n", blk - det
        }' "$DIR/events_on.log"
fi
echo
echo "Biểu đồ: $DIR/rtt.png $DIR/loss.png $DIR/link.png"
