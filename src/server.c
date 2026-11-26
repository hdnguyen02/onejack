// server: nhận truy vấn UDP "Q <seq> <ts>" và trả lời "A <seq> <ts>".
// Gói tải "D ..." của loadgen chỉ được đếm, không trả lời.
// Mỗi giây in số gói, thông lượng nhận được (Mbit/s) và số gói theo từng IP nguồn.
// -o file.csv: ghi thêm CSV mỗi giây: t,recv_pkts,recv_mbit
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <poll.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "proto.h"

#define MAX_SOURCES 64

struct source {
    uint32_t ip;
    uint32_t count;
};

static struct source sources[MAX_SOURCES];
static int source_count = 0;

static void count_source(uint32_t ip)
{
    for (int i = 0; i < source_count; i++) {
        if (sources[i].ip == ip) {
            sources[i].count++;
            return;
        }
    }
    if (source_count < MAX_SOURCES) {
        sources[source_count].ip = ip;
        sources[source_count].count = 1;
        source_count++;
    }
}

static void print_second(int t, uint32_t recv, uint32_t replied, double mbit)
{
    printf("[server] t=%2d nhận=%u gói (%.2f Mbit/s) trả lời=%u nguồn=", t, recv, mbit, replied);
    for (int i = 0; i < source_count; i++) {
        char ip[INET_ADDRSTRLEN];
        struct in_addr a = { .s_addr = sources[i].ip };
        inet_ntop(AF_INET, &a, ip, sizeof(ip));
        if (i > 0) {
            printf(",");
        }
        printf("%s:%u", ip, sources[i].count);
    }
    printf("\n");
    fflush(stdout);
    source_count = 0;
}

int main(int argc, char **argv)
{
    int port = QUERY_PORT;
    const char *csv_path = NULL;
    int opt;
    while ((opt = getopt(argc, argv, "p:o:")) != -1) {
        if (opt == 'p') {
            port = atoi(optarg);
        } else if (opt == 'o') {
            csv_path = optarg;
        } else {
            fprintf(stderr, "Cách dùng: %s [-p port] [-o file.csv]\n", argv[0]);
            return 1;
        }
    }

    FILE *csv = NULL;
    if (csv_path != NULL) {
        csv = fopen(csv_path, "w");
        if (csv == NULL) {
            perror("fopen");
            return 1;
        }
        fprintf(csv, "t,recv_pkts,recv_mbit\n");
        fflush(csv);
    }

    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) {
        perror("socket");
        return 1;
    }

    // Tăng bộ đệm nhận để chịu được flood.
    int rcvbuf = 4 * 1024 * 1024;
    setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof(rcvbuf));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons((uint16_t)port);
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }

    printf("[server] đang nghe UDP cổng %d\n", port);
    fflush(stdout);

    uint64_t start = now_us();
    uint64_t next_tick = start + 1000000;
    int t = 0;
    uint32_t recv_count = 0;
    uint64_t recv_bytes = 0;
    uint32_t replied = 0;
    char buf[2048];

    while (true) {
        struct pollfd pfd = { .fd = fd, .events = POLLIN };
        poll(&pfd, 1, 100);

        if (pfd.revents & POLLIN) {
            // Đọc hết các gói đang chờ, nhưng vẫn quay lại kiểm tra mốc 1 giây.
            for (int i = 0; i < 1000; i++) {
                struct sockaddr_in from;
                socklen_t fromlen = sizeof(from);
                ssize_t n = recvfrom(fd, buf, sizeof(buf), MSG_DONTWAIT,
                                     (struct sockaddr *)&from, &fromlen);
                if (n < 0) {
                    break;
                }
                recv_count++;
                recv_bytes += (uint64_t)n;
                count_source(from.sin_addr.s_addr);

                char kind;
                uint32_t seq;
                uint64_t ts;
                if (proto_parse(buf, (size_t)n, &kind, &seq, &ts) == 0 && kind == 'Q') {
                    char reply[64];
                    int len = proto_format(reply, sizeof(reply), 'A', seq, ts);
                    if (len > 0 && sendto(fd, reply, (size_t)len, 0,
                                          (struct sockaddr *)&from, fromlen) == len) {
                        replied++;
                    }
                }
            }
        }

        uint64_t now = now_us();
        while (now >= next_tick) {
            t++;
            // Thông lượng tính theo phần dữ liệu UDP nhận được.
            double mbit = (double)recv_bytes * 8.0 / 1000000.0;
            print_second(t, recv_count, replied, mbit);
            if (csv != NULL) {
                fprintf(csv, "%d,%u,%.3f\n", t, recv_count, mbit);
                fflush(csv);
            }
            recv_count = 0;
            recv_bytes = 0;
            replied = 0;
            next_tick += 1000000;
        }
    }
}
