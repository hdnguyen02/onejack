#!/bin/bash
# Chạy liên tiếp 4 lượt đo rồi vẽ biểu đồ và in bảng so sánh.
# Cách dùng: run-all.sh   (LAB=eve mặc định, LAB=netns cho mini-lab)
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export LAB="${LAB:-eve}"
for m in base fqcodel multipath combined; do
    "$ROOT/scripts/demo.sh" "$m"
done
"$ROOT/scripts/plot.sh"
