#include "proto.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

uint64_t now_us(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000ULL + (uint64_t)ts.tv_nsec / 1000ULL;
}

int proto_format(char *buf, size_t cap, char kind, uint32_t seq, uint64_t ts_us)
{
    int n = snprintf(buf, cap, "%c %u %llu", kind, seq, (unsigned long long)ts_us);
    if (n < 0 || (size_t)n >= cap) {
        return -1;
    }
    return n;
}

int proto_parse(const char *buf, size_t len, char *kind, uint32_t *seq, uint64_t *ts_us)
{
    // Chỉ cần phần đầu của gói. Copy sang buffer có '\0' để sscanf an toàn
    // (gói nhận từ mạng không có ký tự kết thúc chuỗi).
    char head[64];
    size_t n = len;
    if (n > sizeof(head) - 1) {
        n = sizeof(head) - 1;
    }
    memcpy(head, buf, n);
    head[n] = '\0';

    char k;
    char seq_str[11];
    char ts_str[21];
    if (sscanf(head, "%c %10[0-9] %20[0-9]", &k, seq_str, ts_str) != 3) {
        return -1;
    }
    if (k != 'Q' && k != 'A') {
        return -1;
    }

    *kind = k;
    *seq = (uint32_t)strtoul(seq_str, NULL, 10);
    *ts_us = (uint64_t)strtoull(ts_str, NULL, 10);
    return 0;
}
