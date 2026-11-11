#!/bin/sh
# Ghi số byte/giây gửi ra trên một interface, mỗi giây một dòng CSV: t,bytes_per_s
# Cách dùng: linkmon.sh <iface> <số_giây>
IF="$1"
DUR="$2"
F="/sys/class/net/$IF/statistics/tx_bytes"
echo "t,bytes_per_s"
prev=$(cat "$F")
t=0
while [ "$t" -lt "$DUR" ]; do
    sleep 1
    t=$((t + 1))
    cur=$(cat "$F")
    echo "$t,$((cur - prev))"
    prev=$cur
done
