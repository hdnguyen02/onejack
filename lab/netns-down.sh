#!/bin/bash
# Xóa toàn bộ namespace của mini-lab.
for n in loadgen client r1 r2 r3 server sw; do
    ip netns del "$n" 2>/dev/null || true
done
echo "netns lab: đã xóa"
