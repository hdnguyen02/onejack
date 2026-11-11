// Danh sách IP đã chặn, whitelist, và kiểm tra mạng điều khiển (10.0.99.0/24).
#ifndef BLOCKLIST_H
#define BLOCKLIST_H

#include <stdint.h>

#define BL_MAX 256

struct blocklist {
    uint32_t blocked[BL_MAX];   // network byte order
    int blocked_size;
    uint32_t white[BL_MAX];
    int white_size;
};

void bl_init(struct blocklist *bl);
// Trả về 0 nếu thêm được, -1 nếu đầy.
int bl_whitelist(struct blocklist *bl, uint32_t ip);
// Trả về 0 nếu IP thuộc 10.0.99.0/24 hoặc nằm trong whitelist, ngược lại 1.
int bl_allowed_to_block(const struct blocklist *bl, uint32_t ip);
// Trả về 1 nếu IP vừa được thêm, 0 nếu đã có từ trước (hoặc danh sách đầy).
int bl_add(struct blocklist *bl, uint32_t ip);

#endif
