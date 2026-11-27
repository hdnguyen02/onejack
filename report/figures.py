"""Vẽ các hình minh họa cho báo cáo vào report/figures/. Chạy: python3 report/figures.py

Ảnh 200 dpi, rộng 15cm (1181 px). Chữ dùng Liberation Serif (cùng kích thước với Times New Roman).
Biểu đồ số liệu lấy từ results/eve (vẽ bằng scripts/plot.sh).
"""
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/figures"
DATA = ROOT / "results/eve"
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
ROUTER = (220, 230, 250)


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

    def line(self, points, fill=BLACK, width=4):
        self.draw.line(points, fill=fill, width=width)

    def arrow(self, start, end, fill=BLACK, width=4, head=16):
        self.draw.line([start, end], fill=fill, width=width)
        (x1, y1), (x2, y2) = start, end
        length = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1)
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        left = (x2 - head * ux + head * 0.5 * uy, y2 - head * uy - head * 0.5 * ux)
        right = (x2 - head * ux - head * 0.5 * uy, y2 - head * uy + head * 0.5 * ux)
        self.draw.polygon([end, left, right], fill=fill)

    def save(self, name: str):
        self.img.save(OUT / name, dpi=(DPI, DPI))


def packets(c, x, y, colors, size=28, gap=8):
    for i, color in enumerate(colors):
        c.draw.rectangle([x + i * (size + gap), y, x + i * (size + gap) + size, y + size], fill=color)


def tcpip():
    c = Canvas(6.6)
    layers = [
        ("Tầng ứng dụng", "server, client, loadgen (mã C của đề tài)"),
        ("Tầng giao vận", "UDP: truy vấn và gói tải đều gửi tới cổng 9000 của server"),
        ("Tầng mạng", "IP, định tuyến: router chọn đường dài, đường ngắn hoặc chia tải"),
        ("Tầng liên kết", "Ethernet; tc netem/tbf tạo độ trễ và giới hạn băng thông link"),
    ]
    for i, (name, note) in enumerate(layers):
        y = 25 + i * 125
        c.box(40, y, 330, 95, name, fill=LIGHT, f=F_BOLD)
        c.text((790, y + 47), note, F_TEXT)
        if i < 3:
            c.arrow((205, y + 95), (205, y + 125), GREY, 3, 12)
    c.save("tcpip.png")


def delay_parts():
    """Các thành phần của độ trễ trên một chặng: xử lý, xếp hàng, phát, truyền."""
    c = Canvas(6.5)
    c.box(40, 150, 200, 110, "Router A", fill=ROUTER, f=F_BOLD)
    c.box(940, 150, 200, 110, "Router B", fill=ROUTER, f=F_BOLD)
    c.box(270, 160, 250, 90, fill=LIGHT)
    packets(c, 290, 190, [ORANGE, ORANGE, ORANGE, ORANGE, GREEN, ORANGE])
    c.arrow((520, 205), (940, 205), BLACK, 5)
    parts = [
        (140, "(1) xử lý\nđọc tiêu đề,\nchọn đường"),
        (395, "(2) xếp hàng\nchờ tới lượt\nđược gửi đi"),
        (590, "(3) phát\nđẩy gói\nlên dây"),
        (780, "(4) truyền\ntín hiệu đi\nhết chiều dài dây"),
    ]
    for x, label in parts:
        c.text((x, 360), label, F_SMALL)
        c.line([(x, 300), (x, 270)], GREY, 2)
    c.text((WIDTH / 2, 60), "Độ trễ một chặng = xử lý + xếp hàng + phát + truyền", F_BOLD)
    c.text((WIDTH / 2, 470), "Khi đường không nghẽn, (2) gần bằng 0. Khi lưu lượng vượt băng thông, (2) tăng mạnh.",
           F_SMALL, GREY)
    c.save("delay_parts.png")


