#!/usr/bin/env bash
# Run Opus on every verified task with parallel=N, write a live summary.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

N=${PCB_OPUS_PARALLEL:-3}
SUMMARY="bench_runs/_summary.txt"
mkdir -p bench_runs
: > "$SUMMARY"

sem() {
  while [ "$(jobs -rp | wc -l)" -ge "$N" ]; do sleep 5; done
}

for f in tasks/*.json; do
  inst=$(basename "$f" .json)
  if [ -f "bench_runs/${inst}/grade.json" ]; then
    echo "[skip] $inst (already graded)"
    continue
  fi
  sem
  (
    bash scripts/run_opus.sh "$f" >> "$SUMMARY" 2>&1
  ) &
  echo "[launch] $inst (pid=$!)"
done
wait

echo
echo "=== FINAL TALLY ==="
total=0
passed=0
for g in bench_runs/*/grade.json; do
  total=$((total+1))
  if [ "$(python3 -c "import json; print(json.load(open('$g'))['passed'])")" = "True" ]; then
    passed=$((passed+1))
  fi
done
echo "Pass rate: $passed/$total"
