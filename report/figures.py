"""Vẽ các hình minh họa cho báo cáo vào report/figures/. Chạy: python3 report/figures.py

Ảnh 200 dpi, rộng 15cm (1181 px). Chữ dùng Liberation Serif (cùng kích thước với Times New Roman).
"""
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/figures"
DATA = ROOT / "results/eve-v2-report"
FONT_DIR = Path("/usr/share/fonts/truetype/liberation2")  # bản 2 có đủ chữ Việt
DPI = 200
WIDTH = 1181                      # 15cm ở 200 dpi
PT = DPI / 72                     # số pixel cho 1 point

BLACK = (0, 0, 0)
GREY = (120, 120, 120)
LIGHT = (235, 235, 235)
RED = (200, 40, 40)
GREEN = (40, 140, 60)
BLUE = (40, 90, 180)
ORANGE = (230, 140, 30)


def font(size_pt: float, bold: bool = False, mono: bool = False):
    if mono:
        name = "LiberationMono-Bold.ttf" if bold else "LiberationMono-Regular.ttf"
    else:
        name = "LiberationSerif-Bold.ttf" if bold else "LiberationSerif-Regular.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), int(size_pt * PT))


F_TEXT = font(10)
F_BOLD = font(10, bold=True)
F_SMALL = font(8.5)


class Canvas:
    def __init__(self, height_cm: float):
        self.img = Image.new("RGB", (WIDTH, int(height_cm / 2.54 * DPI)), "white")
        self.draw = ImageDraw.Draw(self.img)

    def text(self, xy, text, f=F_TEXT, fill=BLACK, anchor="mm"):
        self.draw.multiline_text(xy, text, font=f, fill=fill, anchor=anchor, align="center", spacing=4)

    def box(self, x, y, w, h, text="", fill="white", outline=BLACK, f=F_TEXT, width=3, text_fill=BLACK):
        self.draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=fill, outline=outline, width=width)
        if text:
            self.text((x + w / 2, y + h / 2), text, f, text_fill)

    def arrow(self, start, end, fill=BLACK, width=4, head=16):
        self.draw.line([start, end], fill=fill, width=width)
        (x1, y1), (x2, y2) = start, end
        length = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1)
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        left = (x2 - head * ux + head * 0.5 * uy, y2 - head * uy - head * 0.5 * ux)
        right = (x2 - head * ux - head * 0.5 * uy, y2 - head * uy + head * 0.5 * ux)
        self.draw.polygon([end, left, right], fill=fill)

    def cross(self, x, y, size=22, fill=RED):
        self.draw.line([(x - size, y - size), (x + size, y + size)], fill=fill, width=7)
        self.draw.line([(x - size, y + size), (x + size, y - size)], fill=fill, width=7)

    def save(self, name: str):
        self.img.save(OUT / name, dpi=(DPI, DPI))


def tcpip():
    c = Canvas(6.6)
    layers = [
        ("Tầng ứng dụng", "server, client, attacker, guard (mã C của đề tài)"),
        ("Tầng giao vận", "UDP: truy vấn ở cổng 9000, cảnh báo ở cổng 9999"),
        ("Tầng mạng", "IP, định tuyến; Netfilter/iptables lọc gói ở chain FORWARD"),
        ("Tầng liên kết", "Ethernet; raw socket AF_PACKET của guard đọc gói ở đây"),
    ]
    for i, (name, note) in enumerate(layers):
        y = 25 + i * 125
        c.box(40, y, 330, 95, name, fill=LIGHT, f=F_BOLD)
        c.text((790, y + 47), note, F_TEXT)
        if i < 3:
            c.arrow((205, y + 95), (205, y + 125), GREY, 3, 12)
    c.save("tcpip.png")


def packets(c, x, y, colors, size=28, gap=8):
    for i, color in enumerate(colors):
        c.draw.rectangle([x + i * (size + gap), y, x + i * (size + gap) + size, y + size], fill=color)