def queue_build_up():
    c = Canvas(7)
    c.text((175, 70), "Vào: {} Mbit/s\n(tải nặng + truy vấn của client)".format(12), F_TEXT)
    c.arrow((60, 230), (300, 230), BLACK, 6)
    c.box(320, 160, 520, 140, fill=LIGHT)
    c.text((580, 140), "Hàng đợi của router (tối đa 500KB, khoảng 400 ms)", F_SMALL)
    colors = [ORANGE, ORANGE, GREEN, ORANGE, ORANGE, ORANGE, ORANGE, GREEN, ORANGE, ORANGE, ORANGE, ORANGE]
    packets(c, 340, 216, colors)
    c.arrow((840, 230), (1100, 230), BLACK, 4)
    c.text((975, 180), "Ra: 10 Mbit/s", F_TEXT)
    c.arrow((580, 300), (580, 400), RED, 4)
    c.text((580, 450), "Hàng đợi đầy: gói tải tới sau bị loại bỏ", F_TEXT, RED)
    packets(c, 60, 470, [ORANGE])
    c.text((110, 485), "gói tải 1000 byte", F_SMALL, anchor="lm")
    packets(c, 330, 470, [GREEN])
    c.text((380, 485), "truy vấn của client: nhỏ, vẫn vào được hàng nhưng phải chờ phía sau", F_SMALL, anchor="lm")
    c.save("queue.png")


def router_box(c, x, y, name):
    c.box(x - 70, y - 45, 140, 90, name, fill=ROUTER, f=F_BOLD)


def topology():
    c = Canvas(11)
    c.box(20, 90, 230, 90, "Loadgen\n10.0.1.10", fill=LIGHT)
    c.box(20, 330, 230, 90, "Client\n10.0.1.20", fill=LIGHT)
    r1, r2, r3 = (410, 255), (650, 110), (890, 255)
    router_box(c, *r1, "R1")
    router_box(c, *r2, "R2")
    router_box(c, *r3, "R3")
    c.box(1000, 380, 170, 90, "Server\n10.0.3.10", fill=LIGHT)
    c.line([(250, 135), (340, 235)])
    c.line([(250, 375), (340, 275)])
    c.text((140, 255), "LAN1\n10.0.1.0/24", F_SMALL)
    # Đường dài: R1 - R2 - R3
    c.line([(470, 215), (580, 135)], RED, 8)
    c.line([(720, 135), (830, 215)], RED, 8)
    c.text((470, 140), "eth2 .1\n10.0.12.0/24", F_SMALL, RED)
    c.text((830, 140), "10.0.23.0/24\neth1 .3", F_SMALL, RED)
    c.text((650, 30), "đường dài: 2 link", F_BOLD, RED)
    # Đường ngắn: R1 - R3
    c.line([(480, 290), (820, 290)], BLUE, 8)
    c.text((650, 330), "đường ngắn: 1 link, 10.0.13.0/24\n(R1 eth3 .1, R3 eth3 .3)", F_SMALL, BLUE)
    c.line([(930, 300), (1040, 380)])
    c.text((1080, 300), "10.0.3.0/24", F_SMALL)
    c.text((WIDTH / 2, 520), "Mỗi link giữa hai router: độ trễ truyền 10 ms mỗi chiều, băng thông 10 Mbit/s.", F_SMALL)
    c.line([(40, 610), (1140, 610)], GREY, 4)
    c.text((590, 645), "Mạng quản lý MGMT 172.30.0.0/24 (cổng eth0 mọi node, máy EVE là .1, node 1..6 là .11..16)",
           F_SMALL, GREY)
    c.text((590, 740), "Cổng eth1 trở đi là mạng dữ liệu; mạng quản lý chỉ dùng để điều khiển, không tham gia đo.",
           F_SMALL, GREY)
    c.save("topology.png")


