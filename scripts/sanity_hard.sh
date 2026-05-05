#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p grades_hard
N=4
sem() { while [ "$(jobs -rp | wc -l)" -ge "$N" ]; do sleep 1; done; }
for f in tasks_hard/*.json; do
  name=$(basename "$f" .json)
  out="grades_hard/${name}__GOLD.json"
  [ -f "$out" ] && continue
  sem
  ( timeout 1500 python3 scripts/run_task.py --task-file "$f" \
      --workdir-root /tmp/pcb_hard_workdirs \
      --out "$out" --timeout 1200 \
      > "grades_hard/${name}__GOLD.stdout" 2>&1 ) &
done
wait
echo "[hard sanity done]"
