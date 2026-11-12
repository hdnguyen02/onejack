# Các lệnh bạn cần tự chạy

Những lệnh dưới đây cần `sudo` (mật khẩu Ubuntu) nên bạn tự chạy. Có hai cách chạy:

- **Trong Claude Code:** gõ cả dấu `!` ở đầu dòng, ví dụ `! sudo ...`. Kết quả hiện ngay trong phiên để Claude đọc.
- **Trong terminal bình thường:** bỏ dấu `!`, chạy từ thư mục `~/Desktop/onejack`.

Mỗi bước làm xong thì đánh dấu `[x]`. Claude sẽ thêm bước mới vào file này khi tới lúc.

---

## Bước 1: Chạy thử mini-lab trên máy (khoảng 2,5 phút)

Bước này dựng mạng ảo bằng namespace trên chính máy bạn, kiểm tra ping, rồi chạy 2 lượt demo `off` và `on`.

- [x] Dựng lab và chạy 2 lượt:
  ```
  ! cd ~/Desktop/onejack && sudo lab/netns-up.sh && sudo ip netns exec client ping -c2 10.0.3.10 && sudo ip netns exec r1 ping -c2 10.0.99.3 && sudo scripts/demo.sh off && sudo scripts/demo.sh on
  ```
  Kết quả sẽ nằm trong `results/`.

Các lệnh dùng thêm khi cần:

| Mục đích | Lệnh |
|---|---|
| Chạy lại riêng lượt không hợp tác | `! cd ~/Desktop/onejack && sudo scripts/demo.sh off` |
| Chạy lại riêng lượt có hợp tác | `! cd ~/Desktop/onejack && sudo scripts/demo.sh on` |
| Dừng mọi thứ đang chạy, xóa rule chặn | `! cd ~/Desktop/onejack && sudo scripts/reset.sh` |
| Xóa mini-lab | `! cd ~/Desktop/onejack && sudo lab/netns-down.sh` |
| Dựng lại mini-lab (sau khi khởi động lại máy) | `! cd ~/Desktop/onejack && sudo lab/netns-down.sh; sudo lab/netns-up.sh` |

## Bước 2: Cài KVM để chạy EVE-NG

- [ ] Cài các gói cần thiết và thêm tài khoản của bạn vào nhóm `libvirt`:
  ```
  ! sudo apt-get update && sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients virtinst virt-manager bridge-utils tmux gnuplot sshpass && sudo usermod -aG libvirt,kvm $USER
  ```
- [ ] **Đăng xuất rồi đăng nhập lại Ubuntu** để quyền nhóm `libvirt` có hiệu lực.

## Bước 3: Tải và cài EVE-NG

- [ ] File ISO `~/Downloads/eve-ce-prod-6.2.0-4-full.iso` (EVE-NG Community 6.2.0-4, 3,2GB): Claude tải sẵn và kiểm tra SHA256. Bạn không cần làm gì.
- [ ] Tạo máy ảo EVE-NG (6GB RAM, 4 vCPU, ổ 60GB, bật ảo hóa lồng nhau):
  ```
  ! sudo virt-install --name eve-ng --memory 6144 --vcpus 4 --cpu host-passthrough --disk size=60,format=qcow2 --cdrom ~/Downloads/eve-ce-prod-6.2.0-4-full.iso --network network=default --os-variant ubuntu22.04 --graphics vnc --noautoconsole
  ```
- [ ] Mở **virt-manager** (menu ứng dụng, hoặc gõ `virt-manager`), nháy đúp máy `eve-ng` để xem màn hình rồi cài:
  1. Ở menu khởi động, chọn **Install EVE VM**.
  2. Làm theo trình cài đặt, để mặc định hết. Máy sẽ tự khởi động lại.
  3. Sau khi khởi động lại, đăng nhập `root` / `eve`. Trình thiết lập lần đầu sẽ hỏi:
     - Mật khẩu root mới: **ghi lại mật khẩu này**.
     - Hostname và domain: để mặc định.
     - IP: chọn **dhcp**.
     - NTP và proxy: để trống hoặc chọn direct.
  4. Máy khởi động lại lần nữa. Màn hình đăng nhập sẽ hiện địa chỉ IP của EVE.
- [ ] Báo Claude là đã cài xong. Claude sẽ lấy IP và hướng dẫn bước kết nối SSH.

## Bước 4: Tạo image Alpine và dựng lab trong EVE-NG

*(Claude sẽ điền khi tới bước này.)*

## Bước 5: Chạy demo trên EVE-NG

*(Claude sẽ điền khi tới bước này.)*
