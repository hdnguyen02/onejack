#!/bin/bash
# Chuẩn bị lab trước khi demo, rồi kiểm tra sức khỏe.
# In "SẴN SÀNG" nếu mọi thứ ổn, nếu không in "LỖI: <bước>" và thoát mã 1.
#   LAB=eve   (mặc định): chạy trong máy ảo EVE, bật 6 node, copy và cấu hình lại.
#   LAB=netns           : mini-lab trên máy Linux, cần root, dựng bằng lab/netns-up.sh trước.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/scripts/node-run.sh"
LAB="${LAB:-eve}"
export LAB

fail() {
    echo "LỖI: $1"
    exit 1
}

step() {
    echo "--- $1"
}

if [ "$LAB" = "eve" ]; then
    API="http://127.0.0.1/api"
    LABFILE="net-perf.unl"
    COOKIE="$(mktemp)"

    step "Bật 6 node trong EVE"
    curl -s -c "$COOKIE" -X POST -d '{"username":"admin","password":"eve","html5":"-1"}' \
        "$API/auth/login" > /dev/null || fail "không đăng nhập được API của EVE"
    for id in 1 2 3 4 5 6; do
        # Node đang chạy thì EVE bỏ qua lệnh start.
        curl -s -b "$COOKIE" "$API/labs/$LABFILE/nodes/$id/start" > /dev/null
    done
    rm -f "$COOKIE"

    step "Chờ node nhận IP quản lý (tối đa 2 phút)"
    ready=0
    for t in $(seq 1 60); do
        ready=0
        while read -r node ip; do
            case "$node" in
                ''|'#'*) continue ;;
            esac
            if ssh -n -o BatchMode=yes -o ConnectTimeout=2 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                -o LogLevel=ERROR "root@$ip" true 2>/dev/null; then
                ready=$((ready + 1))
            fi
        done < "$ROOT/lab/nodes.conf"
        if [ "$ready" -eq 6 ]; then
            break
        fi
        sleep 2
    done
    if [ "$ready" -ne 6 ]; then
        fail "chỉ $ready/6 node SSH được, xem lab trên web EVE"
    fi

    step "Copy chương trình và cấu hình mạng cho từng node"
    "$ROOT/scripts/eve-push.sh" < /dev/null || fail "copy hoặc cấu hình node"
else
    if ! ip netns list | grep -q '^r1'; then
        fail "chưa dựng mini-lab, chạy: sudo lab/netns-up.sh"
    fi
fi

step "Dọn tiến trình cũ"
"$ROOT/scripts/reset.sh"

step "Client ping server qua R1 -> R2 -> R3"
"$RUN" client "ping -c2 -W2 10.0.3.10" > /dev/null 2>&1 || fail "client không ping được server"

step "R1 ping R3 qua đường ngắn (nối thẳng)"
"$RUN" r1 "ping -c2 -W2 10.0.13.3" > /dev/null 2>&1 || fail "R1 không ping được R3 (10.0.13.3)"

if [ "$LAB" = "eve" ]; then
    CONF="/root"
else
    CONF="$ROOT/lab"
fi
step "Thử cấu hình đường ngắn và chia tải trên router"
for mode in short balance; do
    for r in r1 r2 r3; do
        "$RUN" "$r" "sh $CONF/$r.sh $mode" > /dev/null 2>&1 || fail "$r không cấu hình được đường đi $mode"
    done
    "$RUN" client "ping -c2 -W2 10.0.3.10" > /dev/null 2>&1 || fail "client không ping được server khi đường đi là $mode"
done
"$RUN" r1 "ip route show 10.0.3.0/24" 2>/dev/null | grep -q 10.0.13.3 || fail "R1 chưa có đường ngắn tới server"
for r in r1 r2 r3; do
    "$RUN" "$r" "sh $CONF/$r.sh long" > /dev/null 2>&1 || fail "$r không trả về đường dài mặc định"
done

step "Client gửi truy vấn thật trong 3 giây"
if [ "$LAB" = "eve" ]; then
    BIN="/root"
else
    BIN="$ROOT/build"
fi
"$RUN" server "$BIN/server" > /dev/null 2>&1 &
sleep 1
out="$("$RUN" client "$BIN/client -s 10.0.3.10 -r 20 -d 3" 2>/dev/null)"
"$ROOT/scripts/reset.sh"
wait 2>/dev/null
# Mỗi giây client in một dòng "... nhận=20 ...". Cần đủ 3 giây nhận đủ 20 gói.
good=$(echo "$out" | grep -c 'nhận=20 ')
if [ "$good" -lt 3 ]; then
    echo "$out"
    fail "client không nhận đủ trả lời từ server"
fi

step "RAM trống"
avail=$(free -m | awk '/^Mem:/ { print $7 }')
echo "    còn trống ${avail}MB"
if [ "$avail" -lt 500 ]; then
    fail "RAM trống dưới 500MB, tắt bớt ứng dụng"
fi

echo
echo "SẴN SÀNG"
