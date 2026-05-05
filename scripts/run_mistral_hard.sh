#!/usr/bin/env bash
# mistral-small-4-119b via mistral-vibe (purpose-built Mistral CLI).
# Best harness for Mistral per matrix.
set -uo pipefail
TASK="${1:?need task json}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VIBE_BIN="/opt/projects/research/papers/2026-04-coding-parity-small-tuned/experiments/tier2_smoke/.venv/bin/vibe"
[ -x "$VIBE_BIN" ] || { echo "vibe binary not at $VIBE_BIN"; exit 2; }

INST=$(python3 -c "import json; print(json.load(open('$TASK'))['instance_id'])")
REPO=$(python3 -c "import json; print(json.load(open('$TASK'))['repo'])")
SHA=$(python3 -c "import json; print(json.load(open('$TASK'))['base_commit'])")
PROBLEM=$(python3 -c "import json; t=json.load(open('$TASK')); print(t.get('title','') + chr(10) + chr(10) + (t.get('problem_statement') or ''))")

OUT="$ROOT/bench_runs_hard_mistral/$INST"
WD="$OUT/workdir"
mkdir -p "$OUT"; rm -rf "$WD"

git clone --quiet "https://github.com/$REPO.git" "$WD" 2>"$OUT/clone.err"
( cd "$WD" && git checkout --quiet "$SHA" )

python3 -c "import json; print(json.load(open('$TASK')).get('test_patch',''))" > "$OUT/test.patch"
( cd "$WD" && git apply --whitespace=nowarn "$OUT/test.patch" ) 2>"$OUT/test_patch.err"
TP_RC=$?
[ $TP_RC -ne 0 ] && { echo "[ERROR] test_patch failed" >&2; exit 2; }
( cd "$WD" \
  && git -c user.email=bench@local -c user.name=bench add -A \
  && git -c user.email=bench@local -c user.name=bench commit --quiet -m "test_patch checkpoint" ) 2>>"$OUT/test_patch.err"

cat > "$OUT/prompt.md" <<PEOF
You are debugging a real GitHub issue in the \`$REPO\` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
$PROBLEM

# Your task
1. **First**: \`git diff HEAD\` to see the failing tests already present.
2. Read those tests to understand what behavior is expected.
3. Investigate the relevant source files (NOT test files).
4. Fix the bug by editing source files only.
5. Run the test suite locally to confirm.
6. Stop — your final source-file edits are graded by an automated runner.

# Hard constraints
- Failing tests are ALREADY in the repo. Do not re-add them — that causes "redeclared in this block" errors.
- Edit source files only. Never modify, add to, or duplicate test files.
- Stay focused on the bug fix.
PEOF

LOG="$OUT/agent.log"
START=$(date +%s)
PROMPT="$(cat "$OUT/prompt.md")"
REGOLO_API_KEY="sk-bK-bqo0KwS6QMWCVCT7W3w" \
NODE_TLS_REJECT_UNAUTHORIZED=0 \
timeout 1500 "$VIBE_BIN" \
  -p "$PROMPT" \
  --max-turns 60 \
  --output text \
  --workdir "$WD" \
  --trust \
  > "$LOG" 2>&1 < /dev/null
RC=$?
ELAPSED=$(( $(date +%s) - START ))
echo "[done rc=$RC elapsed=${ELAPSED}s]" >> "$LOG"

( cd "$WD" && git add -A && git diff HEAD ) > "$OUT/agent.diff" 2>"$OUT/diff.err"

python3 scripts/run_task.py \
  --task-file "$TASK" --patch "$OUT/agent.diff" \
  --workdir-root "/tmp/pcb_grade_workdirs_hard_mistral" \
  --out "$OUT/grade.json" --timeout 600 \
  > "$OUT/grade.log" 2>&1

PASSED=$(python3 -c "import json; print(json.load(open('$OUT/grade.json'))['passed'])" 2>/dev/null || echo "?")
F2P=$(python3 -c "import json; d=json.load(open('$OUT/grade.json')); print(f\"{d['fail_to_pass_passed']}/{d['fail_to_pass_total']}\")" 2>/dev/null || echo "?")
echo "$INST  agent=${ELAPSED}s  passed=$PASSED  F2P=$F2P"
