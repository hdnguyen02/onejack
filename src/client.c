// client: gửi truy vấn đều đặn tới server, mỗi giây in và ghi CSV:
// t,sent,recv,loss_pct,rtt_avg_ms
#include <arpa/inet.h>
#include <netinet/in.h>
#include <poll.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "proto.h"
#include "stats.h"

static struct stats st;

int main(int argc, char **argv)
{
    const char *server_ip = NULL;
    int port = QUERY_PORT;
    int rate = 20;
    int duration = 60;
    const char *csv_path = NULL;

    int opt;
    while ((opt = getopt(argc, argv, "s:p:r:d:o:")) != -1) {
        if (opt == 's') {
            server_ip = optarg;
        } else if (opt == 'p') {
            port = atoi(optarg);
        } else if (opt == 'r') {
            rate = atoi(optarg);
        } else if (opt == 'd') {
            duration = atoi(optarg);
        } else if (opt == 'o') {
            csv_path = optarg;
        } else {
            server_ip = NULL;
            break;
        }
    }
    if (server_ip == NULL || rate <= 0 || duration <= 0) {
        fprintf(stderr, "Cách dùng: %s -s <server_ip> [-p 9000] [-r 20] [-d 60] [-o file.csv]\n", argv[0]);
        return 1;
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    if (inet_pton(AF_INET, server_ip, &addr.sin_addr) != 1) {
        fprintf(stderr, "IP server không hợp lệ: %s\n", server_ip);
        return 1;
    }

    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0 || connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("socket/connect");
        return 1;
    }

    FILE *csv = NULL;
    if (csv_path != NULL) {
        csv = fopen(csv_path, "w");
        if (csv == NULL) {
            perror("fopen");
            return 1;
        }
        fprintf(csv, "t,sent,recv,loss_pct,rtt_avg_ms\n");
        fflush(csv);
    }

    stats_init(&st);
    uint64_t start = now_us();
    uint64_t interval = 1000000ULL / (uint64_t)rate;
    uint64_t next_send = start;
    uint64_t next_tick = start + 1000000;
    uint32_t seq = 0;
    int t = 0;
    char buf[256];

    while (t < duration) {
        uint64_t now = now_us();

        // Gửi truy vấn theo đúng nhịp.
        while (now >= next_send) {
            seq++;
            int len = proto_format(buf, sizeof(buf), 'Q', seq, now);
            stats_on_send(&st, seq, now);
            if (len > 0) {
                send(fd, buf, (size_t)len, 0);   // lỗi gửi cũng sẽ tính là mất gói
            }
            next_send += interval;
        }

        // Chờ trả lời tối đa 1ms.
        struct pollfd pfd = { .fd = fd, .events = POLLIN };
        if (poll(&pfd, 1, 1) > 0 && (pfd.revents & POLLIN)) {
            while (true) {
                ssize_t n = recv(fd, buf, sizeof(buf), MSG_DONTWAIT);
                if (n < 0) {
                    break;
                }
                char kind;
                uint32_t rseq;
                uint64_t ts;
                if (proto_parse(buf, (size_t)n, &kind, &rseq, &ts) == 0 && kind == 'A') {
                    stats_on_reply(&st, rseq, now_us());
                }
            }
        }

        now = now_us();
        if (now >= next_tick) {
            t++;
            struct stats_row r;
            stats_tick(&st, now, &r);
            printf("[client] t=%2d gửi=%u nhận=%u mất=%5.1f%% rtt=%7.2f ms\n",
                   t, r.sent, r.recv, r.loss_pct, r.rtt_avg_ms);
            fflush(stdout);
            if (csv != NULL) {
                fprintf(csv, "%d,%u,%u,%.1f,%.2f\n", t, r.sent, r.recv, r.loss_pct, r.rtt_avg_ms);
                fflush(csv);
            }
            next_tick += 1000000;
        }
    }

    if (csv != NULL) {
        fclose(csv);
    }
    return 0;
}