def bottleneck_queue():
    c = Canvas(7)
    c.text((175, 70), "Vào: khoảng 40 Mbit/s\n(tấn công + truy vấn hợp lệ)", F_TEXT)
    c.arrow((60, 230), (300, 230), BLACK, 6)
    c.box(320, 160, 520, 140, fill=LIGHT)
    c.text((580, 140), "Hàng đợi của router (tối đa 500KB, khoảng 400 ms)", F_SMALL, anchor="mm")
    colors = [RED, RED, GREEN, RED, RED, RED, RED, GREEN, RED, RED, RED, RED]
    packets(c, 340, 216, colors)
    c.arrow((840, 230), (1100, 230), BLACK, 4)
    c.text((975, 180), "Ra: 10 Mbit/s", F_TEXT)
    c.arrow((580, 300), (580, 400), RED, 4)
    c.text((580, 450), "Hàng đợi đầy: gói tới sau bị loại bỏ (mất gói)", F_TEXT, RED)
    packets(c, 60, 470, [RED])
    c.text((110, 485), "gói tấn công", F_SMALL, anchor="lm")
    packets(c, 260, 470, [GREEN])
    c.text((310, 485), "truy vấn của client: phải xếp hàng sau gói tấn công", F_SMALL, anchor="lm")
    c.save("bottleneck_queue.png")


def chain(c, y, block_at, link_colors, title):
    names = ["Attacker", "R1", "R2", "R3", "Server"]
    xs = [90, 340, 590, 840, 1090]
    c.text((WIDTH / 2, y - 80), title, F_BOLD)
    for i, (x, name) in enumerate(zip(xs, names)):
        c.box(x - 75, y - 35, 150, 70, name, fill=LIGHT)
        if i < 4:
            c.draw.line([(x + 75, y), (xs[i + 1] - 75, y)], fill=link_colors[i], width=12 if link_colors[i] == RED else 4)
    c.cross(xs[block_at] - 115, y)


def victim_vs_edge():
    c = Canvas(8)
    chain(c, 150, 3, [RED, RED, RED, GREY],
          "(a) Chỉ R3 chặn: server an toàn, nhưng lưu lượng tấn công vẫn chiếm link R1 → R2 → R3")
    chain(c, 450, 1, [RED, GREY, GREY, GREY],
          "(b) R3 báo cho R1 chặn: lưu lượng tấn công dừng ngay ở router đầu vào")
    c.text((WIDTH / 2, 590), "Đường đỏ đậm: link bị lưu lượng tấn công chiếm. Dấu ×: nơi gói của attacker bị loại bỏ.", F_SMALL, GREY)
    c.save("victim_vs_edge.png")


def two_lane_queue():
    c = Canvas(7.5)
    c.box(30, 200, 170, 110, "Gói đi ra\ncổng eth2", f=F_TEXT)
    c.box(260, 190, 230, 130, "Bộ lọc u32\nTOS = 0xB8 ?", fill=LIGHT)
    c.arrow((200, 255), (260, 255))
    c.box(570, 70, 280, 110, "Làn 1 (ưu tiên)\nbfifo 500KB", fill=(220, 240, 220))
    c.box(570, 330, 280, 110, "Làn 2 (thường)\nbfifo 500KB", fill=(245, 225, 225))
    c.arrow((490, 230), (570, 125), GREEN)
    c.text((470, 150), "có", F_SMALL, GREEN)
    c.arrow((490, 280), (570, 385), RED)
    c.text((470, 360), "không", F_SMALL, RED)
    c.box(930, 190, 220, 130, "prio: lấy làn 1\ntrước, rồi làn 2", fill=LIGHT)
    c.arrow((850, 125), (930, 230), GREEN)
    c.arrow((850, 385), (930, 280), RED)
    c.text((1040, 400), "tbf: giới hạn\n10 Mbit/s", F_TEXT)
    c.arrow((1040, 320), (1040, 360), GREY, 3, 12)
    c.save("two_lane_queue.png")