def mini_net(c, y0, title, long_mbit, short_mbit, long_full, short_full):
    """Một sơ đồ nhỏ R1 -> R3 với hai đường, ghi lưu lượng trên mỗi đường."""
    c.text((WIDTH / 2, y0), title, F_BOLD)
    r1, r2, r3 = (230, y0 + 120), (590, y0 + 60), (950, y0 + 120)
    c.box(r1[0] - 60, r1[1] - 35, 120, 70, "R1", fill=ROUTER, f=F_BOLD)
    c.box(r2[0] - 60, r2[1] - 35, 120, 70, "R2", fill=ROUTER, f=F_BOLD)
    c.box(r3[0] - 60, r3[1] - 35, 120, 70, "R3", fill=ROUTER, f=F_BOLD)
    c.arrow((40, r1[1]), (r1[0] - 60, r1[1]), BLACK, 4)
    c.text((95, r1[1] - 30), "12 Mbit/s", F_SMALL)
    c.arrow((r3[0] + 60, r3[1]), (1150, r3[1]), BLACK, 4)
    long_color = RED if long_full else (GREEN if long_mbit else GREY)
    short_color = RED if short_full else (GREEN if short_mbit else GREY)
    long_width = 10 if long_mbit else 3
    short_width = 10 if short_mbit else 3
    c.line([(r1[0] + 60, r1[1] - 20), (r2[0] - 60, r2[1])], long_color, long_width)
    c.line([(r2[0] + 60, r2[1]), (r3[0] - 60, r3[1] - 20)], long_color, long_width)
    c.line([(r1[0] + 60, r1[1] + 20), (r3[0] - 60, r3[1] + 20)], short_color, short_width)
    c.text((360, y0 + 30), long_mbit or "bỏ trống", F_SMALL, long_color)
    c.text((590, y0 + 175), short_mbit or "bỏ trống", F_SMALL, short_color)


def three_runs():
    c = Canvas(15.5)
    mini_net(c, 30, "(a) base: mọi lưu lượng đi đường dài qua R2", "12 Mbit/s > 10: tắc nghẽn", "", True, False)
    mini_net(c, 400, "(b) short: mọi lưu lượng đi đường ngắn R1 → R3", "", "12 Mbit/s > 10: tắc nghẽn", False, True)
    mini_net(c, 770, "(c) balance: chia các luồng ra cả hai đường", "khoảng 6 Mbit/s", "khoảng 6 Mbit/s", False, False)
    c.text((WIDTH / 2, 1180), "Đỏ: đường bị quá tải, gói phải xếp hàng. Xanh lá: đường còn dư băng thông. Xám: đường không dùng.",
           F_SMALL, GREY)
    c.save("three_runs.png")


def ecmp_hash():
    c = Canvas(8.5)
    c.text((WIDTH / 2, 40), "R1 chọn đường cho từng luồng theo (IP nguồn, IP đích, cổng nguồn, cổng đích, giao thức)", F_SMALL)
    flows = ["luồng cổng 20000", "luồng cổng 20001", "luồng cổng 20002", "...", "luồng cổng 20031"]
    for i, name in enumerate(flows):
        y = 110 + i * 95
        c.box(30, y, 260, 70, name, fill=LIGHT, f=F_SMALL)
        c.arrow((290, y + 35), (430, 330), GREY, 3, 12)
    c.box(430, 270, 260, 120, "hàm băm\n→ chọn 1 trong 2 đường", fill=ROUTER, f=F_SMALL)
    c.arrow((690, 300), (870, 190), RED, 4)
    c.arrow((690, 360), (870, 470), BLUE, 4)
    c.box(870, 140, 290, 100, "đường dài (eth2)", fill=(250, 225, 225), f=F_SMALL)
    c.box(870, 420, 290, 100, "đường ngắn (eth3)", fill=(225, 235, 250), f=F_SMALL)
    c.text((WIDTH / 2, 610), "Mọi gói của cùng một luồng luôn ra cùng một đường, nên không bị đảo thứ tự.\n"
           "Có nhiều luồng thì hai đường nhận số luồng gần bằng nhau.", F_SMALL, GREY)
    c.save("ecmp_hash.png")


def experiment_flow():
    c = Canvas(14)
    steps = [
        "reset.sh: dừng mọi chương trình đo còn sót lại",
        "Cấu hình R1, R2, R3 theo lượt: sh rX.sh long | short | balance",
        "Khởi động server, bộ đo lưu lượng linkmon trên R1, client 20 truy vấn/giây",
        "Chờ 15 giây: đo độ trễ lúc mạng chưa có tải",
        "Khởi động loadgen: 12 Mbit/s, 32 luồng, chạy tới hết lượt",
        "Hết 60 giây: dừng chương trình, lưu CSV và log vào results/",
        "plot.sh: tính trung bình, vẽ biểu đồ, in bảng so sánh",
    ]
    y = 30
    for i, text in enumerate(steps):
        c.box(120, y, 940, 100, text, fill=LIGHT if i not in (3, 4) else (255, 240, 220), f=F_TEXT)
        if i < len(steps) - 1:
            c.arrow((590, y + 100), (590, y + 140), BLACK, 3, 12)
        y += 140
    c.save("experiment_flow.png")


