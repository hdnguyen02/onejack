#!/bin/bash
# Tạo image Alpine "linux-alpine-demo" cho các node EVE-NG. Chỉ cần chạy một lần.
# Chạy NGAY TRONG máy ảo EVE (root), trong thư mục dự án đã copy vào EVE.
#   bash lab/eve-make-image.sh
# Node nhận khóa SSH của EVE và các khóa đang được phép vào EVE (authorized_keys),
# nên từ EVE, và từ máy thật nếu đã ssh-copy-id, SSH thẳng vào node được.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG_DIR="/opt/unetlab/addons/qemu/linux-alpine-demo"
WORK="$(mktemp -d)"
TOOL_URL="https://raw.githubusercontent.com/alpinelinux/alpine-make-vm-image/v0.13.0/alpine-make-vm-image"

if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -q -t ed25519 -N "" -f ~/.ssh/id_ed25519
fi
cat ~/.ssh/id_ed25519.pub > "$WORK/keys"
if [ -f ~/.ssh/authorized_keys ]; then
    cat ~/.ssh/authorized_keys >> "$WORK/keys"
fi
cp "$ROOT/lab/eve-image-configure.sh" "$WORK/configure.sh"
chmod +x "$WORK/configure.sh"

wget -q -O "$WORK/alpine-make-vm-image" "$TOOL_URL"
chmod +x "$WORK/alpine-make-vm-image"
modprobe nbd max_part=8

cd "$WORK"
./alpine-make-vm-image --image-format qcow2 --image-size 1G --branch v3.20 \
    --kernel-flavor virt --packages "openssh iproute2 iptables" \
    --script-chroot alpine-demo.qcow2 -- ./configure.sh

mkdir -p "$IMG_DIR"
mv alpine-demo.qcow2 "$IMG_DIR/virtioa.qcow2"
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
rm -rf "$WORK"
echo "Đã tạo image: $IMG_DIR/virtioa.qcow2"
