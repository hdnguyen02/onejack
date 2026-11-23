// Giao thức truy vấn: "Q <seq> <timestamp_us>" và trả lời "A <seq> <timestamp_us>".
#ifndef PROTO_H
#define PROTO_H

#include <stddef.h>
#include <stdint.h>

#define QUERY_PORT 9000
#define ALERT_PORT 9999

// Giá trị byte TOS của gói được đánh dấu ưu tiên (QoS): DSCP EF = 46, dịch trái 2 bit = 0xB8.
// Router chia hàng đợi làm 2 làn, gói mang dấu này đi làn ưu tiên (xem lab/r1.sh).
#define TOS_PRIORITY 0xB8

// Thời gian hiện tại tính bằng micro giây (CLOCK_MONOTONIC).
uint64_t now_us(void);

// Ghi gói vào buf, trả về độ dài (không tính '\0'), hoặc -1 nếu lỗi.
int proto_format(char *buf, size_t cap, char kind, uint32_t seq, uint64_t ts_us);

// Đọc gói. Trả về 0 nếu hợp lệ, -1 nếu sai định dạng. Cho phép có byte đệm phía sau.
int proto_parse(const char *buf, size_t len, char *kind, uint32_t *seq, uint64_t *ts_us);

#endif
