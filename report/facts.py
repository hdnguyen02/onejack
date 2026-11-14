"""Bảng số liệu cho báo cáo, tính từ file kết quả đo thật.

Mọi con số đo đạc trong báo cáo đều lấy từ đây (qua token {{tên}}),
không gõ tay, để báo cáo luôn khớp với dữ liệu trong results/.
"""
import re
from pathlib import Path

ATTACK_AT = 15


def vn_number(value: float, decimals: int) -> str:
    """Định dạng số kiểu Việt: dấu phẩy thập phân, dấu chấm phân cách hàng nghìn."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def average_after_attack(csv_path: Path, column: int) -> float:
    """Trung bình một cột CSV trên các dòng có t > ATTACK_AT (giống scripts/plot.sh)."""
    total = 0.0
    count = 0
    lines = csv_path.read_text().splitlines()
    for line in lines[1:]:
        fields = line.split(",")
        if int(fields[0]) > ATTACK_AT:
            total += float(fields[column])
            count += 1
    return total / count


def seconds_of_day(stamp: str) -> float:
    hours, minutes, seconds = stamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def event_times(events_path: Path) -> dict:
    """Thời điểm bắt đầu tấn công, R3 phát hiện, R1 nhận cảnh báo (giây trong ngày)."""
    times = {}
    for line in events_path.read_text().splitlines():
        stamp = line.split(" ", 1)[0]
        if "[demo] BẮT ĐẦU TẤN CÔNG" in line and "start" not in times:
            times["start"] = seconds_of_day(stamp)
        elif "[R3] PHÁT HIỆN" in line and "detect" not in times:
            times["detect"] = seconds_of_day(stamp)
        elif "[R1] NHẬN" in line and "block" not in times:
            times["block"] = seconds_of_day(stamp)
    return times


def qos_rtts(path: Path) -> tuple:
    text = path.read_text()
    normal = re.search(r"RTT truy vấn thường:\s+([\d.]+) ms", text)
    priority = re.search(r"RTT truy vấn ưu tiên:\s+([\d.]+) ms", text)
    return float(normal.group(1)), float(priority.group(1))


def qdisc_counters(path: Path, handle: str) -> tuple:
    """(số gói đã gửi, số gói bị vứt) của một bfifo trong kết quả `tc -s qdisc`."""
    match = re.search(
        r"qdisc bfifo " + handle + r":.*?\n\s*Sent \d+ bytes (\d+) pkt \(dropped (\d+)",
        path.read_text(),
    )
    return int(match.group(1)), int(match.group(2))


def shell_value(script: Path, name: str) -> str:
    match = re.search(r"^" + name + r"=(\d+)", script.read_text(), re.M)
    return match.group(1)


def load_facts(results_dir: Path, demo_sh: Path) -> dict:
    facts = {}

    for mode in ["off", "on", "inband"]:
        rtt = average_after_attack(results_dir / f"client_{mode}.csv", 4)
        link_bytes = average_after_attack(results_dir / f"link_{mode}.csv", 1)
        facts[f"rtt_{mode}"] = vn_number(rtt, 2)
        facts[f"link_{mode}"] = vn_number(link_bytes * 8 / 1_000_000, 2)

        times = event_times(results_dir / f"events_{mode}.log")
        facts[f"detect_{mode}"] = vn_number(times["detect"] - times["start"], 3)
        if "block" in times:
            facts[f"block_{mode}_ms"] = str(round((times["block"] - times["detect"]) * 1000))

    normal, priority = qos_rtts(results_dir / "qos-check-eve.txt")
    facts["qos_normal_eve"] = vn_number(normal, 2)
    facts["qos_prio_eve"] = vn_number(priority, 2)
    normal, priority = qos_rtts(results_dir / "qos-check-netns.txt")
    facts["qos_normal_netns"] = vn_number(normal, 2)
    facts["qos_prio_netns"] = vn_number(priority, 2)

    prio_sent, _ = qdisc_counters(results_dir / "qos-check-eve.txt", "101")
    _, normal_dropped = qdisc_counters(results_dir / "qos-check-eve.txt", "102")
    facts["qos_prio_pkts"] = vn_number(prio_sent, 0)
    facts["qos_normal_dropped"] = vn_number(normal_dropped, 0)

    facts["duration"] = shell_value(demo_sh, "DURATION")
    facts["attack_at"] = shell_value(demo_sh, "ATTACK_AT")
    facts["client_rate"] = shell_value(demo_sh, "CLIENT_RATE")
    facts["attack_rate"] = vn_number(int(shell_value(demo_sh, "ATTACK_RATE")), 0)
    facts["attack_size"] = vn_number(int(shell_value(demo_sh, "ATTACK_SIZE")), 0)
    facts["threshold"] = shell_value(demo_sh, "THRESHOLD")

    router = (demo_sh.parent.parent / "lab/r1.sh").read_text()
    facts["bottleneck"] = re.search(r'TC_RATE:-(\d+)mbit', router).group(1)
    queue_bytes = int(re.search(r"bfifo limit (\d+)", router).group(1))
    facts["queue_kb"] = str(queue_bytes // 1000)

    return facts
