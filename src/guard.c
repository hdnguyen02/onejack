// guard: chạy trên router R1/R2/R3.
//   -d : phát hiện. Bắt gói trên interface -i, đếm gói UDP tới cổng 9000 theo IP nguồn.
//        IP nào vượt ngưỡng -t (gói/giây) thì chặn bằng iptables. Nếu có -P thì gửi cảnh báo cho peer.
//   -l : nghe cảnh báo "BLOCK <ip> <node>" trên <-b ip>:9999, nhận được thì chặn theo.
//   -Q : đánh dấu gói cảnh báo là ưu tiên (QoS), để router cho đi trước khi đường bị nghẽn.
#include <arpa/inet.h>
#include <errno.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <net/if.h>
#include <netinet/in.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include "alert.h"
#include "blocklist.h"
#include "firewall.h"
#include "proto.h"
#include "ratecount.h"

#define MAX_PEERS 8

static volatile sig_atomic_t stop = 0;

static const char *node_name = NULL;
static struct ratecount rc;
static struct blocklist bl;
static uint32_t peers[MAX_PEERS];
static int peer_count = 0;
static int alert_fd = -1;   // socket dùng để gửi và nhận cảnh báo

static void on_signal(int sig)
{
    (void)sig;
    stop = 1;
}

// In một dòng log có thời gian HH:MM:SS.mmm và tên node.
static void log_line(const char *fmt, ...)
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    struct tm tm;
    localtime_r(&ts.tv_sec, &tm);
    printf("%02d:%02d:%02d.%03ld [%s] ", tm.tm_hour, tm.tm_min, tm.tm_sec,
           ts.tv_nsec / 1000000, node_name);

    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);

    printf("\n");
    fflush(stdout);
}

static const char *ip_str(uint32_t ip, char *buf)
{
    struct in_addr a = { .s_addr = ip };
    inet_ntop(AF_INET, &a, buf, INET_ADDRSTRLEN);
    return buf;
}

static int parse_ip(const char *s, uint32_t *out)
{
    struct in_addr a;
    if (inet_pton(AF_INET, s, &a) != 1) {
        return -1;
    }
    *out = a.s_addr;
    return 0;
}

// Gửi cảnh báo tới mọi peer, trả về chuỗi tên peer để in log.
static void send_alerts(uint32_t ip, char *peer_list, size_t cap)
{
    char msg[64];
    int len = alert_format(msg, sizeof(msg), ip, node_name);
    peer_list[0] = '\0';
    if (len < 0) {
        return;
    }

    for (int i = 0; i < peer_count; i++) {
        struct sockaddr_in to;
        memset(&to, 0, sizeof(to));
        to.sin_family = AF_INET;
        to.sin_port = htons(ALERT_PORT);
        to.sin_addr.s_addr = peers[i];
        sendto(alert_fd, msg, (size_t)len, 0, (struct sockaddr *)&to, sizeof(to));

        char buf[INET_ADDRSTRLEN];
        if (i > 0) {
            strncat(peer_list, ",", cap - strlen(peer_list) - 1);
        }
        strncat(peer_list, ip_str(peers[i], buf), cap - strlen(peer_list) - 1);
    }
}

// Mỗi giây: tìm IP vượt ngưỡng, chặn, gửi cảnh báo.
static void check_rates(uint32_t threshold)
{
    uint32_t ips[RC_MAX];
    uint32_t counts[RC_MAX];
    int n = rc_over(&rc, threshold, ips, counts, RC_MAX);

    for (int i = 0; i < n; i++) {
        char buf[INET_ADDRSTRLEN];
        if (!bl_allowed_to_block(&bl, ips[i])) {
            log_line("BỎ QUA %s (whitelist), %u gói/s", ip_str(ips[i], buf), counts[i]);
            continue;
        }
        if (bl_add(&bl, ips[i]) == 0) {
            continue;   // đã chặn rồi; AF_PACKET vẫn thấy gói vì bắt trước iptables
        }
        if (fw_block(ips[i]) != 0) {
            log_line("LỖI: không chặn được %s bằng iptables", ip_str(ips[i], buf));
            continue;
        }

        if (peer_count > 0) {
            char peer_list[160];
            send_alerts(ips[i], peer_list, sizeof(peer_list));
            log_line("PHÁT HIỆN %s (%u gói/s) → CHẶN, gửi cảnh báo tới %s",
                     ip_str(ips[i], buf), counts[i], peer_list);
        } else {
            log_line("PHÁT HIỆN %s (%u gói/s) → CHẶN", ip_str(ips[i], buf), counts[i]);
        }
    }
    rc_reset(&rc);
}

