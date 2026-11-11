// Thống kê theo giây cho client: số gói gửi/nhận, % mất gói, RTT trung bình.
#ifndef STATS_H
#define STATS_H

#include <stdint.h>

#define STATS_SLOTS 4096
#define STATS_TIMEOUT_US 1000000ULL   // quá 1 giây chưa có trả lời thì tính là mất

enum slot_state {
    SLOT_EMPTY = 0,
    SLOT_PENDING,
    SLOT_DONE
};

struct stats_slot {
    uint32_t seq;
    uint64_t sent_us;
    enum slot_state state;
};

struct stats {
    struct stats_slot slot[STATS_SLOTS];   // bảng vòng, vị trí = seq % STATS_SLOTS
    uint32_t sent;                          // các bộ đếm của giây hiện tại
    uint32_t recv;
    uint32_t lost;
    uint64_t rtt_sum_us;
};

struct stats_row {
    uint32_t sent;
    uint32_t recv;
    double loss_pct;
    double rtt_avg_ms;
};

void stats_init(struct stats *s);
void stats_on_send(struct stats *s, uint32_t seq, uint64_t t_us);
void stats_on_reply(struct stats *s, uint32_t seq, uint64_t t_us);

// Tổng kết một giây: đánh dấu các truy vấn quá hạn là mất, ghi kết quả vào out, rồi xóa bộ đếm.
void stats_tick(struct stats *s, uint64_t now, struct stats_row *out);

#endif
