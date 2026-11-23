#include "blocklist.h"

#include <arpa/inet.h>
#include <string.h>

void bl_init(struct blocklist *bl)
{
    memset(bl, 0, sizeof(*bl));
}

int bl_whitelist(struct blocklist *bl, uint32_t ip)
{
    if (bl->white_size >= BL_MAX) {
        return -1;
    }
    bl->white[bl->white_size] = ip;
    bl->white_size++;
    return 0;
}

int bl_allowed_to_block(const struct blocklist *bl, uint32_t ip)
{
    // Không bao giờ chặn mạng điều khiển 10.0.99.0/24.
    uint32_t host = ntohl(ip);
    if ((host & 0xFFFFFF00u) == 0x0A006300u) {
        return 0;
    }
    for (int i = 0; i < bl->white_size; i++) {
        if (bl->white[i] == ip) {
            return 0;
        }
    }
    return 1;
}

int bl_add(struct blocklist *bl, uint32_t ip)
{
    for (int i = 0; i < bl->blocked_size; i++) {
        if (bl->blocked[i] == ip) {
            return 0;
        }
    }
    if (bl->blocked_size >= BL_MAX) {
        return 0;
    }
    bl->blocked[bl->blocked_size] = ip;
    bl->blocked_size++;
    return 1;
}
