#!/bin/bash
# Tạo lab collab-defense trong EVE-NG qua REST API, không cần kéo thả trên web.
# Chạy NGAY TRONG máy ảo EVE (bằng root). Cần image linux-alpine-demo đã có sẵn.
#   bash eve-create-lab.sh
# Mạng quản lý: Cloud1 (pnet1) = 172.30.0.0/24, EVE là 172.30.0.1,
# node số N có IP 172.30.0.(10+N) (tự đặt khi khởi động, xem image).
set -eu

API="http://127.0.0.1/api"
LAB="collab-defense"
COOKIE="$(mktemp)"

api() {
    # api <METHOD> <đường dẫn> [json]
    curl -s -b "$COOKIE" -c "$COOKIE" -X "$1" -H 'Content-Type: application/json' \
        ${3:+-d "$3"} "$API$2"
}

# 1. IP quản lý cho EVE trên pnet1 (giữ lại sau khi khởi động lại).
if ! grep -q '172.30.0.1' /etc/network/interfaces; then
    sed -i 's/^iface pnet1 inet manual/iface pnet1 inet static\n    address 172.30.0.1\/24/' /etc/network/interfaces
fi
ip addr replace 172.30.0.1/24 dev pnet1
ip link set pnet1 up

# 2. Đăng nhập, dừng và xóa lab cũ nếu có.
api POST /auth/login '{"username":"admin","password":"eve","html5":"-1"}' > /dev/null
api GET "/labs/$LAB.unl/nodes/stop" > /dev/null || true
sleep 2
# Node của lab cũ có thể còn chạy dù API báo đã dừng.
for pid in $(pgrep qemu-system); do
    kill "$pid"
done
sleep 2
api GET "/labs/$LAB.unl/nodes/wipe" > /dev/null || true
api DELETE "/labs/$LAB.unl" > /dev/null || true
api POST /labs "{\"path\":\"/\",\"name\":\"$LAB\",\"version\":\"1\",\"author\":\"onejack\",\"description\":\"Collaborative defense demo\"}" > /dev/null

# 3. Các mạng. Thứ tự tạo quyết định id mạng (1..6).
net() {
    # net <tên> <loại> <x> <y>
    api POST "/labs/$LAB.unl/networks" \
        "{\"name\":\"$1\",\"type\":\"$2\",\"left\":\"$3\",\"top\":\"$4\",\"visibility\":\"1\"}" > /dev/null
}
net MGMT  pnet1  600 600
net LAN1  bridge 250 300
net R1R2  bridge 450 300
net R2R3  bridge 650 300
net R3SRV bridge 850 300
net CTRL  bridge 600 450
MGMT=1; LAN1=2; R1R2=3; R2R3=4; R3SRV=5; CTRL=6

# 4. Các node. Thứ tự tạo quyết định id node (1..6) và IP quản lý (.11..16).
node() {
    # node <tên> <số cổng> <x> <y>
    api POST "/labs/$LAB.unl/nodes" \
        "{\"type\":\"qemu\",\"template\":\"linux\",\"image\":\"linux-alpine-demo\",\"name\":\"$1\",\"ethernet\":\"$2\",\"ram\":\"256\",\"cpu\":\"1\",\"console\":\"vnc\",\"left\":\"$3\",\"top\":\"$4\",\"icon\":\"Server.png\"}" > /dev/null
}
node attacker 2 100 200
node client   2 100 400
node r1       4 350 300
node r2       4 550 300
node r3       4 750 300
node server   2 950 300

# 5. Nối dây: cổng 0 = MGMT, các cổng sau theo lab/<node>.sh.
wire() {
    # wire <id node> <json cổng -> id mạng>
    api PUT "/labs/$LAB.unl/nodes/$1/interfaces" "$2" > /dev/null
}
wire 1 "{\"0\":$MGMT,\"1\":$LAN1}"
wire 2 "{\"0\":$MGMT,\"1\":$LAN1}"
wire 3 "{\"0\":$MGMT,\"1\":$LAN1,\"2\":$R1R2,\"3\":$CTRL}"
wire 4 "{\"0\":$MGMT,\"1\":$R1R2,\"2\":$R2R3,\"3\":$CTRL}"
wire 5 "{\"0\":$MGMT,\"1\":$R2R3,\"2\":$R3SRV,\"3\":$CTRL}"
wire 6 "{\"0\":$MGMT,\"1\":$R3SRV}"

# 6. Khởi động cả 6 node.
for id in 1 2 3 4 5 6; do
    api GET "/labs/$LAB.unl/nodes/$id/start" > /dev/null
done

rm -f "$COOKIE"
echo "Lab $LAB đã tạo và khởi động. Node 1..6 = attacker client r1 r2 r3 server (172.30.0.11..16)."
