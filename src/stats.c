#include "stats.h"

#include <string.h>

void stats_init(struct stats *s)
{
    memset(s, 0, sizeof(*s));
}

void stats_on_send(struct stats *s, uint32_t seq, uint64_t t_us)
{
    struct stats_slot *slot = &s->slot[seq % STATS_SLOTS];

    // Slot cũ vẫn đang chờ mà bị ghi đè: coi như gói cũ đã mất.
    if (slot->state == SLOT_PENDING) {
        s->lost++;
    }

    slot->seq = seq;
    slot->sent_us = t_us;
    slot->state = SLOT_PENDING;
    s->sent++;
}

void stats_on_reply(struct stats *s, uint32_t seq, uint64_t t_us)
{
    struct stats_slot *slot = &s->slot[seq % STATS_SLOTS];

    // Bỏ qua trả lời lạ hoặc trả lời lặp lại.
    if (slot->state != SLOT_PENDING || slot->seq != seq) {
        return;
    }

    // Trả lời tới muộn: để stats_tick tính là mất.
    uint64_t rtt = t_us - slot->sent_us;
    if (rtt > STATS_TIMEOUT_US) {
        return;
    }

    slot->state = SLOT_DONE;
    s->recv++;
    s->rtt_sum_us += rtt;
}

void stats_tick(struct stats *s, uint64_t now, struct stats_row *out)
{
    // Truy vấn nào quá hạn mà chưa có trả lời thì tính là mất.
    for (int i = 0; i < STATS_SLOTS; i++) {
        struct stats_slot *slot = &s->slot[i];
        if (slot->state == SLOT_PENDING && now - slot->sent_us > STATS_TIMEOUT_US) {
            slot->state = SLOT_DONE;
            s->lost++;
        }
    }

    out->sent = s->sent;
    out->recv = s->recv;

    uint32_t finished = s->recv + s->lost;
    if (finished > 0) {
        out->loss_pct = 100.0 * s->lost / finished;
    } else {
        out->loss_pct = 0.0;
    }

    if (s->recv > 0) {
        out->rtt_avg_ms = (double)s->rtt_sum_us / s->recv / 1000.0;
    } else {
        out->rtt_avg_ms = 0.0;
    }

    s->sent = 0;
    s->recv = 0;
    s->lost = 0;
    s->rtt_sum_us = 0;
}
