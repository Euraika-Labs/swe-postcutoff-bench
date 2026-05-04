#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
N=${PCB_QWEN_PARALLEL:-3}
SUMMARY="bench_runs_qwen/_summary.txt"
mkdir -p bench_runs_qwen
: > "$SUMMARY"

sem() { while [ "$(jobs -rp | wc -l)" -ge "$N" ]; do sleep 5; done; }

for f in tasks/*.json; do
  inst=$(basename "$f" .json)
  if [ -f "bench_runs_qwen/${inst}/grade.json" ]; then
    echo "[skip] $inst (already graded)"
    continue
  fi
  sem
  ( bash scripts/run_qwen.sh "$f" >> "$SUMMARY" 2>&1 ) &
  echo "[launch] $inst (pid=$!)"
done
wait
echo
echo "=== FINAL TALLY ==="
total=0; passed=0
for g in bench_runs_qwen/*/grade.json; do
  total=$((total+1))
  if [ "$(python3 -c "import json; print(json.load(open('$g'))['passed'])")" = "True" ]; then
    passed=$((passed+1))
  fi
done
echo "qwen3-coder-next: $passed/$total"