def sequence():
    c = Canvas(11)
    names = ["Attacker", "R1", "R2", "R3", "Server"]
    xs = [100, 330, 560, 790, 1060]
    top, bottom = 40, 730
    for x, name in zip(xs, names):
        c.box(x - 80, top, 160, 60, name, fill=LIGHT, f=F_BOLD)
        c.draw.line([(x, top + 60), (x, bottom)], fill=GREY, width=2)

    def message(y, a, b, label, color=BLACK, dashed=False):
        c.arrow((xs[a], y), (xs[b], y), color, 4)
        c.text(((xs[a] + xs[b]) / 2, y - 22), label, F_SMALL, color)

    message(150, 0, 3, "UDP flood 5.000 gói/s đi qua R1, R2", RED)
    message(220, 3, 4, "chuyển tiếp tới server", RED)
    c.box(700, 260, 180, 110, "đếm theo IP:\n> 200 gói/s\n→ iptables DROP", fill=(255, 240, 220), f=F_SMALL)
    message(430, 3, 2, "BLOCK 10.0.1.10 R3", BLUE)
    message(500, 3, 1, "BLOCK 10.0.1.10 R3", BLUE)
    c.box(250, 540, 160, 80, "iptables DROP", fill=(255, 240, 220), f=F_SMALL)
    c.box(480, 540, 160, 80, "iptables DROP", fill=(255, 240, 220), f=F_SMALL)
    c.arrow((xs[0], 690), (xs[1] - 10, 690), RED, 4)
    c.cross(xs[1] + 30, 690, size=18)
    c.text((xs[1] + 260, 690), "gói tấn công bị loại bỏ ngay tại R1", F_SMALL, RED)
    c.text((WIDTH / 2, 790), "Mũi tên xanh: cảnh báo (lượt on: mạng điều khiển; lượt inband: chung đường, ưu tiên QoS)", F_SMALL, GREY)
    c.save("sequence.png")


def topology():
    c = Canvas(11)
    c.box(20, 90, 230, 90, "Attacker\n10.0.1.10", fill=LIGHT)
    c.box(20, 330, 230, 90, "Client\n10.0.1.20", fill=LIGHT)
    c.box(330, 205, 170, 100, "R1", fill=(220, 230, 250), f=F_BOLD)
    c.box(610, 205, 170, 100, "R2", fill=(220, 230, 250), f=F_BOLD)
    c.box(890, 205, 170, 100, "R3", fill=(220, 230, 250), f=F_BOLD)
    c.box(890, 20, 270, 90, "Server\n10.0.3.10", fill=LIGHT)
    c.draw.line([(250, 135), (330, 240)], fill=BLACK, width=4)
    c.draw.line([(250, 375), (330, 270)], fill=BLACK, width=4)
    c.text((140, 255), "LAN1 10.0.1.0/24", F_SMALL)
    c.draw.line([(500, 255), (610, 255)], fill=RED, width=10)
    c.draw.line([(780, 255), (890, 255)], fill=RED, width=10)
    c.text((555, 200), "10.0.12.0/24\n10 Mbit/s", F_SMALL, RED)
    c.text((835, 200), "10.0.23.0/24\n10 Mbit/s", F_SMALL, RED)
    c.draw.line([(975, 205), (1025, 110)], fill=BLACK, width=4)
    c.text((1110, 160), "10.0.3.0/24", F_SMALL)
    c.draw.line([(415, 305), (415, 480)], fill=BLUE, width=4)
    c.draw.line([(695, 305), (695, 480)], fill=BLUE, width=4)
    c.draw.line([(975, 305), (975, 480)], fill=BLUE, width=4)
    c.draw.line([(415, 480), (975, 480)], fill=BLUE, width=6)
    c.text((695, 515), "Mạng điều khiển CTRL 10.0.99.0/24 (R1 .1, R2 .2, R3 .3)", F_SMALL, BLUE)
    c.draw.line([(40, 620), (1140, 620)], fill=GREY, width=4)
    c.text((590, 655), "Mạng quản lý MGMT 172.30.0.0/24 (cổng eth0 mọi node, máy EVE là .1, node 1..6 là .11..16)", F_SMALL, GREY)
    c.text((590, 760), "Cổng eth1 trở đi là mạng dữ liệu. Đường đỏ: nút cổ chai, mỗi chiều có hàng đợi 2 làn.", F_SMALL, GREY)
    c.save("topology.png")


