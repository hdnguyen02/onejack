# Cài đặt và chạy demo trên Windows 11

Hướng dẫn từng bước để chạy demo **onejack** (cải thiện hiệu năng mạng: giảm độ trễ) trên một máy Windows 11, từ lúc chưa có gì tới lúc chạy xong 3 lượt demo.

Tổng quan dự án, mô hình mạng và kết quả đo xem trong [README.md](README.md). Cách trình bày và demo với giảng viên xem trong [KICH-BAN-DEMO.md](KICH-BAN-DEMO.md).

> **Máy đã cài bản cũ** (lab `collab-defense`, demo `off` / `on` / `inband`): không cần cài lại từ đầu, làm theo [mục 12](#12-cập-nhật-từ-bản-cũ-lên-bản-hiện-tại).

---

## 0. Hiểu cách hoạt động trước khi cài

Các script và chương trình C của dự án đều chạy trên **Linux**, không chạy trực tiếp trên Windows. Vì vậy cách làm như sau:

```
Windows 11 (máy thật)
 └─ VMware Workstation Pro
     └─ Máy ảo EVE-NG (Ubuntu 22.04)        ← code dự án nằm ở /root/onejack
         └─ 6 máy ảo Alpine nhỏ: loadgen, client, r1, r2, r3, server
```

- Máy ảo EVE-NG lại chạy 6 máy ảo con bên trong, gọi là **ảo hóa lồng nhau** (nested virtualization). Đây là lý do phải tắt Hyper-V ở bước 2.
- Windows chỉ dùng để mở VMware, mở trình duyệt xem sơ đồ mạng, và dùng `ssh` để gõ lệnh vào máy EVE.
- Từ bước 5 trở đi, mọi lệnh đều gõ **bên trong máy EVE** qua `ssh`.

Thời gian làm lần đầu: khoảng 1 tới 1,5 giờ, phần lớn là thời gian tải và cài.

---

## 1. Kiểm tra máy

| Yêu cầu | Tối thiểu | Cách kiểm tra |
|---|---|---|
| RAM | 16 GB | Task Manager → Performance → Memory |
| Ổ cứng trống | 70 GB | File Explorer → This PC |
| CPU hỗ trợ ảo hóa | Intel VT-x hoặc AMD-V, **đang bật** | Task Manager → Performance → CPU, dòng **Virtualization: Enabled** |
| Internet | Có | Máy EVE cần tải gói khi cài |

Nếu dòng Virtualization hiện **Disabled**, vào BIOS/UEFI để bật. Tùy hãng máy, mục này tên là Intel Virtualization Technology, Intel VT-x, SVM Mode hoặc AMD-V. Cách vào BIOS thường là bấm F2, F10, Del hoặc Esc ngay khi bật máy.

---

## 2. Tắt Hyper-V

Windows 11 thường bật sẵn Hyper-V và các tính năng bảo mật dựa trên ảo hóa. Khi các tính năng này bật, VMware không thể cho máy ảo EVE chạy máy ảo con, và các node trong lab sẽ không khởi động được.

### 2.1. Tắt các tính năng Windows

1. Bấm **Win + R**, gõ `optionalfeatures`, Enter.
2. **Bỏ tick** các mục sau (mục nào không có thì bỏ qua):
   - Hyper-V
   - Virtual Machine Platform
   - Windows Hypervisor Platform
   - Windows Sandbox
   - Windows Subsystem for Linux
3. Bấm OK. **Chưa cần** khởi động lại ngay.

> Tắt WSL nghĩa là tạm thời không dùng được WSL và Docker Desktop. Muốn dùng lại thì bật lại các mục này và chạy `bcdedit /set hypervisorlaunchtype auto`.

### 2.2. Tắt Memory integrity

1. Mở **Windows Security** → **Device security** → **Core isolation details**.
2. Gạt **Memory integrity** sang **Off**.

### 2.3. Tắt hypervisor lúc khởi động

1. Bấm Start, gõ `cmd`, chuột phải **Command Prompt** → **Run as administrator**.
2. Chạy:
   ```
   bcdedit /set hypervisorlaunchtype off
   ```
   Kết quả đúng: `The operation completed successfully.`

### 2.4. Khởi động lại máy

Khởi động lại để các thay đổi ở trên có hiệu lực.

**Kiểm tra:** mở cmd thường, chạy `systeminfo`, kéo xuống cuối. Nếu thấy dòng *"A hypervisor has been detected"* thì Hyper-V vẫn đang chạy, cần xem lại các bước trên.

---

## 3. Cài VMware Workstation Pro

VMware Workstation Pro hiện **miễn phí** cho cá nhân.

1. Vào `support.broadcom.com` và tạo tài khoản Broadcom nếu chưa có.
2. Vào mục **My Downloads** → **VMware Workstation Pro** → chọn bản mới nhất cho Windows → tải file `.exe`.
3. Chạy file cài đặt, để mặc định hết, khởi động lại máy nếu được hỏi.

> Không dùng VirtualBox. VirtualBox chạy ảo hóa lồng nhau kém, các node trong EVE sẽ rất chậm hoặc không chạy.

---

## 4. Cài máy ảo EVE-NG

### 4.1. Tải file ISO

Vào `eve-ng.net` → **Download** → **Community** → tải file `eve-ce-prod-6.2.0-4-full.iso` (khoảng 3,2 GB).

### 4.2. Tạo máy ảo trong VMware

1. Mở VMware → **File** → **New Virtual Machine** → chọn **Typical** → Next.
2. **Installer disc image file (iso)**: chọn file ISO vừa tải → Next.
3. Guest operating system: **Linux**, Version: **Ubuntu 64-bit** → Next.
4. Tên máy ảo: `eve-ng` → Next.
5. Disk size: **60 GB**, chọn **Store virtual disk as a single file** → Next.
6. Bấm **Customize Hardware** rồi chỉnh:

   | Mục | Giá trị |
   |---|---|
   | Memory | 6144 MB (6 GB). Máy thật có 32 GB thì cho 8 GB |
   | Processors | 4 core |
   | Processors → **Virtualize Intel VT-x/EPT or AMD-V/RVI** | **Tick** (bắt buộc) |
   | Network Adapter | **NAT** |

7. Close → Finish. **Bỏ tick** "Power on this virtual machine after creation" nếu có.

### 4.3. Cài EVE

1. Bấm **Power on this virtual machine**.
2. Ở menu khởi động, chọn **Install EVE VM**, Enter.
3. Trình cài đặt chạy tự động. Câu hỏi nào hiện ra cũng để mặc định rồi Enter. Máy sẽ tự khởi động lại.
4. Đăng nhập: user `root`, mật khẩu `eve`.
5. Trình thiết lập lần đầu sẽ hỏi lần lượt:

   | Câu hỏi | Trả lời |
   |---|---|
   | Root password | Đặt mật khẩu mới, **ghi lại mật khẩu này** |
   | Hostname | Để mặc định |
   | DNS domain name | Để mặc định |
   | IP address | Chọn **dhcp** |
   | NTP server | Để trống |
   | Proxy | Chọn **direct connection** |

6. Máy khởi động lại lần nữa. Màn hình đăng nhập sẽ hiện địa chỉ IP, ví dụ `http://192.168.xx.yy/`.

**Từ đây trở đi, địa chỉ IP này được viết là `<EVE_IP>`.** Khi gõ lệnh, nhớ thay bằng IP thật.

### 4.4. Kiểm tra

- Mở trình duyệt trên Windows, vào `http://<EVE_IP>`, đăng nhập `admin` / `eve`. Thấy giao diện EVE là được.
- Kiểm tra máy ảo có hỗ trợ ảo hóa lồng nhau không: đăng nhập vào màn hình máy EVE trong VMware rồi chạy:
  ```
  egrep -c '(vmx|svm)' /proc/cpuinfo
  ```
  Kết quả phải **lớn hơn 0**. Nếu ra `0`, xem lại bước 2 và ô tick VT-x ở bước 4.2.

---

## 5. Kết nối SSH từ Windows vào EVE

Gõ lệnh trong cửa sổ VMware rất bất tiện vì không copy/paste được, nên ta dùng `ssh`. Lệnh này có sẵn trong Windows 11.

1. Mở **PowerShell** (không cần quyền Admin).
2. Tạo khóa SSH, chỉ cần làm một lần. Bấm Enter cho mọi câu hỏi:
   ```
   ssh-keygen -t ed25519
   ```
3. Gửi khóa công khai vào EVE để lần sau không phải gõ mật khẩu. Lần này cần nhập mật khẩu root đã đặt ở bước 4.3:
   ```
   type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@<EVE_IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   ```
   Lần đầu kết nối, ssh sẽ hỏi `Are you sure you want to continue connecting`, gõ `yes`.
4. Thử đăng nhập:
   ```
   ssh root@<EVE_IP>
   ```
   Vào được mà không bị hỏi mật khẩu là xong.

> **Cần làm bước 3 trước bước 7.** Khi tạo image, script `lab/eve-make-image.sh` chép các khóa đang được phép vào EVE vào image của các node. Nhờ vậy, từ Windows cũng SSH thẳng được vào từng node.

---

## 6. Đưa mã nguồn vào EVE

Có 2 cách. **Nên dùng cách A.**

### Cách A: clone bằng git ngay trong EVE

Cách này giữ đúng định dạng file Linux, gồm xuống dòng kiểu LF và quyền chạy của các file `.sh`.

Trong phiên `ssh root@<EVE_IP>`:

```
apt-get update
apt-get install -y git
git clone -b v4 https://github.com/hdnguyen02/onejack.git /root/onejack
```

Lưu ý:
- Nhánh dùng cho demo là **`v4`**. Trước khi clone, đảm bảo máy đang code đã `git push` nhánh này lên GitHub.
- Nếu repo để **private**, git sẽ hỏi username và password. Ô password **không** nhập mật khẩu GitHub mà nhập **Personal Access Token**: vào GitHub → Settings → Developer settings → Personal access tokens để tạo.

### Cách B: copy thư mục từ Windows sang

Dùng khi đã có sẵn thư mục `onejack` trên Windows, ví dụ nhận qua USB hoặc file zip.

1. Trong PowerShell, `cd` tới **thư mục cha** của `onejack`, rồi chạy:
   ```
   scp -r onejack root@<EVE_IP>:/root/
   ```
2. SSH vào EVE và sửa định dạng file. **Bắt buộc**, vì Windows có thể đã đổi xuống dòng thành CRLF và làm mất quyền chạy:
   ```
   cd /root/onejack
   sed -i 's/\r$//' lab/*.sh lab/nodes.conf scripts/*.sh Makefile
   chmod +x lab/*.sh scripts/*.sh
   rm -rf build
   ```

> Nếu bỏ qua bước 2, lỗi sẽ có dạng `/bin/bash^M: bad interpreter`, `$'\r': command not found` hoặc `Permission denied`.

---

## 7. Build và dựng lab (làm một lần)

Mọi lệnh dưới đây chạy **trong EVE**, trong thư mục `/root/onejack`:

```
ssh root@<EVE_IP>
cd /root/onejack
```

### 7.1. Cài công cụ

```
apt-get update
apt-get install -y build-essential tmux gnuplot-nox
```

| Gói | Dùng để |
|---|---|
| `build-essential` | gcc, make, thư viện C tĩnh để build 3 chương trình |
| `tmux` | màn hình demo chia 4 ô |
| `gnuplot-nox` | vẽ biểu đồ kết quả |

### 7.2. Build và chạy unit test

```
make && make test
```

Kết quả đúng: thư mục `build/` có 3 file `server`, `client`, `loadgen`, và `make test` chạy hết mà không báo lỗi.

Các chương trình được biên dịch **tĩnh** (`-static`) nên chép vào node Alpine là chạy được ngay, không cần cài thêm thư viện.

### 7.3. Tạo image Alpine cho các node (khoảng 2 phút, cần Internet)

```
bash lab/eve-make-image.sh
```

Script này tải công cụ `alpine-make-vm-image`, tạo một ổ đĩa Alpine Linux có sẵn `openssh`, `iproute2` (lệnh `ip`, `tc`), rồi đặt vào `/opt/unetlab/addons/qemu/linux-alpine-demo/`.

Kết quả đúng: dòng cuối là `Đã tạo image: .../virtioa.qcow2`.

### 7.4. Tạo lab 6 node trong EVE

```
bash lab/eve-create-lab.sh
```

Script gọi API của EVE để tạo lab `net-perf` gồm 6 node, 6 mạng, rồi bật các node lên. Script cũng gán IP `172.30.0.1` cho cổng `pnet1` của EVE, dùng làm mạng quản lý để SSH vào node.

Kết quả đúng: dòng cuối là `Lab net-perf đã tạo và khởi động...`.

Mở `http://<EVE_IP>` trên trình duyệt → File manager → mở lab **net-perf** để xem sơ đồ mạng.

### 7.5. Cấu hình node và kiểm tra

```
scripts/lab-up.sh
```

Script bật 6 node, chờ các node nhận IP, chép chương trình và cấu hình vào từng node, rồi kiểm tra kết nối. Mất khoảng 40 giây tới 2 phút.

Kết quả đúng: dòng cuối là **`SẴN SÀNG`**. Nếu ra `LỖI: <bước>`, xem mục 10.

---

## 8. Chạy demo (mỗi lần bật máy)

### 8.1. Khởi động

1. Mở VMware, bấm **Power on** máy `eve-ng`, đợi khoảng 1 phút.
2. Mở PowerShell:
   ```
   ssh root@<EVE_IP>
   cd /root/onejack
   scripts/lab-up.sh
   ```
   Phải thấy **`SẴN SÀNG`**.

> IP của EVE do NAT của VMware cấp, thường giữ nguyên sau mỗi lần khởi động lại. Nếu không SSH được, xem lại IP trên màn hình máy EVE trong VMware.

### 8.2. Chạy 3 lượt

Mỗi lượt dài 60 giây, tải nặng bắt đầu ở giây 15. Chạy xong một lượt thì gõ `exit` để thoát màn hình tmux.

```
scripts/tmux-demo.sh base        # mọi lưu lượng đi đường dài R1 -> R2 -> R3
scripts/tmux-demo.sh short       # mọi lưu lượng đi đường ngắn R1 -> R3
scripts/tmux-demo.sh balance     # chia tải ra hai đường
```

Màn hình chia 4 ô:

| Vị trí | Hiển thị |
|---|---|
| Trên trái | RTT, jitter, mất gói của client |
| Dưới trái | Lưu lượng R1 gửi ra đường dài và đường ngắn (Mbit/s) |
| Trên phải | Thông lượng server nhận được (Mbit/s) |
| Dưới phải | Tiến trình `demo.sh`: đường đi đang dùng, lúc bắt đầu tải |

Kết quả mong đợi:
- **base:** trước giây 15 RTT khoảng 44 ms, sau giây 15 lên khoảng 450 ms.
- **short:** trước giây 15 RTT khoảng 22 ms, sau giây 15 vẫn lên khoảng 420 ms.
- **balance:** RTT khoảng 33 ms cả trước lẫn sau giây 15, tải chia ra hai đường mỗi đường khoảng 6 Mbit/s.

Muốn chạy cả 3 lượt liền một lèo mà không mở màn hình demo: `scripts/run-all.sh`.

Phím tắt tmux: **Ctrl+B** rồi **D** để thoát màn hình nhưng vẫn để chạy nền. Vào lại bằng `tmux attach`.

### 8.3. Vẽ biểu đồ và in bảng so sánh

```
scripts/plot.sh
```

Biểu đồ được lưu ở `results/rtt.png`, `results/rtt_low.png`, `results/jitter.png`, `results/throughput.png`, `results/paths.png`. Để lấy về Windows, mở một PowerShell **mới** (không phải phiên đang ssh) rồi chạy:

```
scp root@<EVE_IP>:/root/onejack/results/*.png .
```

### 8.4. Dọn dẹp

```
scripts/reset.sh     # dừng mọi chương trình đo trên các node
```

Khi xong việc: tắt máy EVE bằng lệnh `poweroff` trong EVE, hoặc bấm **Suspend** trong VMware để lần sau mở nhanh hơn.

---

## 9. Phương án dự phòng: mini-lab không cần node EVE

Nếu các node EVE gặp lỗi, ví dụ máy yếu hoặc ảo hóa lồng nhau không chạy, ta vẫn demo được bằng **network namespace**. Cách này dựng cùng mô hình mạng ngay trong máy EVE mà không cần máy ảo con nào. Vẫn cần làm xong bước 7.1 và 7.2.

```
cd /root/onejack
lab/netns-up.sh
LAB=netns scripts/lab-up.sh
LAB=netns scripts/tmux-demo.sh base
LAB=netns scripts/tmux-demo.sh short
LAB=netns scripts/tmux-demo.sh balance
scripts/plot.sh
lab/netns-down.sh     # xóa mini-lab khi xong
```

---

## 10. Xử lý lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách sửa |
|---|---|---|
| VMware báo *"Virtualized Intel VT-x/EPT is not supported on this platform"* | Hyper-V hoặc Memory integrity vẫn đang bật | Làm lại bước 2, khởi động lại máy, kiểm tra bằng `systeminfo` |
| `egrep -c '(vmx\|svm)' /proc/cpuinfo` ra `0` | Chưa tick VT-x trong VMware hoặc BIOS chưa bật ảo hóa | Tắt máy EVE, tick ô ở bước 4.2, kiểm tra BIOS |
| `ssh: connect to host ... Connection timed out` | Sai IP hoặc máy EVE chưa bật xong | Xem IP trên màn hình máy EVE trong VMware |
| `bad interpreter`, `$'\r': command not found` | File bị xuống dòng kiểu Windows (CRLF) | Chạy lại lệnh `sed` ở cách B, bước 6 |
| `Permission denied` khi chạy `scripts/...` | File `.sh` mất quyền chạy | `chmod +x lab/*.sh scripts/*.sh` |
| `make` báo `cannot find -lc` | Thiếu thư viện C tĩnh | `apt-get install -y build-essential` |
| `eve-make-image.sh` lỗi khi `wget` | EVE không có Internet | Kiểm tra mạng NAT của VMware, thử `ping 8.8.8.8` trong EVE |
| `lab-up.sh` báo `LỖI: chỉ x/6 node SSH được` | Node chưa khởi động xong hoặc không chạy được | Chờ thêm rồi chạy lại. Mở web EVE xem node có màu xanh không. Nếu node không lên, dùng mục 9 |
| `lab-up.sh` báo `LỖI: RAM trống dưới 500MB` | Máy EVE thiếu RAM | Tắt bớt ứng dụng, hoặc tăng RAM cho máy EVE trong VMware |
| Node lên nhưng rất chậm | Máy thật thiếu RAM hoặc đang mở nhiều ứng dụng nặng | Tắt trình duyệt nhiều tab và IDE, tăng RAM cho máy EVE |
| `lab-up.sh` báo `LỖI: r1 không cấu hình được đường đi ...` | Lab cũ (trước bản v4) chưa có đường ngắn R1 – R3 | Chạy lại `bash lab/eve-create-lab.sh` rồi `scripts/lab-up.sh` |
| Kết quả demo lạ | Lượt trước bị ngắt giữa chừng | `scripts/reset.sh` rồi `scripts/lab-up.sh` |

---

## 11. Tóm tắt nhanh

**Cài lần đầu:**

```
# Windows: tắt Hyper-V → cài VMware → tạo VM EVE (NAT, tick VT-x) → cài EVE
# PowerShell:
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@<EVE_IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
ssh root@<EVE_IP>

# Trong EVE:
apt-get update && apt-get install -y git build-essential tmux gnuplot-nox
git clone -b v4 https://github.com/hdnguyen02/onejack.git /root/onejack
cd /root/onejack
make && make test
bash lab/eve-make-image.sh
bash lab/eve-create-lab.sh
scripts/lab-up.sh            # → SẴN SÀNG
```

**Mỗi lần demo:**

```
ssh root@<EVE_IP>
cd /root/onejack && scripts/lab-up.sh
scripts/tmux-demo.sh base
scripts/tmux-demo.sh short
scripts/tmux-demo.sh balance
scripts/plot.sh
```

---

## 12. Cập nhật từ bản cũ lên bản hiện tại

Dùng khi máy EVE đã cài và chạy được bản cũ (lab `collab-defense`, các lượt `off` / `on` / `inband`). Bản hiện tại khác bản cũ ở mấy điểm:

| | Bản cũ | Bản hiện tại |
|---|---|---|
| Nhánh git | `v2` | `v4` |
| Tên lab trong EVE | `collab-defense` | `net-perf` |
| Mô hình | R1 → R2 → R3 một đường, thêm mạng điều khiển R1–R2–R3 | Hai đường: đường dài R1 → R2 → R3 và đường ngắn R1 → R3 |
| Chương trình | `server`, `client`, `attacker`, `guard` | `server`, `client`, `loadgen` |
| Các lượt demo | `off`, `on`, `inband` | `base`, `short`, `balance` |
| Kiểm chứng QoS | `scripts/qos-check.sh` | Không còn |

Vì cách nối dây giữa các router đã đổi, **phải tạo lại lab một lần**. Image Alpine giữ nguyên, không cần tạo lại.

Trong phiên `ssh root@<EVE_IP>`:

```
cd /root/onejack
git fetch
git checkout v4                # hoặc git pull nếu đang ở sẵn nhánh v4
make clean && make && make test
bash lab/eve-create-lab.sh     # dừng lab collab-defense, tạo lab net-perf và bật 6 node
scripts/lab-up.sh              # → SẴN SÀNG
```

Nếu đã copy code bằng cách B (bước 6) thay vì git, copy lại cả thư mục `onejack` rồi chạy lại các lệnh `sed`, `chmod`, `rm -rf build` ở cách B trước khi chạy các lệnh trên.

Lab cũ `collab-defense` chỉ bị dừng, không bị xóa, vẫn thấy trong File manager của EVE. **Không bật lab cũ cùng lúc với lab mới**, vì node của hai lab dùng chung địa chỉ quản lý 172.30.0.11 tới .16.

Sau đó chạy demo như mục 8.
