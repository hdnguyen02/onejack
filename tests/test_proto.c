#include <string.h>
#include "check.h"
#include "proto.h"

static void test_format_and_parse_roundtrip(void)
{
    char buf[64];
    int n = proto_format(buf, sizeof(buf), 'Q', 7, 123456);
    CHECK(n == (int)strlen("Q 7 123456"));
    CHECK(strcmp(buf, "Q 7 123456") == 0);

    char kind = 0;
    uint32_t seq = 0;
    uint64_t ts = 0;
    CHECK(proto_parse(buf, (size_t)n, &kind, &seq, &ts) == 0);
    CHECK(kind == 'Q');
    CHECK(seq == 7);
    CHECK(ts == 123456);
}

static void test_parse_answer(void)
{
    char kind = 0;
    uint32_t seq = 0;
    uint64_t ts = 0;
    CHECK(proto_parse("A 42 999", 8, &kind, &seq, &ts) == 0);
    CHECK(kind == 'A');
    CHECK(seq == 42);
    CHECK(ts == 999);
}

static void test_parse_with_padding(void)
{
    // Gói của attacker: phần đầu hợp lệ, phía sau đệm tới 1000 byte, không có '\0'.
    char pkt[1000];
    memset(pkt, 'x', sizeof(pkt));
    memcpy(pkt, "Q 1 5 ", 6);

    char kind = 0;
    uint32_t seq = 0;
    uint64_t ts = 0;
    CHECK(proto_parse(pkt, sizeof(pkt), &kind, &seq, &ts) == 0);
    CHECK(kind == 'Q');
    CHECK(seq == 1);
    CHECK(ts == 5);
}

static void test_parse_rejects_bad_input(void)
{
    char kind;
    uint32_t seq;
    uint64_t ts;
    CHECK(proto_parse("", 0, &kind, &seq, &ts) == -1);
    CHECK(proto_parse("Z 1 2", 5, &kind, &seq, &ts) == -1);
    CHECK(proto_parse("Q abc 2", 7, &kind, &seq, &ts) == -1);
    CHECK(proto_parse("Q 1", 3, &kind, &seq, &ts) == -1);
}

static void test_now_us_increases(void)
{
    uint64_t a = now_us();
    uint64_t b = now_us();
    CHECK(a > 0);
    CHECK(b >= a);
}

int main(void)
{
    test_format_and_parse_roundtrip();
    test_parse_answer();
    test_parse_with_padding();
    test_parse_rejects_bad_input();
    test_now_us_increases();
    printf("test_proto: OK\n");
    return 0;
}
