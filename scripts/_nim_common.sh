# Sourced by run_nim_*_hard.sh — provides $TASK $MODEL $OUTDIR $INST $REPO $SHA $PROBLEM $OUT $WD setup
#
# Caller must pre-set: TASK, MODEL, OUTDIR
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export VAULT_ADDR="${VAULT_ADDR:-https://vault.euraika.net}"
NIM_KEY=$(vault kv get -mount=secret -field=api_key api-keys/nvidia-nim 2>/dev/null)
[ -z "$NIM_KEY" ] && { echo "[ERROR] NIM key fetch failed" >&2; exit 3; }

INST=$(python3 -c "import json; print(json.load(open('$TASK'))['instance_id'])")
REPO=$(python3 -c "import json; print(json.load(open('$TASK'))['repo'])")
SHA=$(python3 -c "import json; print(json.load(open('$TASK'))['base_commit'])")
PROBLEM=$(python3 -c "import json; t=json.load(open('$TASK')); print(t.get('title','') + chr(10) + chr(10) + (t.get('problem_statement') or ''))")

OUT="$ROOT/bench_runs_hard_${OUTDIR}/$INST"
WD="$OUT/workdir"
mkdir -p "$OUT"; rm -rf "$WD"

git clone --quiet "https://github.com/$REPO.git" "$WD" 2>"$OUT/clone.err"
( cd "$WD" && git checkout --quiet "$SHA" )

python3 -c "import json; print(json.load(open('$TASK')).get('test_patch',''))" > "$OUT/test.patch"
( cd "$WD" && git apply --whitespace=nowarn "$OUT/test.patch" ) 2>"$OUT/test_patch.err"
TP_RC=$?
[ $TP_RC -ne 0 ] && { echo "[ERROR] test_patch failed rc=$TP_RC" >&2; exit 2; }
( cd "$WD" \
  && git -c user.email=bench@local -c user.name=bench add -A \
  && git -c user.email=bench@local -c user.name=bench commit --quiet -m "test_patch checkpoint" ) 2>>"$OUT/test_patch.err"

LOG="$OUT/agent.log"
START_TS=$(date +%s)

write_prompt_coder() {
  cat > "$OUT/prompt.md" <<PEOF
The repo \`$REPO\` is cloned in this workdir. Failing tests have been added to the test files.

# Issue
$PROBLEM

# Task
1. \`git diff HEAD\` to see the new failing tests.
2. Read them — they show what behavior is expected.
3. Edit source files (NOT tests) to make them pass.
4. Verify with the project's test command if you can.

# Constraints
- Tests already exist; never duplicate them.
- Source files only — no test additions.
PEOF
}

write_prompt_general() {
  cat > "$OUT/prompt.md" <<PEOF
You are debugging a real GitHub issue in the \`$REPO\` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
$PROBLEM

# Step-by-step plan
1. **Locate**: \`git diff HEAD\` to see the failing tests already present.
2. **Understand**: read those tests carefully — they encode the expected behavior.
3. **Investigate**: find the source files responsible for the bug.
4. **Fix**: edit source files only.
5. **Verify**: run the test command if possible.
6. **Stop**: your final source-file edits are graded automatically.

# Hard constraints
- Failing tests are ALREADY in the repo. Do not duplicate them.
- Edit source files only. Never modify test files.
- Stay focused on the bug fix; no refactoring.
PEOF
}

finish_grade() {
  ELAPSED=$(( $(date +%s) - START_TS ))
  echo "[done elapsed=${ELAPSED}s model=$MODEL]" >> "$LOG"
  ( cd "$WD" && git add -A && git diff HEAD ) > "$OUT/agent.diff" 2>"$OUT/diff.err"
  python3 scripts/run_task.py \
    --task-file "$TASK" --patch "$OUT/agent.diff" \
    --workdir-root "/tmp/pcb_grade_workdirs_${OUTDIR}" \
    --out "$OUT/grade.json" --timeout 600 \
    > "$OUT/grade.log" 2>&1
  PASSED=$(python3 -c "import json; print(json.load(open('$OUT/grade.json'))['passed'])" 2>/dev/null || echo "?")
  F2P=$(python3 -c "import json; d=json.load(open('$OUT/grade.json')); print(f\"{d['fail_to_pass_passed']}/{d['fail_to_pass_total']}\")" 2>/dev/null || echo "?")
  echo "$INST  agent=${ELAPSED}s  passed=$PASSED  F2P=$F2P  model=$MODEL"
}
