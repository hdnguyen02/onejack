// Đếm số gói theo IP nguồn trong 1 giây.
#ifndef RATECOUNT_H
#define RATECOUNT_H

#include <stdint.h>

#define RC_MAX 256

struct ratecount {
    uint32_t ip[RC_MAX];      // network byte order
    uint32_t count[RC_MAX];
    int size;
};

void rc_init(struct ratecount *rc);
// Khi bảng đã đủ RC_MAX IP thì IP mới bị bỏ qua.
void rc_add(struct ratecount *rc, uint32_t ip);
// Trả về số IP có count > threshold (ghi tối đa cap IP vào ips/counts).
int rc_over(const struct ratecount *rc, uint32_t threshold, uint32_t *ips, uint32_t *counts, int cap);
void rc_reset(struct ratecount *rc);

#endif
