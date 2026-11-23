#include "firewall.h"

#include <arpa/inet.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static int dry_run = 0;
static char last_cmd[256];

void fw_set_dry_run(int on)
{
    dry_run = on;
}

const char *fw_last_cmd(void)
{
    return last_cmd;
}

// Chạy iptables với danh sách tham số (argv kết thúc bằng NULL).
// Dùng fork + execvp nên không có shell, không thể bị chèn lệnh.
// Trả về mã thoát của iptables (0 = thành công).
static int run(char *const argv[])
{
    last_cmd[0] = '\0';
    for (int i = 0; argv[i] != NULL; i++) {
        if (i > 0) {
            strncat(last_cmd, " ", sizeof(last_cmd) - strlen(last_cmd) - 1);
        }
        strncat(last_cmd, argv[i], sizeof(last_cmd) - strlen(last_cmd) - 1);
    }

    if (dry_run) {
        return 0;
    }

    pid_t pid = fork();
    if (pid < 0) {
        return -1;
    }
    if (pid == 0) {
        // Ẩn thông báo lỗi của iptables (ví dụ chain đã tồn tại).
        FILE *devnull = freopen("/dev/null", "w", stderr);
        (void)devnull;
        execvp(argv[0], argv);
        _exit(127);
    }

    int status = 0;
    if (waitpid(pid, &status, 0) < 0) {
        return -1;
    }
    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }
    return -1;
}

int fw_init(void)
{
    char *create[] = { "iptables", "-N", "GUARD", NULL };
    run(create);   // chain đã có từ lần trước thì bỏ qua lỗi

    char *flush[] = { "iptables", "-F", "GUARD", NULL };
    if (run(flush) != 0) {
        return -1;
    }

    char *check[] = { "iptables", "-C", "FORWARD", "-j", "GUARD", NULL };
    if (run(check) != 0) {
        char *insert[] = { "iptables", "-I", "FORWARD", "1", "-j", "GUARD", NULL };
        if (run(insert) != 0) {
            return -1;
        }
    }
    return 0;
}

int fw_block(uint32_t ip)
{
    char ipstr[INET_ADDRSTRLEN];
    struct in_addr a = { .s_addr = ip };
    inet_ntop(AF_INET, &a, ipstr, sizeof(ipstr));

    char *argv[] = { "iptables", "-A", "GUARD", "-s", ipstr, "-j", "DROP", NULL };
    if (run(argv) != 0) {
        return -1;
    }
    return 0;
}

int fw_cleanup(void)
{
    // Gỡ hết các lần gắn GUARD vào FORWARD (nếu bị gắn nhiều lần).
    char *del[] = { "iptables", "-D", "FORWARD", "-j", "GUARD", NULL };
    for (int i = 0; i < 10; i++) {
        if (run(del) != 0 || dry_run) {
            break;
        }
    }

    char *flush[] = { "iptables", "-F", "GUARD", NULL };
    run(flush);

    char *remove[] = { "iptables", "-X", "GUARD", NULL };
    if (run(remove) != 0) {
        return -1;
    }
    return 0;
}
