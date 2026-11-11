// Gói cảnh báo giữa các node: "BLOCK <ip> <tên_node>".
#ifndef ALERT_H
#define ALERT_H

#include <stddef.h>
#include <stdint.h>

#define ALERT_NODE_MAX 15

int alert_format(char *buf, size_t cap, uint32_t ip, const char *node);
// Trả về 0 nếu hợp lệ, -1 nếu sai. IP kiểm tra bằng inet_pton,
// tên node chỉ gồm [A-Za-z0-9_-], dài tối đa ALERT_NODE_MAX.
int alert_parse(const char *buf, size_t len, uint32_t *ip, char *node, size_t node_cap);

#endif
