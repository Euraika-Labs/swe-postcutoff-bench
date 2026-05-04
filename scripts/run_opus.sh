#!/usr/bin/env bash
# Per-task harness: spawn `claude` (Opus) on a workdir, extract diff, grade it.
#
# Usage: scripts/run_opus.sh tasks/<instance_id>.json
#
# Writes:
#   bench_runs/<instance_id>/workdir/   — the cloned repo Opus operates in
#   bench_runs/<instance_id>/prompt.md  — the prompt sent to Opus
#   bench_runs/<instance_id>/agent.log  — Opus stdout/stderr
#   bench_runs/<instance_id>/agent.diff — diff of workdir after agent run
#   bench_runs/<instance_id>/grade.json — final grading
set -uo pipefail

TASK="${1:?need task json}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INST=$(python3 -c "import json; print(json.load(open('$TASK'))['instance_id'])")
REPO=$(python3 -c "import json; print(json.load(open('$TASK'))['repo'])")
SHA=$(python3 -c "import json; print(json.load(open('$TASK'))['base_commit'])")
PROBLEM=$(python3 -c "import json,sys; t=json.load(open('$TASK')); print(t.get('title','') + chr(10) + chr(10) + (t.get('problem_statement') or ''))")

OUT="$ROOT/bench_runs/$INST"
WD="$OUT/workdir"
mkdir -p "$OUT"
rm -rf "$WD"

# 1) Clone at base_commit (absolute paths so subshell cwd doesn't matter)
git clone --quiet "https://github.com/$REPO.git" "$WD" 2>"$OUT/clone.err"
( cd "$WD" && git checkout --quiet "$SHA" )

# 2) Apply test_patch FIRST so Opus sees the failing tests in the workdir.
python3 -c "
import json
t = json.load(open('$TASK'))
print(t.get('test_patch',''))
" > "$OUT/test.patch"
( cd "$WD" && git apply --whitespace=nowarn "$OUT/test.patch" ) 2>"$OUT/test_patch.err"
TP_RC=$?
if [ $TP_RC -ne 0 ]; then
  echo "[ERROR] test_patch failed to apply (rc=$TP_RC); aborting" >&2
  cat "$OUT/test_patch.err" >&2
  exit 2
fi
# Commit it as a checkpoint so the agent.diff captures ONLY Opus's source changes,
# not the test_patch (which run_task.py re-applies during grading).
( cd "$WD" \
  && git -c user.email=bench@local -c user.name=bench add -A \
  && git -c user.email=bench@local -c user.name=bench commit --quiet -m "test_patch checkpoint" ) 2>>"$OUT/test_patch.err"

# 3) Build prompt
cat > "$OUT/prompt.md" <<EOF
You are debugging a real GitHub issue in the \`$REPO\` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
$PROBLEM

# Your task
1. **First**: \`git diff HEAD\` in the workdir to see what tests are already present. They are the FAIL_TO_PASS tests you need to make pass — do NOT re-create them.
2. Read those tests to understand what behavior is expected.
3. Investigate the relevant source files (NOT test files).
4. Fix the bug by editing source files only.
5. Run the test suite locally to confirm your fix.
6. Stop — your final source-file edits are graded by an automated runner.

# Hard constraints
- The failing tests are ALREADY in the repo. Do not add tests with the same name — that causes "redeclared in this block" or "duplicate test" errors.
- Edit source files only. Never edit, add to, or duplicate test files.
- Stay focused: fix only what the issue describes; no refactors or unrelated changes.
EOF

# 4) Spawn Opus via claude CLI, scoped to the workdir
LOG="$OUT/agent.log"
START=$(date +%s)
timeout 1200 claude \
  -p "$(cat "$OUT/prompt.md")" \
  --dangerously-skip-permissions \
  --add-dir "$WD" \
  > "$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START ))
echo "[done rc=$RC elapsed=${ELAPSED}s]" >> "$LOG"

# 5) Extract the agent's diff (everything since base_commit + test_patch)
( cd "$WD" && git add -A && git diff HEAD ) > "$OUT/agent.diff" 2>"$OUT/diff.err"

# 6) Grade — feed agent.diff back through run_task.py
python3 scripts/run_task.py \
  --task-file "$TASK" \
  --patch "$OUT/agent.diff" \
  --workdir-root "/tmp/pcb_grade_workdirs" \
  --out "$OUT/grade.json" \
  --timeout 600 \
  > "$OUT/grade.log" 2>&1
GRADE_RC=$?

# 7) Report
PASSED=$(python3 -c "import json; print(json.load(open('$OUT/grade.json'))['passed'])" 2>/dev/null || echo "?")
F2P=$(python3 -c "import json; d=json.load(open('$OUT/grade.json')); print(f\"{d['fail_to_pass_passed']}/{d['fail_to_pass_total']}\")" 2>/dev/null || echo "?")
echo "$INST  agent=${ELAPSED}s  passed=$PASSED  F2P=$F2P"