// Xử lý một gói IP bắt được: nếu là UDP tới cổng 9000 thì đếm theo IP nguồn.
static void handle_packet(const unsigned char *pkt, ssize_t len)
{
    if (len < 20) {
        return;
    }
    if ((pkt[0] >> 4) != 4) {
        return;
    }
    int ihl = (pkt[0] & 0x0F) * 4;
    if (ihl < 20 || len < ihl + 8) {
        return;
    }
    if (pkt[9] != IPPROTO_UDP) {
        return;
    }
    uint16_t dport = (uint16_t)((pkt[ihl + 2] << 8) | pkt[ihl + 3]);
    if (dport != QUERY_PORT) {
        return;
    }

    uint32_t src;
    memcpy(&src, pkt + 12, sizeof(src));
    rc_add(&rc, src);
}

static void handle_alert(void)
{
    char msg[128];
    struct sockaddr_in from;
    socklen_t fromlen = sizeof(from);
    ssize_t n = recvfrom(alert_fd, msg, sizeof(msg), MSG_DONTWAIT, (struct sockaddr *)&from, &fromlen);
    if (n <= 0) {
        return;
    }

    uint32_t ip;
    char sender[ALERT_NODE_MAX + 1];
    char buf[INET_ADDRSTRLEN];
    if (alert_parse(msg, (size_t)n, &ip, sender, sizeof(sender)) != 0) {
        log_line("BỎ QUA cảnh báo không hợp lệ từ %s", ip_str(from.sin_addr.s_addr, buf));
        return;
    }
    if (!bl_allowed_to_block(&bl, ip)) {
        log_line("BỎ QUA %s (whitelist), cảnh báo từ %s", ip_str(ip, buf), sender);
        return;
    }
    if (bl_add(&bl, ip) == 0) {
        log_line("ĐÃ CHẶN %s từ trước (cảnh báo từ %s)", ip_str(ip, buf), sender);
        return;
    }
    if (fw_block(ip) != 0) {
        log_line("LỖI: không chặn được %s bằng iptables", ip_str(ip, buf));
        return;
    }
    log_line("NHẬN cảnh báo từ %s → CHẶN %s", sender, ip_str(ip, buf));
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Cách dùng: %s -n <tên> [-d -i <iface>] [-t 200] [-l -b <ip>] [-P <peer_ip>]... [-W <ip>]... [-Q]\n"
            "  -d        bật phát hiện trên interface -i\n"
            "  -t        ngưỡng gói/giây (mặc định 200)\n"
            "  -l        nghe cảnh báo trên <ip>:%d\n"
            "  -P        peer nhận cảnh báo (có -P = chế độ hợp tác)\n"
            "  -W        IP không bao giờ chặn\n"
            "  -Q        đánh dấu gói cảnh báo là ưu tiên (QoS)\n",
            prog, ALERT_PORT);
}

