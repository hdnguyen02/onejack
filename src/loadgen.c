// loadgen: máy tạo tải nặng (mô phỏng tải file, xem video...) gửi tới server.
// Gửi gói UDP "D <seq> xxxx..." với tốc độ cố định, chia đều cho nhiều luồng.
// Mỗi luồng là một socket có cổng nguồn riêng (cổng gốc + i), nhờ vậy router
// dùng định tuyến nhiều đường có thể đưa các luồng khác nhau sang các đường khác nhau.
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

#define MAX_FLOWS 32

int main(int argc, char **argv)
{
    const char *server_ip = NULL;
    int port = QUERY_PORT;
    int rate = 5000;
    int size = 1000;
    int duration = 45;
    int flows = 8;
    int base_port = 20000;

    int opt;
    while ((opt = getopt(argc, argv, "s:p:r:l:d:f:b:")) != -1) {
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
        } else if (opt == 'f') {
            flows = atoi(optarg);
        } else if (opt == 'b') {
            base_port = atoi(optarg);
        } else {
            server_ip = NULL;
            break;
        }
    }
    if (server_ip == NULL || rate <= 0 || duration <= 0 || size < 32 || size > 1400
        || flows < 1 || flows > MAX_FLOWS || base_port < 1024 || base_port + flows > 65535) {
        fprintf(stderr,
                "Cách dùng: %s -s <server_ip> [-p 9000] [-r 5000 gói/s] [-l 1000 byte (32..1400)]\n"
                "           [-d 45 giây] [-f 8 luồng (1..%d)] [-b 20000 cổng nguồn đầu tiên]\n",
                argv[0], MAX_FLOWS);
        return 1;
    }

    struct sockaddr_in to;
    memset(&to, 0, sizeof(to));
    to.sin_family = AF_INET;
    to.sin_port = htons((uint16_t)port);
    if (inet_pton(AF_INET, server_ip, &to.sin_addr) != 1) {
        fprintf(stderr, "IP server không hợp lệ: %s\n", server_ip);
        return 1;
    }

    // Mỗi luồng một socket, gắn cố định cổng nguồn để lần chạy nào cũng chia đường giống nhau.
    int fds[MAX_FLOWS];
    for (int i = 0; i < flows; i++) {
        fds[i] = socket(AF_INET, SOCK_DGRAM, 0);
        if (fds[i] < 0) {
            perror("socket");
            return 1;
        }
        int one = 1;
        setsockopt(fds[i], SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

        struct sockaddr_in from;
        memset(&from, 0, sizeof(from));
        from.sin_family = AF_INET;
        from.sin_addr.s_addr = htonl(INADDR_ANY);
        from.sin_port = htons((uint16_t)(base_port + i));
        if (bind(fds[i], (struct sockaddr *)&from, sizeof(from)) < 0) {
            perror("bind cổng nguồn");
            return 1;
        }
        if (connect(fds[i], (struct sockaddr *)&to, sizeof(to)) < 0) {
            perror("connect");
            return 1;
        }
    }

    char pkt[1400];
    memset(pkt, 'x', sizeof(pkt));

    printf("[loadgen] tải %s:%d, %d gói/s × %d byte (%.1f Mbit/s), %d luồng, trong %d giây\n",
           server_ip, port, rate, size, rate * size * 8 / 1e6, flows, duration);
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

        // Gửi bù cho đủ số gói đáng lẽ phải gửi tới thời điểm này, lần lượt qua từng luồng.
        uint64_t target = (now - start) * (uint64_t)rate / 1000000ULL;
        while (total < target) {
            seq++;
            int head = snprintf(pkt, sizeof(pkt), "D %u", seq);
            if (head > 0 && head < size) {
                pkt[head] = ' ';   // ghi đè '\0' để phần đệm 'x' nối liền phía sau
            }
            send(fds[total % (uint64_t)flows], pkt, (size_t)size, 0);
            total++;
            sent_this_second++;
        }

        if (now >= next_tick) {
            t++;
            printf("[loadgen] t=%2d đã gửi %llu gói\n", t, (unsigned long long)sent_this_second);
            fflush(stdout);
            sent_this_second = 0;
            next_tick += 1000000;
        }

        nanosleep(&one_ms, NULL);
    }

    printf("[loadgen] xong, tổng %llu gói\n", (unsigned long long)total);
    return 0;
}
