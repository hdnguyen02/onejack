#!/bin/bash
# Copy chương trình C và script cấu hình vào /root/ của từng node EVE,
# rồi chạy lab/<node>.sh để đặt IP, route, tc. Chạy trong máy ảo EVE.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

while read -r node ip; do
    case "$node" in
        ''|'#'*) continue ;;
    esac
    scp -q $SSH_OPTS "$ROOT"/build/server "$ROOT"/build/client "$ROOT"/build/attacker \
        "$ROOT"/build/guard "$ROOT"/scripts/linkmon.sh "$ROOT/lab/$node.sh" "root@$ip:/root/"
    # Đồng bộ giờ với máy EVE để log của các node xếp đúng thứ tự.
    ssh -n $SSH_OPTS "root@$ip" "date -s @$(date +%s) >/dev/null; sh /root/$node.sh"
    echo "$node ($ip): đã copy và cấu hình"
done < "$ROOT/lab/nodes.conf"