def wrap(lines: list, width: int) -> list:
    """Ngắt dòng dài thành nhiều dòng, dòng tiếp theo thụt vào cho dễ đọc."""
    out = []
    for text in lines:
        text = " ".join(text.replace("\t", " ").split())
        while len(text) > width:
            cut = text.rfind(" ", 0, width)
            if cut <= 0:
                cut = width
            out.append(text[:cut])
            text = "    " + text[cut:].strip()
        out.append(text)
    return out


def tmux_balance():
    """Vẽ lại 4 ô màn hình demo ở cuối lượt balance, từ chính các file kết quả của lượt đó."""
    client = [l for l in (DATA / "client_balance.log").read_text(encoding="utf-8").splitlines() if l.strip()]
    link_rows = (DATA / "link_balance.csv").read_text().splitlines()[1:]
    server_rows = (DATA / "server_balance.csv").read_text().splitlines()[1:]
    events = [l for l in (DATA / "events_balance.log").read_text(encoding="utf-8").splitlines() if l.strip()]

    link = []
    for row in link_rows[-6:]:
        t, long_b, short_b = row.split(",")
        link.append(f"t={int(t):2d}  đường dài: {int(long_b) * 8 / 1e6:6.2f}   đường ngắn: {int(short_b) * 8 / 1e6:6.2f} Mbit/s")
    server = []
    for row in server_rows:
        t, _, value = row.split(",")
        if 55 <= int(t) <= 60:
            server.append(f"t={int(t):2d}  {float(value):6.2f} Mbit/s")
    panes = [
        ("Ô trên trái: client (RTT, jitter, mất gói mỗi giây), 6 dòng cuối", ["..."] + client[-6:]),
        ("Ô dưới trái: lưu lượng R1 gửi ra từng đường, 6 dòng cuối", ["..."] + link),
        ("Ô trên phải: thông lượng server nhận được, giây 55 tới 60", ["..."] + server),
        ("Ô dưới phải: tiến trình demo.sh", wrap(events, 92)),
    ]
    mono = font(7, mono=True)
    label_font = font(8)
    line_h = int(7 * PT * 1.25)
    label_h = int(8 * PT * 1.4)
    height = sum(label_h + len(body) * line_h + 40 for _, body in panes) + 20
    img = Image.new("RGB", (WIDTH, height), "white")
    draw = ImageDraw.Draw(img)
    y = 10
    for label, body in panes:
        draw.text((12, y), label, font=label_font, fill=GREY)
        y += label_h
        top = y
        draw.rectangle([8, top, WIDTH - 8, top + len(body) * line_h + 20], fill=(250, 250, 250), outline=GREY, width=2)
        y += 10
        for text in body:
            draw.text((20, y), text.replace("\t", " "), font=mono, fill=BLACK)
            y += line_h
        y += 30
    img.save(OUT / "tmux_balance.png", dpi=(DPI, DPI))


def eve_placeholder():
    """Khung chờ: người dùng thay bằng ảnh chụp giao diện web EVE-NG mở lab net-perf."""
    c = Canvas(7)
    c.draw.rectangle([10, 10, WIDTH - 10, c.img.height - 10], outline=GREY, width=4)
    c.text((WIDTH / 2, c.img.height / 2),
           "[Ảnh chụp giao diện EVE-NG: lab net-perf với 6 node]\n"
           "Mở http://<IP máy EVE>, vào lab net-perf, chụp màn hình\n"
           "rồi dán đè lên khung này (giữ nguyên nhãn hình bên dưới).", F_TEXT, GREY)
    c.save("eve_placeholder.png")


def charts():
    subprocess.run([str(ROOT / "scripts/plot.sh"), str(DATA)], check=True, stdout=subprocess.DEVNULL)
    for name in ["rtt.png", "rtt_low.png", "jitter.png", "throughput.png", "paths.png"]:
        shutil.copyfile(DATA / name, OUT / name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tcpip()
    delay_parts()
    queue_build_up()
    topology()
    three_runs()
    ecmp_hash()
    experiment_flow()
    tmux_balance()
    eve_placeholder()
    charts()
    for path in sorted(OUT.glob("*.png")):
        print(path.name)


if __name__ == "__main__":
    main()
