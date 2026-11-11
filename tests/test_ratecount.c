#include <arpa/inet.h>
#include "check.h"
#include "ratecount.h"

static uint32_t ip(const char *s)
{
    struct in_addr a;
    inet_pton(AF_INET, s, &a);
    return a.s_addr;
}

static struct ratecount rc;

static void test_detects_only_ip_over_threshold(void)
{
    rc_init(&rc);
    for (int i = 0; i < 300; i++) {
        rc_add(&rc, ip("10.0.1.10"));
    }
    for (int i = 0; i < 20; i++) {
        rc_add(&rc, ip("10.0.1.20"));
    }
    uint32_t ips[8];
    uint32_t counts[8];
    int n = rc_over(&rc, 200, ips, counts, 8);
    CHECK(n == 1);
    CHECK(ips[0] == ip("10.0.1.10"));
    CHECK(counts[0] == 300);
}

static void test_exactly_threshold_is_not_over(void)
{
    rc_init(&rc);
    for (int i = 0; i < 200; i++) {
        rc_add(&rc, ip("10.0.1.10"));
    }
    uint32_t ips[8];
    uint32_t counts[8];
    CHECK(rc_over(&rc, 200, ips, counts, 8) == 0);
}

static void test_table_full_does_not_crash(void)
{
    rc_init(&rc);
    for (uint32_t i = 0; i < 300; i++) {
        rc_add(&rc, htonl(0x0A000000u + i));
    }
    CHECK(rc.size == RC_MAX);
}

static void test_reset_clears_counts(void)
{
    rc_init(&rc);
    for (int i = 0; i < 300; i++) {
        rc_add(&rc, ip("10.0.1.10"));
    }
    rc_reset(&rc);
    uint32_t ips[8];
    uint32_t counts[8];
    CHECK(rc_over(&rc, 200, ips, counts, 8) == 0);
    CHECK(rc.size == 0);
}

int main(void)
{
    test_detects_only_ip_over_threshold();
    test_exactly_threshold_is_not_over();
    test_table_full_does_not_crash();
    test_reset_clears_counts();
    printf("test_ratecount: OK\n");
    return 0;
}
