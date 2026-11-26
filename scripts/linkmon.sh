#!/bin/sh
# Ghi số byte/giây gửi ra trên một hoặc nhiều interface, mỗi giây một dòng CSV.
# Cách dùng: linkmon.sh <số_giây> <iface> [iface...]
# Ví dụ trên R1: linkmon.sh 60 eth2 eth3  ->  t,eth2,eth3  (byte/giây đi ra đường 1 và đường 2)
DUR="$1"
shift
IFACES="$*"

read_all() {
    out=""
    for i in $IFACES; do
        out="$out $(cat "/sys/class/net/$i/statistics/tx_bytes")"
    done
    echo "$out"
}

header="t"
for i in $IFACES; do
    header="$header,$i"
done
echo "$header"

prev=$(read_all)
t=0
while [ "$t" -lt "$DUR" ]; do
    sleep 1
    t=$((t + 1))
    cur=$(read_all)
    line="$t"
    set -- $prev
    for c in $cur; do
        line="$line,$((c - $1))"
        shift
    done
    echo "$line"
    prev=$cur
done
