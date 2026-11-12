#!/bin/sh
# Chạy trong chroot của image Alpine (alpine-make-vm-image --script-chroot).
# /mnt là thư mục chứa script này, cần thêm file keys (các khóa SSH được phép vào node).
# Bật sshd, IP quản lý theo MAC của EVE.
set -e
rc-update add sshd default
rc-update add local default
echo 'root:eve' | chpasswd
mkdir -p /root/.ssh
cp /mnt/keys /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
printf 'auto lo\niface lo inet loopback\n' > /etc/network/interfaces
cat > /etc/local.d/mgmt.start <<'EOS'
#!/bin/sh
# MAC của EVE: 00:50:<tenant>:<id/512>:<id%512>:<cổng> -> lấy id node.
mac=$(cat /sys/class/net/eth0/address)
hi=$(echo "$mac" | cut -d: -f4)
lo=$(echo "$mac" | cut -d: -f5)
id=$((0x$hi * 512 + 0x$lo))
ip link set eth0 up
ip addr add "172.30.0.$((10 + id))/24" dev eth0
hostname "node$id"
EOS
chmod +x /etc/local.d/mgmt.start