def guard_flow():
    c = Canvas(17)
    x = 330
    steps = [
        ("Đọc tham số (-d, -l, -P, -Q, -W...)\nmở socket cảnh báo, raw socket, fw_init()", 0),
        ("poll() chờ tối đa 50 ms\ntrên raw socket và socket cảnh báo", 1),
        ("Có gói trên raw socket?\n→ handle_packet(): UDP tới cổng 9000\n→ rc_add(IP nguồn)", 2),
        ("Có cảnh báo?\n→ handle_alert(): alert_parse, kiểm tra whitelist,\nbl_add, fw_block", 3),
        ("Đã qua 1 giây?\n→ check_rates(): IP > ngưỡng → fw_block,\nsend_alerts (nếu có peer) → rc_reset", 4),
        ("Nhận SIGINT/SIGTERM?\n→ fw_cleanup(): xóa chain GUARD, thoát", 5),
    ]
    heights = [130, 120, 160, 160, 160, 130]
    y = 30
    centers = []
    for (label, index), h in zip(steps, heights):
        fill = (220, 230, 250) if index in (0, 5) else LIGHT
        c.box(x - 280, y, 820, h, label, fill=fill, f=F_TEXT)
        centers.append((y, h))
        y += h + 70
    for i in range(len(centers) - 1):
        top, h = centers[i]
        c.arrow((x + 130, top + h), (x + 130, centers[i + 1][0]), BLACK, 4)
    loop_top = centers[1][0] + 60
    loop_bottom = centers[4][0] + 80
    c.draw.line([(x + 540, loop_bottom), (x + 600, loop_bottom), (x + 600, loop_top)], fill=BLUE, width=4)
    c.arrow((x + 600, loop_top), (x + 540, loop_top), BLUE, 4)
    c.text((x + 690, (loop_top + loop_bottom) / 2), "lặp lại\nđến khi\ndừng", F_SMALL, BLUE)
    c.save("guard_flow.png")


def tmux_inband():
    """Vẽ lại nội dung thật của 4 ô tmux (lượt inband), xếp dọc.
    Chữ trong khung là nguyên văn file chụp; nhãn xám phía trên khung là chú thích của báo cáo."""
    panes = [
        ("inband_pane0.txt", 9, "Ô trên trái: client (RTT, mất gói mỗi giây), 9 dòng cuối"),
        ("inband_pane1.txt", 6, "Ô dưới trái: lưu lượng link R1 → R2, 6 dòng cuối"),
        ("inband_pane2.txt", 0, "Ô trên phải: sự kiện phát hiện, cảnh báo, chặn"),
        ("inband_pane3.txt", 0, "Ô dưới phải: tiến trình demo.sh"),
    ]
    mono = font(7, mono=True)
    label_font = font(8)
    line_h = int(7 * PT * 1.25)
    label_h = int(8 * PT * 1.4)
    blocks = []
    for name, tail, label in panes:
        lines = [l.rstrip() for l in (DATA / "tmux" / name).read_text(encoding="utf-8").splitlines()]
        lines = [l for l in lines if l.strip()]
        if tail and len(lines) > tail:
            lines = ["..."] + lines[-tail:]
        blocks.append((label, lines))
    height = sum(label_h + len(b) * line_h + 40 for _, b in blocks) + 20
    img = Image.new("RGB", (WIDTH, height), "white")
    draw = ImageDraw.Draw(img)
    y = 10
    for label, body in blocks:
        draw.text((12, y), label, font=label_font, fill=GREY)
        y += label_h
        top = y
        draw.rectangle([8, top, WIDTH - 8, top + len(body) * line_h + 20], fill=(250, 250, 250), outline=GREY, width=2)
        y += 10
        for text in body:
            draw.text((20, y), text, font=mono, fill=BLACK)
            y += line_h
        y += 30
    img.save(OUT / "tmux_inband.png", dpi=(DPI, DPI))


def eve_placeholder():
    """Khung chờ: người dùng thay bằng ảnh chụp giao diện web EVE-NG mở lab collab-defense."""
    c = Canvas(7)
    c.draw.rectangle([10, 10, WIDTH - 10, c.img.height - 10], outline=GREY, width=4)
    c.text((WIDTH / 2, c.img.height / 2),
           "[Ảnh chụp giao diện EVE-NG: lab collab-defense với 6 node]\n"
           "Mở http://<IP máy EVE>, vào lab collab-defense, chụp màn hình\n"
           "rồi dán đè lên khung này (giữ nguyên nhãn hình bên dưới).", F_TEXT, GREY)
    c.save("eve_placeholder.png")


def charts():
    subprocess.run([str(ROOT / "scripts/plot.sh"), str(DATA)], check=True, stdout=subprocess.DEVNULL)
    for name in ["rtt.png", "link.png"]:
        shutil.copyfile(DATA / name, OUT / name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tcpip()
    bottleneck_queue()
    victim_vs_edge()
    two_lane_queue()
    sequence()
    topology()
    guard_flow()
    tmux_inband()
    eve_placeholder()
    charts()
    for path in sorted(OUT.glob("*.png")):
        print(path.name)


if __name__ == "__main__":
    main()
