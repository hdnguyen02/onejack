#include "alert.h"

#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>

int alert_format(char *buf, size_t cap, uint32_t ip, const char *node)
{
    char ipstr[INET_ADDRSTRLEN];
    struct in_addr a = { .s_addr = ip };
    inet_ntop(AF_INET, &a, ipstr, sizeof(ipstr));

    int n = snprintf(buf, cap, "BLOCK %s %s", ipstr, node);
    if (n < 0 || (size_t)n >= cap) {
        return -1;
    }
    return n;
}

static int is_node_char(char c)
{
    if (c >= 'A' && c <= 'Z') {
        return 1;
    }
    if (c >= 'a' && c <= 'z') {
        return 1;
    }
    if (c >= '0' && c <= '9') {
        return 1;
    }
    return c == '_' || c == '-';
}

int alert_parse(const char *buf, size_t len, uint32_t *ip, char *node, size_t node_cap)
{
    // Copy sang buffer có '\0', bỏ ký tự xuống dòng ở cuối.
    char msg[64];
    if (len == 0 || len >= sizeof(msg)) {
        return -1;
    }
    memcpy(msg, buf, len);
    msg[len] = '\0';
    while (len > 0 && (msg[len - 1] == '\n' || msg[len - 1] == '\r')) {
        len--;
        msg[len] = '\0';
    }

    if (strncmp(msg, "BLOCK ", 6) != 0) {
        return -1;
    }

    // Phần IP: từ sau "BLOCK " tới dấu cách tiếp theo.
    char *ip_start = msg + 6;
    char *space = strchr(ip_start, ' ');
    if (space == NULL) {
        return -1;
    }
    *space = '\0';

    struct in_addr a;
    if (inet_pton(AF_INET, ip_start, &a) != 1) {
        return -1;
    }

    // Phần tên node: chỉ cho phép [A-Za-z0-9_-], không được có gì phía sau.
    char *name = space + 1;
    size_t name_len = strlen(name);
    if (name_len == 0 || name_len > ALERT_NODE_MAX || name_len >= node_cap) {
        return -1;
    }
    for (size_t i = 0; i < name_len; i++) {
        if (!is_node_char(name[i])) {
            return -1;
        }
    }

    *ip = a.s_addr;
    memcpy(node, name, name_len + 1);
    return 0;
}
