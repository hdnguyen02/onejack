#!/bin/bash
# Vẽ biểu đồ so sánh các lượt off / on / inband và in bảng tóm tắt.
# Bắt buộc có lượt off và on, lượt inband có thì vẽ thêm.
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

MODES="off on"
if [ -f "$DIR/client_inband.csv" ] && [ -f "$DIR/link_inband.csv" ]; then
    MODES="off on inband"
fi

# Màu và chú thích của từng lượt trên biểu đồ.
color() {
    if [ "$1" = "off" ]; then
        echo "#d62728"
    elif [ "$1" = "on" ]; then
        echo "#2ca02c"
    else
        echo "#1f77b4"
    fi
}

title() {
    if [ "$1" = "off" ]; then
        echo "off: không hợp tác"
    elif [ "$1" = "on" ]; then
        echo "on: hợp tác, mạng điều khiển riêng"
    else
        echo "inband: hợp tác, chung đường + QoS"
    fi
}

plot() {
    # plot <file png> <tiêu đề> <nhãn trục y> <tiền tố file: client|link> <biểu thức y của gnuplot> [khoảng trục y]
    local lines=""
    for m in $MODES; do
        if [ -n "$lines" ]; then
            lines="$lines, "
        fi
        lines="$lines\"$DIR/$4_$m.csv\" every ::1 using 1:($5) with lines linewidth 2 linecolor rgb \"$(color "$m")\" title \"$(title "$m")\""
    done

    gnuplot <<EOF
set terminal pngcairo size 1000,500 font "Sans,11"
set output "$DIR/$1"
set title "$2"
set xlabel "Thời gian (giây)"
set ylabel "$3"
set datafile separator ","
set key right center box opaque
set grid
set yrange ${6:-[0:*]}
set arrow from $ATTACK_AT, graph 0 to $ATTACK_AT, graph 1 nohead dashtype 2 linecolor rgb "#888888"
set label "bắt đầu tấn công" at $ATTACK_AT, graph 0.7 offset 1.5,0
plot $lines
EOF
}

plot rtt.png  "Độ trễ RTT của client"        "RTT (ms)"    client '$5'
plot loss.png "Tỉ lệ mất gói của client"     "Mất gói (%)" client '$4' '[0:100]'
plot link.png "Lưu lượng trên đường truyền R1 -> R2" "Mbit/s"      link   '$2*8/1000000'

summary() {
    # summary <lượt>: trung bình RTT, % mất gói, Mbit/s trên link sau khi bị tấn công
    local m="$1"
    local client link
    client=$(awk -F, -v a="$ATTACK_AT" 'NR > 1 && $1 > a { r += $5; l += $4; n++ }
        END { if (n) printf "%10.2f %10.1f", r / n, l / n; else printf "%10s %10s", "-", "-" }' "$DIR/client_$m.csv")
    link=$(awk -F, -v a="$ATTACK_AT" 'NR > 1 && $1 > a { b += $2; n++ }
        END { if (n) printf "%10.2f", b / n * 8 / 1000000; else printf "%10s", "-" }' "$DIR/link_$m.csv")
    printf "%-7s %s %s\n" "$m" "$client" "$link"
}

# timing <lượt>: thời gian R3 phát hiện và R1 chặn, tính từ log sự kiện.
timing() {
    local m="$1"
    if [ ! -f "$DIR/events_$m.log" ]; then
        return
    fi
    awk -v m="$m" '
        function sec(s,   p) { split(s, p, ":"); return p[1] * 3600 + p[2] * 60 + p[3] }
        /\[demo\] BẮT ĐẦU TẤN CÔNG/ { start = sec($1) }
        /\[R3\] PHÁT HIỆN/ && !det { det = sec($1) }
        /\[R1\] NHẬN/ && !blk { blk = sec($1) }
        END {
            if (start && det) printf "%-7s R3 phát hiện sau %.3f giây kể từ lúc tấn công", m, det - start
            if (det && blk) printf ", R1 chặn sau %.3f giây kể từ lúc R3 phát hiện", blk - det
            print ""
        }' "$DIR/events_$m.log"
}

echo
echo "Trung bình sau khi bị tấn công (giây $((ATTACK_AT + 1)) tới hết lượt):"
# Độ rộng tính theo byte, chữ có dấu chiếm nhiều byte hơn nên cộng thêm cho thẳng cột.
printf "%-10s %10s %12s %10s\n" "Lượt" "RTT (ms)" "Mất (%)" "Link Mbit/s"
for m in $MODES; do
    summary "$m"
done
echo
for m in $MODES; do
    timing "$m"
done
echo
echo "Biểu đồ: $DIR/rtt.png $DIR/loss.png $DIR/link.png"
