#include <arpa/inet.h>
#include <string.h>
#include "check.h"
#include "alert.h"

static uint32_t ip(const char *s)
{
    struct in_addr a;
    inet_pton(AF_INET, s, &a);
    return a.s_addr;
}

static int parse(const char *s, uint32_t *out_ip, char *node)
{
    return alert_parse(s, strlen(s), out_ip, node, 16);
}

static void test_format_and_parse_roundtrip(void)
{
    char buf[64];
    int n = alert_format(buf, sizeof(buf), ip("10.0.1.10"), "R3");
    CHECK(n > 0);
    CHECK(strcmp(buf, "BLOCK 10.0.1.10 R3") == 0);

    uint32_t got = 0;
    char node[16];
    CHECK(alert_parse(buf, (size_t)n, &got, node, sizeof(node)) == 0);
    CHECK(got == ip("10.0.1.10"));
    CHECK(strcmp(node, "R3") == 0);
}

static void test_rejects_malformed_alerts(void)
{
    uint32_t got;
    char node[16];
    CHECK(parse("BLOCK 1.2.3.4;rm -rf / R3", &got, node) == -1);
    CHECK(parse("BLOCK 999.1.1.1 R3", &got, node) == -1);
    CHECK(parse("BLOCK 1.2.3.4", &got, node) == -1);
    CHECK(parse("BLOCK 1.2.3.4 R3 extra", &got, node) == -1);
    CHECK(parse("HELLO 1.2.3.4 R3", &got, node) == -1);
    CHECK(parse("BLOCK 1.2.3.4 R3;ls", &got, node) == -1);
    CHECK(parse("BLOCK 1.2.3.4 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", &got, node) == -1);
    CHECK(parse("", &got, node) == -1);
}

static void test_accepts_trailing_newline(void)
{
    uint32_t got;
    char node[16];
    CHECK(parse("BLOCK 10.0.1.10 R1\n", &got, node) == 0);
    CHECK(strcmp(node, "R1") == 0);
}

int main(void)
{
    test_format_and_parse_roundtrip();
    test_rejects_malformed_alerts();
    test_accepts_trailing_newline();
    printf("test_alert: OK\n");
    return 0;
}
