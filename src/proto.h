// Giao thức đo đạc giữa các node.
//   Truy vấn của client: "Q <seq> <timestamp_us>", server trả lời "A <seq> <timestamp_us>".
//   Gói tải của loadgen: "D <seq> xxxx..." (đệm cho đủ kích thước), server chỉ đếm, không trả lời.
#ifndef PROTO_H
#define PROTO_H

#include <stddef.h>
#include <stdint.h>

#define QUERY_PORT 9000

// Thời gian hiện tại tính bằng micro giây (CLOCK_MONOTONIC).
uint64_t now_us(void);

// Ghi gói vào buf, trả về độ dài (không tính '\0'), hoặc -1 nếu lỗi.
int proto_format(char *buf, size_t cap, char kind, uint32_t seq, uint64_t ts_us);

// Đọc gói Q hoặc A. Trả về 0 nếu hợp lệ, -1 nếu sai định dạng. Cho phép có byte đệm phía sau.
int proto_parse(const char *buf, size_t len, char *kind, uint32_t *seq, uint64_t *ts_us);

#endif
