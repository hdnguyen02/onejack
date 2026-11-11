#include <arpa/inet.h>
#include "check.h"
#include "blocklist.h"

static uint32_t ip(const char *s)
{
    struct in_addr a;
    inet_pton(AF_INET, s, &a);
    return a.s_addr;
}

static struct blocklist bl;

static void test_add_is_deduplicated(void)
{
    bl_init(&bl);
    CHECK(bl_add(&bl, ip("10.0.1.10")) == 1);
    CHECK(bl_add(&bl, ip("10.0.1.10")) == 0);
}

static void test_control_network_never_blocked(void)
{
    bl_init(&bl);
    CHECK(bl_allowed_to_block(&bl, ip("10.0.99.2")) == 0);
    CHECK(bl_allowed_to_block(&bl, ip("10.0.99.255")) == 0);
}

static void test_whitelist_never_blocked(void)
{
    bl_init(&bl);
    CHECK(bl_whitelist(&bl, ip("10.0.3.10")) == 0);
    CHECK(bl_allowed_to_block(&bl, ip("10.0.3.10")) == 0);
}

static void test_attacker_can_be_blocked(void)
{
    bl_init(&bl);
    bl_whitelist(&bl, ip("10.0.3.10"));
    CHECK(bl_allowed_to_block(&bl, ip("10.0.1.10")) == 1);
}

int main(void)
{
    test_add_is_deduplicated();
    test_control_network_never_blocked();
    test_whitelist_never_blocked();
    test_attacker_can_be_blocked();
    printf("test_blocklist: OK\n");
    return 0;
}
