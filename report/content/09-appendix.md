#! PHỤ LỤC

**A. Hướng dẫn chạy demo**

Mọi lệnh dưới đây chạy trong máy ảo EVE-NG, thư mục `/root/onejack`. Hướng dẫn cài đặt đầy đủ nằm trong tệp `README.md` của mã nguồn.

```
make && make test                   # build 4 chương trình C và chạy kiểm thử đơn vị
bash lab/eve-make-image.sh          # tạo image Alpine cho node (chạy một lần)
bash lab/eve-create-lab.sh          # tạo lab collab-defense 6 node (chạy một lần)
scripts/lab-up.sh                   # chuẩn bị lab, phải in SẴN SÀNG
scripts/tmux-demo.sh off            # lượt không hợp tác
scripts/tmux-demo.sh on             # lượt hợp tác qua mạng điều khiển riêng
scripts/tmux-demo.sh inband         # lượt hợp tác chung đường, ưu tiên QoS
scripts/qos-check.sh                # kiểm chứng làn ưu tiên
scripts/plot.sh                     # bảng tóm tắt và biểu đồ
```

**B. Hàm check_rates của chương trình guard**

Hàm được gọi mỗi giây ở router làm nhiệm vụ phát hiện (trích nguyên văn từ `src/guard.c`).

```
// Mỗi giây: tìm IP vượt ngưỡng, chặn, gửi cảnh báo.
static void check_rates(uint32_t threshold)
{
    uint32_t ips[RC_MAX];
    uint32_t counts[RC_MAX];
    int n = rc_over(&rc, threshold, ips, counts, RC_MAX);

    for (int i = 0; i < n; i++) {
        char buf[INET_ADDRSTRLEN];
        if (!bl_allowed_to_block(&bl, ips[i])) {
            log_line("BỎ QUA %s (whitelist), %u gói/s", ip_str(ips[i], buf), counts[i]);
            continue;
        }
        if (bl_add(&bl, ips[i]) == 0) {
            continue;   // đã chặn rồi; AF_PACKET vẫn thấy gói vì bắt trước iptables
        }
        if (fw_block(ips[i]) != 0) {
            log_line("LỖI: không chặn được %s bằng iptables", ip_str(ips[i], buf));
            continue;
        }

        if (peer_count > 0) {
            char peer_list[160];
            send_alerts(ips[i], peer_list, sizeof(peer_list));
            log_line("PHÁT HIỆN %s (%u gói/s) → CHẶN, gửi cảnh báo tới %s",
                     ip_str(ips[i], buf), counts[i], peer_list);
        } else {
            log_line("PHÁT HIỆN %s (%u gói/s) → CHẶN", ip_str(ips[i], buf), counts[i]);
        }
    }
    rc_reset(&rc);
}
```

**C. Kế hoạch thực hiện**

Bảng: Kế hoạch thực hiện khóa luận
| Thời gian | Công việc | Kết quả |
|---|---|---|
| 11/11/2026 | Phân tích đề tài, thiết kế; viết các chương trình C và kiểm thử đơn vị; dựng mini-lab bằng network namespace | Chương trình chạy đúng trên mini-lab |
| 12/11/2026 | Cài EVE-NG trên KVM; tạo image Alpine và lab bằng API; viết script chuẩn bị lab, màn hình demo, vẽ biểu đồ | Ba lượt đầu tiên chạy được trên EVE-NG |
| 14/11/2026 | Thêm lượt inband với QoS; đo lại toàn bộ số liệu; viết báo cáo | Bộ số liệu dùng trong báo cáo |
| [15/11 – 05/12/2026] | [Hoàn thiện báo cáo theo góp ý của giáo viên hướng dẫn] | [ ] |
| Trước 06/12/2026 | Nộp báo cáo cho giáo viên hướng dẫn | |
| 07/12 – 18/12/2026 | Bộ môn phản biện đánh giá đề tài | |
| 23/12/2026 | Báo cáo trước hội đồng | |

**D. Nhật ký làm việc**

Bảng: Nhật ký làm việc
| Ngày | Nội dung đã làm | Ghi chú |
|---|---|---|
| 11/11/2026 | Viết Makefile, bộ kiểm thử, module giao thức; viết server, client, attacker; viết các module của guard và chương trình guard; viết cấu hình node và mini-lab bằng namespace | Mini-lab chạy được lượt off và on |
| 12/11/2026 | Cài KVM và EVE-NG; tạo image Alpine; tạo lab bằng REST API; sửa lỗi lượt demo bị treo trên Alpine, lỗi trùng địa chỉ quản lý và lỗi thứ tự log; viết script chuẩn bị lab, màn hình tmux, vẽ biểu đồ và README | Ba lượt chạy ổn định trên EVE-NG, kiểm tra lại sau khi khởi động lại máy ảo |
| 14/11/2026 | Thêm hàng đợi hai làn, cờ `-Q`, lượt inband và script kiểm chứng QoS; đo lại toàn bộ số liệu; viết báo cáo | |
| [...] | [...] | [...] |
