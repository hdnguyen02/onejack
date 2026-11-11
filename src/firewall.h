// Gọi iptables qua fork + execvp (không dùng system()), dùng chain riêng GUARD.
#ifndef FIREWALL_H
#define FIREWALL_H

#include <stdint.h>

// Chế độ dry-run: chỉ ghi lại lệnh, không chạy (dùng cho unit test).
void fw_set_dry_run(int on);
const char *fw_last_cmd(void);

int fw_init(void);           // tạo/flush chain GUARD và gắn vào FORWARD
int fw_block(uint32_t ip);   // iptables -A GUARD -s <ip> -j DROP
int fw_cleanup(void);        // gỡ chain GUARD khỏi FORWARD rồi xóa

#endif
