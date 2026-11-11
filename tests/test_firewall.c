#include <arpa/inet.h>
#include <string.h>
#include "check.h"
#include "firewall.h"

static void test_block_builds_iptables_command(void)
{
    fw_set_dry_run(1);
    struct in_addr a;
    inet_pton(AF_INET, "10.0.1.10", &a);
    CHECK(fw_block(a.s_addr) == 0);
    CHECK(strcmp(fw_last_cmd(), "iptables -A GUARD -s 10.0.1.10 -j DROP") == 0);
}

static void test_cleanup_deletes_chain(void)
{
    fw_set_dry_run(1);
    CHECK(fw_cleanup() == 0);
    CHECK(strcmp(fw_last_cmd(), "iptables -X GUARD") == 0);
}

int main(void)
{
    test_block_builds_iptables_command();
    test_cleanup_deletes_chain();
    printf("test_firewall: OK\n");
    return 0;
}