int main(int argc, char **argv)
{
    const char *iface = NULL;
    const char *bind_ip = NULL;
    int detect = 0;
    int listen_alerts = 0;
    int priority = 0;
    uint32_t threshold = 200;

    bl_init(&bl);
    rc_init(&rc);

    int opt;
    while ((opt = getopt(argc, argv, "n:i:dt:lb:P:W:Q")) != -1) {
        if (opt == 'n') {
            node_name = optarg;
        } else if (opt == 'i') {
            iface = optarg;
        } else if (opt == 'd') {
            detect = 1;
        } else if (opt == 't') {
            threshold = (uint32_t)atoi(optarg);
        } else if (opt == 'l') {
            listen_alerts = 1;
        } else if (opt == 'b') {
            bind_ip = optarg;
        } else if (opt == 'P') {
            if (peer_count >= MAX_PEERS || parse_ip(optarg, &peers[peer_count]) != 0) {
                fprintf(stderr, "Peer không hợp lệ hoặc quá nhiều: %s\n", optarg);
                return 1;
            }
            peer_count++;
        } else if (opt == 'Q') {
            priority = 1;
        } else if (opt == 'W') {
            uint32_t ip;
            if (parse_ip(optarg, &ip) != 0) {
                fprintf(stderr, "IP whitelist không hợp lệ: %s\n", optarg);
                return 1;
            }
            bl_whitelist(&bl, ip);
        } else {
            usage(argv[0]);
            return 1;
        }
    }

    if (node_name == NULL || strlen(node_name) > ALERT_NODE_MAX
        || (!detect && !listen_alerts)
        || (detect && iface == NULL)
        || (listen_alerts && bind_ip == NULL)) {
        usage(argv[0]);
        return 1;
    }

    if (geteuid() != 0) {
        fprintf(stderr, "guard cần quyền root (raw socket + iptables)\n");
        return 1;
    }

    // Socket cảnh báo: dùng để nghe (nếu -l) và để gửi (nếu có peer).
    alert_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (alert_fd < 0) {
        perror("socket");
        return 1;
    }
    if (priority) {
        int tos = TOS_PRIORITY;
        if (setsockopt(alert_fd, IPPROTO_IP, IP_TOS, &tos, sizeof(tos)) < 0) {
            perror("setsockopt IP_TOS");
            return 1;
        }
    }
    if (listen_alerts) {
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(ALERT_PORT);
        if (parse_ip(bind_ip, &addr.sin_addr.s_addr) != 0
            || bind(alert_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
            perror("bind cảnh báo");
            return 1;
        }
    }

    // Raw socket bắt gói IP trên interface (SOCK_DGRAM: đã bỏ header Ethernet).
    int raw_fd = -1;
    if (detect) {
        raw_fd = socket(AF_PACKET, SOCK_DGRAM, htons(ETH_P_IP));
        if (raw_fd < 0) {
            perror("socket AF_PACKET");
            return 1;
        }
        struct sockaddr_ll sll;
        memset(&sll, 0, sizeof(sll));
        sll.sll_family = AF_PACKET;
        sll.sll_protocol = htons(ETH_P_IP);
        sll.sll_ifindex = (int)if_nametoindex(iface);
        if (sll.sll_ifindex == 0 || bind(raw_fd, (struct sockaddr *)&sll, sizeof(sll)) < 0) {
            fprintf(stderr, "Không bind được interface %s\n", iface);
            return 1;
        }
    }

    if (fw_init() != 0) {
        fprintf(stderr, "Không khởi tạo được chain iptables GUARD\n");
        return 1;
    }

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    log_line("khởi động: phát hiện=%s, nghe cảnh báo=%s, hợp tác=%s, ưu tiên QoS=%s, ngưỡng=%u gói/s",
             detect ? iface : "TẮT",
             listen_alerts ? "BẬT" : "TẮT", peer_count > 0 ? "BẬT" : "TẮT",
             priority ? "BẬT" : "TẮT", threshold);

    uint64_t next_tick = now_us() + 1000000;
    unsigned char pkt[2048];

    while (!stop) {
        struct pollfd pfd[2];
        int nfds = 0;
        int raw_idx = -1;
        int alert_idx = -1;
        if (raw_fd >= 0) {
            raw_idx = nfds;
            pfd[nfds].fd = raw_fd;
            pfd[nfds].events = POLLIN;
            nfds++;
        }
        if (listen_alerts) {
            alert_idx = nfds;
            pfd[nfds].fd = alert_fd;
            pfd[nfds].events = POLLIN;
            nfds++;
        }

        int r = poll(pfd, (nfds_t)nfds, 50);
        if (r < 0 && errno != EINTR) {
            perror("poll");
            break;
        }

        if (r > 0 && raw_idx >= 0 && (pfd[raw_idx].revents & POLLIN)) {
            for (int i = 0; i < 2000; i++) {
                struct sockaddr_ll from;
                socklen_t fromlen = sizeof(from);
                ssize_t n = recvfrom(raw_fd, pkt, sizeof(pkt), MSG_DONTWAIT,
                                     (struct sockaddr *)&from, &fromlen);
                if (n < 0) {
                    break;
                }
                // Chỉ đếm gói đi vào, bỏ qua gói do chính node gửi ra.
                if (from.sll_pkttype == PACKET_OUTGOING) {
                    continue;
                }
                handle_packet(pkt, n);
            }
        }

        if (r > 0 && alert_idx >= 0 && (pfd[alert_idx].revents & POLLIN)) {
            handle_alert();
        }

        uint64_t now = now_us();
        if (now >= next_tick) {
            if (detect) {
                check_rates(threshold);
            }
            next_tick = now + 1000000;
        }
    }

    fw_cleanup();
    log_line("dừng, đã xóa các rule iptables");
    return 0;
}
