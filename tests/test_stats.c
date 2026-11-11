#include <math.h>
#include "check.h"
#include "stats.h"

static struct stats s;   // struct lớn, để static cho khỏi tràn stack

static int near(double a, double b)
{
    return fabs(a - b) < 0.01;
}

static void test_all_replied(void)
{
    stats_init(&s);
    for (uint32_t i = 1; i <= 20; i++) {
        stats_on_send(&s, i, 0);
    }
    for (uint32_t i = 1; i <= 20; i++) {
        stats_on_reply(&s, i, 5000);
    }
    struct stats_row r;
    stats_tick(&s, 2000000, &r);
    CHECK(r.sent == 20);
    CHECK(r.recv == 20);
    CHECK(near(r.loss_pct, 0.0));
    CHECK(near(r.rtt_avg_ms, 5.0));
}

static void test_half_lost_after_timeout(void)
{
    stats_init(&s);
    for (uint32_t i = 1; i <= 10; i++) {
        stats_on_send(&s, i, 0);
    }
    for (uint32_t i = 1; i <= 5; i++) {
        stats_on_reply(&s, i, 2000);
    }
    struct stats_row r;
    stats_tick(&s, 1500000, &r);
    CHECK(r.sent == 10);
    CHECK(r.recv == 5);
    CHECK(near(r.loss_pct, 50.0));
}

static void test_pending_not_lost_before_timeout(void)
{
    stats_init(&s);
    stats_on_send(&s, 1, 0);
    struct stats_row r;
    stats_tick(&s, 500000, &r);   // mới 0,5 giây: chưa tính là mất
    CHECK(r.recv == 0);
    CHECK(near(r.loss_pct, 0.0));
}

static void test_late_reply_counts_as_lost(void)
{
    stats_init(&s);
    stats_on_send(&s, 1, 0);
    stats_on_reply(&s, 1, 1500000);   // tới sau 1,5 giây
    struct stats_row r;
    stats_tick(&s, 1600000, &r);
    CHECK(r.recv == 0);
    CHECK(near(r.loss_pct, 100.0));
}

static void test_duplicate_reply_counted_once(void)
{
    stats_init(&s);
    stats_on_send(&s, 3, 0);
    stats_on_reply(&s, 3, 1000);
    stats_on_reply(&s, 3, 1200);
    struct stats_row r;
    stats_tick(&s, 2000000, &r);
    CHECK(r.recv == 1);
    CHECK(r.loss_pct <= 100.0);
    CHECK(near(r.rtt_avg_ms, 1.0));
}

static void test_reply_for_unknown_seq_ignored(void)
{
    stats_init(&s);
    stats_on_reply(&s, 99, 1000);
    struct stats_row r;
    stats_tick(&s, 2000000, &r);
    CHECK(r.recv == 0);
}

static void test_counters_reset_each_tick(void)
{
    stats_init(&s);
    stats_on_send(&s, 1, 0);
    stats_on_reply(&s, 1, 1000);
    struct stats_row r;
    stats_tick(&s, 1000000, &r);
    stats_tick(&s, 2000000, &r);
    CHECK(r.sent == 0);
    CHECK(r.recv == 0);
    CHECK(near(r.rtt_avg_ms, 0.0));
}

int main(void)
{
    test_all_replied();
    test_half_lost_after_timeout();
    test_pending_not_lost_before_timeout();
    test_late_reply_counts_as_lost();
    test_duplicate_reply_counted_once();
    test_reply_for_unknown_seq_ignored();
    test_counters_reset_each_tick();
    printf("test_stats: OK\n");
    return 0;
}
