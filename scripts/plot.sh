#!/bin/bash
# Vẽ biểu đồ so sánh các lượt base / short / balance và in bảng tóm tắt.
# Lượt nào có số liệu thì vẽ lượt đó, cần ít nhất lượt base.
# Cách dùng: plot.sh [thư mục kết quả]   (mặc định: results/)
# Tạo ra: rtt.png, rtt_low.png, jitter.png, throughput.png, paths.png trong thư mục đó.
set -eu
# Dấu chấm thập phân, không theo locale tiếng Việt (dấu phẩy).
export LC_ALL=C
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${1:-$ROOT/results}"
LOAD_AT=15
DURATION=60

if [ ! -f "$DIR/client_base.csv" ]; then
    echo "Thiếu $DIR/client_base.csv, chạy demo.sh base trước." >&2
    exit 1
fi

MODES=""
for m in base short balance; do
    if [ -f "$DIR/client_$m.csv" ] && [ -f "$DIR/server_$m.csv" ] && [ -f "$DIR/link_$m.csv" ]; then
        MODES="$MODES $m"
    fi
done

# Màu và chú thích của từng lượt trên biểu đồ.
color() {
    if [ "$1" = "base" ]; then
        echo "#d62728"
    elif [ "$1" = "short" ]; then
        echo "#ff7f0e"
    else
        echo "#2ca02c"
    fi
}

title() {
    if [ "$1" = "base" ]; then
        echo "base: đường dài qua R2"
    elif [ "$1" = "short" ]; then
        echo "short: đường ngắn R1 -> R3"
    else
        echo "balance: chia tải 2 đường"
    fi
}

# plot <file png> <tiêu đề> <nhãn trục y> <khoảng trục y> <danh sách đường vẽ của gnuplot> [vị trí chú thích] [độ cao nhãn, 0..1]
plot() {
    gnuplot <<EOF
set terminal pngcairo size 1000,500 font "Sans,11" noenhanced
set output "$DIR/$1"
set title "$2"
set xlabel "Thời gian (giây)"
set ylabel "$3"
set datafile separator ","
set key ${6:-right bottom} box opaque
set grid
set xrange [0:$DURATION]
set yrange $4
set arrow from $LOAD_AT, graph 0 to $LOAD_AT, graph 1 nohead dashtype 2 linecolor rgb "#888888"
set label "bắt đầu tải nặng" at $LOAD_AT, graph ${7:-0.9} right offset -1,0
plot $5
EOF
}

# lines <tiền tố file: client|server> <biểu thức y của gnuplot> [các lượt]: một đường cho mỗi lượt.
lines() {
    local out=""
    for m in ${3:-$MODES}; do
        if [ -n "$out" ]; then
            out="$out, "
        fi
        out="$out\"$DIR/$1_$m.csv\" every ::1 using 1:($2) with lines linewidth 2 linecolor rgb \"$(color "$m")\" title \"$(title "$m")\""
    done
    echo "$out"
}

plot rtt.png        "Độ trễ RTT của client"                         "RTT (ms)"    "[0:*]"  "$(lines client '$5')" "right center" 0.7
# Phóng to vùng độ trễ thấp: thấy rõ đường dài (~40 ms) và đường ngắn (~20 ms) lúc chưa tải.
plot rtt_low.png    "Độ trễ RTT của client (phóng to vùng dưới 80 ms)" "RTT (ms)" "[0:80]" "$(lines client '$5')"
plot jitter.png     "Jitter của client"                             "Jitter (ms)" "[0:*]"  "$(lines client '$6')"
plot throughput.png "Thông lượng server nhận được (tải gửi 12 Mbit/s)" "Mbit/s"   "[0:15]" "$(lines server '$3')"

# Lưu lượng R1 gửi ra từng đường: cột 2 = đường dài (eth2), cột 3 = đường ngắn (eth3).
paths_lines=""
add_path() {
    # add_path <lượt> <cột> <tên đường> <kiểu nét>
    if [ -f "$DIR/link_$1.csv" ]; then
        if [ -n "$paths_lines" ]; then
            paths_lines="$paths_lines, "
        fi
        paths_lines="$paths_lines\"$DIR/link_$1.csv\" every ::1 using 1:(\$$2*8/1000000) with lines linewidth 2 dashtype $4 linecolor rgb \"$(color "$1")\" title \"$1: $3\""
    fi
}
add_path base 2 "đường dài" 1
add_path short 3 "đường ngắn" 1
add_path balance 2 "đường dài" 1
add_path balance 3 "đường ngắn" 2
plot paths.png "Lưu lượng R1 gửi ra từng đường (mỗi đường tối đa 10 Mbit/s)" "Mbit/s" "[0:12]" "$paths_lines"

# avg <file csv> <cột>: trung bình một cột trong lúc có tải (bỏ giây đầu tiên và giây cuối).
avg() {
    awk -F, -v a="$LOAD_AT" -v c="$2" 'NR > 1 && $1 > a + 1 { last = $1; v[$1] = $c }
        END { s = 0; n = 0; for (t in v) { if (t + 0 < last) { s += v[t]; n++ } }
              if (n) printf "%.2f", s / n; else printf "-" }' "$1"
}

# avg_mbit <file link csv> <cột>: như avg nhưng đổi byte/giây sang Mbit/s.
avg_mbit() {
    awk -F, -v a="$LOAD_AT" -v c="$2" 'NR > 1 && $1 > a + 1 { last = $1; v[$1] = $c }
        END { s = 0; n = 0; for (t in v) { if (t + 0 < last) { s += v[t]; n++ } }
              if (n) printf "%.2f", s / n * 8 / 1000000; else printf "-" }' "$1"
}

# idle <file client csv>: RTT trung bình lúc chưa có tải (giây 2 tới trước lúc bắt đầu tải).
idle() {
    awk -F, -v a="$LOAD_AT" 'NR > 1 && $1 > 1 && $1 < a { s += $5; n++ } END { if (n) printf "%.2f", s / n; else printf "-" }' "$1"
}

echo
echo "Chưa tải: RTT trung bình giây 2 tới $((LOAD_AT - 1))."
echo "Có tải: trung bình giây $((LOAD_AT + 2)) tới hết lượt."
printf "%-10s %16s %16s %11s %9s %13s %12s %13s\n" "Lượt" "RTT chưa tải" "RTT có tải" "Jitter ms" "Mất %" "Server Mbit/s" "Đường dài" "Đường ngắn"
for m in $MODES; do
    printf "%-10s %13s ms %13s ms %11s %9s %13s %10s %10s\n" "$m" \
        "$(idle "$DIR/client_$m.csv")" \
        "$(avg "$DIR/client_$m.csv" 5)" "$(avg "$DIR/client_$m.csv" 6)" "$(avg "$DIR/client_$m.csv" 4)" \
        "$(avg "$DIR/server_$m.csv" 3)" "$(avg_mbit "$DIR/link_$m.csv" 2)" "$(avg_mbit "$DIR/link_$m.csv" 3)"
done
echo
echo "Biểu đồ: $DIR/rtt.png $DIR/rtt_low.png $DIR/jitter.png $DIR/throughput.png $DIR/paths.png"
