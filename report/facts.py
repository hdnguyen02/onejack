"""Bảng số liệu cho báo cáo, tính từ file kết quả đo thật.

Mọi con số đo đạc trong báo cáo đều lấy từ đây (qua token {{tên}}),
không gõ tay, để báo cáo luôn khớp với dữ liệu trong results/.
Cách lấy trung bình giống scripts/plot.sh.
"""
import re
from pathlib import Path

MODES = ["base", "short", "balance"]


def vn_number(value: float, decimals: int) -> str:
    """Định dạng số kiểu Việt: dấu phẩy thập phân, dấu chấm phân cách hàng nghìn."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def read_rows(csv_path: Path) -> list:
    """Các dòng dữ liệu của file CSV (bỏ dòng tiêu đề), mỗi dòng là list số thực."""
    rows = []
    for line in csv_path.read_text().splitlines()[1:]:
        if line.strip() == "":
            continue
        rows.append([float(value) for value in line.split(",")])
    return rows


def average_loaded(csv_path: Path, column: int, load_at: int, duration: int) -> float:
    """Trung bình một cột trong lúc có tải: từ giây load_at + 2 tới giây duration - 1.
    Bỏ giây đầu tiên có tải (đang chuyển trạng thái) và giây cuối (tải dừng giữa chừng);
    file của server còn vài dòng sau khi lượt kết thúc nên phải chặn theo duration."""
    values = []
    for row in read_rows(csv_path):
        if row[0] > load_at + 1 and row[0] < duration:
            values.append(row[column])
    return sum(values) / len(values)


def average_idle(csv_path: Path, column: int, load_at: int) -> float:
    """Trung bình một cột lúc chưa có tải: từ giây 2 tới trước giây load_at."""
    values = []
    for row in read_rows(csv_path):
        if row[0] > 1 and row[0] < load_at:
            values.append(row[column])
    return sum(values) / len(values)


def shell_value(script: Path, name: str) -> str:
    match = re.search(r"^" + name + r"=(\d+)", script.read_text(), re.M)
    return match.group(1)


def mbit(bytes_per_second: float) -> float:
    return bytes_per_second * 8 / 1_000_000


def load_facts(results_dir: Path, demo_sh: Path) -> dict:
    facts = {}
    root = demo_sh.parent.parent

    load_at = int(shell_value(demo_sh, "LOAD_AT"))
    duration = int(shell_value(demo_sh, "DURATION"))
    load_rate = int(shell_value(demo_sh, "LOAD_RATE"))
    load_size = int(shell_value(demo_sh, "LOAD_SIZE"))
    facts["duration"] = shell_value(demo_sh, "DURATION")
    facts["load_at"] = str(load_at)
    facts["client_rate"] = shell_value(demo_sh, "CLIENT_RATE")
    facts["load_rate"] = vn_number(load_rate, 0)
    facts["load_size"] = vn_number(load_size, 0)
    facts["load_flows"] = shell_value(demo_sh, "LOAD_FLOWS")
    load_mbit = load_rate * load_size * 8 / 1_000_000
    facts["load_mbit"] = vn_number(load_mbit, 0)

    router = (root / "lab/r1.sh").read_text()
    link_rate = int(re.search(r"LINK_RATE:-(\d+)mbit", router).group(1))
    link_delay = int(re.search(r"LINK_DELAY:-(\d+)ms", router).group(1))
    queue_latency_ms = int(re.search(r"latency (\d+)ms", router).group(1))
    facts["link_rate"] = str(link_rate)
    facts["link_delay"] = str(link_delay)
    facts["two_links_mbit"] = str(2 * link_rate)
    # Hàng đợi của tbf được tính từ tham số latency: chứa đủ số byte truyền trong khoảng thời gian đó.
    facts["queue_delay_ms"] = str(queue_latency_ms)
    facts["queue_kb"] = str(link_rate * 1_000_000 // 8 * queue_latency_ms // 1000 // 1000)
    # RTT lý thuyết chỉ tính độ trễ truyền: đi và về qua 2 link (đường dài) hoặc 1 link (đường ngắn).
    facts["prop_long_ms"] = str(4 * link_delay)
    facts["prop_short_ms"] = str(2 * link_delay)
    facts["prop_mixed_ms"] = str(3 * link_delay)

    # Ngưỡng độ trễ một chiều khuyến nghị cho thoại (ITU-T G.114), dùng để đối chiếu.
    facts["g114_ms"] = "150"

    image_script = (root / "lab/eve-make-image.sh").read_text()
    facts["alpine_version"] = re.search(r"--branch v([\d.]+)", image_script).group(1)

    values = {}
    for mode in MODES:
        client = results_dir / f"client_{mode}.csv"
        server = results_dir / f"server_{mode}.csv"
        link = results_dir / f"link_{mode}.csv"
        values[mode] = {
            "idle": average_idle(client, 4, load_at),
            "rtt": average_loaded(client, 4, load_at, duration),
            "jitter": average_loaded(client, 5, load_at, duration),
            "loss": average_loaded(client, 3, load_at, duration),
            "server": average_loaded(server, 2, load_at, duration),
            "long": mbit(average_loaded(link, 1, load_at, duration)),
            "short": mbit(average_loaded(link, 2, load_at, duration)),
        }
        facts[f"idle_{mode}"] = vn_number(values[mode]["idle"], 2)
        facts[f"rtt_{mode}"] = vn_number(values[mode]["rtt"], 2)
        facts[f"jitter_{mode}"] = vn_number(values[mode]["jitter"], 2)
        facts[f"loss_{mode}"] = vn_number(values[mode]["loss"], 1)
        facts[f"server_{mode}"] = vn_number(values[mode]["server"], 2)
        facts[f"long_{mode}"] = vn_number(values[mode]["long"], 2)
        facts[f"short_{mode}"] = vn_number(values[mode]["short"], 2)
        # Phần độ trễ tăng thêm khi có tải, chủ yếu là thời gian xếp hàng.
        facts[f"queue_added_{mode}"] = vn_number(values[mode]["rtt"] - values[mode]["idle"], 2)
        # Phần tải không tới được server (bị bỏ khi hàng đợi đầy).
        dropped = (load_mbit - values[mode]["server"]) / load_mbit * 100
        if dropped < 0.05:
            dropped = 0.0   # server nhận đủ (cộng cả truy vấn nhỏ của client nên có thể nhỉnh hơn tải)
        facts[f"dropped_pct_{mode}"] = vn_number(dropped, 1)

    base = values["base"]
    facts["idle_drop_short"] = vn_number((base["idle"] - values["short"]["idle"]) / base["idle"] * 100, 1)
    facts["rtt_drop_short"] = vn_number((base["rtt"] - values["short"]["rtt"]) / base["rtt"] * 100, 1)
    facts["rtt_drop_balance"] = vn_number((base["rtt"] - values["balance"]["rtt"]) / base["rtt"] * 100, 1)
    facts["rtt_ratio_balance"] = vn_number(base["rtt"] / values["balance"]["rtt"], 1)

    # Bản tiếng Anh (dùng cho Abstract): dấu chấm thập phân, dấu phẩy hàng nghìn.
    english = {}
    for key, value in facts.items():
        english[key + "_en"] = value.replace(".", "_").replace(",", ".").replace("_", ",")
    facts.update(english)

    return facts
