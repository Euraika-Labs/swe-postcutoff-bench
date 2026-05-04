#!/usr/bin/env bash
# Run gold-patch sanity for every task in tasks/, in parallel batches.
# Results land in grades/<instance_id>__GOLD.json
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p grades

# Run up to N=4 in parallel to avoid overwhelming network/disk
N=${PCB_SANITY_PARALLEL:-3}
sem() {
  while [ "$(jobs -rp | wc -l)" -ge "$N" ]; do
    sleep 1
  done
}

for f in tasks/*.json; do
  name=$(basename "$f" .json)
  out="grades/${name}__GOLD.json"
  if [ -f "$out" ]; then
    echo "[skip] $name (already graded)"
    continue
  fi
  sem
  (
    timeout 900 python3 scripts/run_task.py --task-file "$f" --timeout 600 \
      > "grades/${name}__GOLD.stdout" 2>&1
  ) &
  echo "[launch] $name (pid=$!)"
done
wait
echo "[all done]"
