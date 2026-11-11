#include "ratecount.h"

#include <string.h>

void rc_init(struct ratecount *rc)
{
    memset(rc, 0, sizeof(*rc));
}

void rc_add(struct ratecount *rc, uint32_t ip)
{
    for (int i = 0; i < rc->size; i++) {
        if (rc->ip[i] == ip) {
            rc->count[i]++;
            return;
        }
    }
    if (rc->size < RC_MAX) {
        rc->ip[rc->size] = ip;
        rc->count[rc->size] = 1;
        rc->size++;
    }
}

int rc_over(const struct ratecount *rc, uint32_t threshold, uint32_t *ips, uint32_t *counts, int cap)
{
    int n = 0;
    for (int i = 0; i < rc->size && n < cap; i++) {
        if (rc->count[i] > threshold) {
            ips[n] = rc->ip[i];
            counts[n] = rc->count[i];
            n++;
        }
    }
    return n;
}

void rc_reset(struct ratecount *rc)
{
    rc->size = 0;
}
