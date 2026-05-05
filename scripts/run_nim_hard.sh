#!/usr/bin/env bash
# Generic NIM harness — qwen CLI pointed at integrate.api.nvidia.com.
# Usage: scripts/run_nim_hard.sh <task.json> <model_id> <out_subdir>
set -uo pipefail

TASK="${1:?need task json}"
MODEL="${2:?need NIM model id}"
OUTDIR="${3:?need out subdir name (e.g. nim_qwen480)}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Pull NIM key from Vault on every run (cheap, < 1s)
export VAULT_ADDR="${VAULT_ADDR:-https://vault.euraika.net}"
NIM_KEY=$(vault kv get -mount=secret -field=api_key api-keys/nvidia-nim 2>/dev/null)
[ -z "$NIM_KEY" ] && { echo "[ERROR] could not fetch NIM key from Vault" >&2; exit 3; }

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
- Failing tests are ALREADY in the repo. Do not re-add them.
- Edit source files only.
- Stay focused on the bug fix.
PEOF

LOG="$OUT/agent.log"
START=$(date +%s)
PROMPT="$(cat "$OUT/prompt.md")"
( cd "$WD" && \
  NODE_TLS_REJECT_UNAUTHORIZED=0 \
  timeout 1500 qwen \
    -y \
    -m "$MODEL" \
    --openai-base-url "https://integrate.api.nvidia.com/v1" \
    --openai-api-key "$NIM_KEY" \
    --auth-type openai \
    -p "$PROMPT" \
) > "$LOG" 2>&1 < /dev/null
RC=$?
ELAPSED=$(( $(date +%s) - START ))
echo "[done rc=$RC elapsed=${ELAPSED}s model=$MODEL]" >> "$LOG"

( cd "$WD" && git add -A && git diff HEAD ) > "$OUT/agent.diff" 2>"$OUT/diff.err"

python3 scripts/run_task.py \
  --task-file "$TASK" --patch "$OUT/agent.diff" \
  --workdir-root "/tmp/pcb_grade_workdirs_hard_${OUTDIR}" \
  --out "$OUT/grade.json" --timeout 600 \
  > "$OUT/grade.log" 2>&1

PASSED=$(python3 -c "import json; print(json.load(open('$OUT/grade.json'))['passed'])" 2>/dev/null || echo "?")
F2P=$(python3 -c "import json; d=json.load(open('$OUT/grade.json')); print(f\"{d['fail_to_pass_passed']}/{d['fail_to_pass_total']}\")" 2>/dev/null || echo "?")
echo "$INST  agent=${ELAPSED}s  passed=$PASSED  F2P=$F2P  model=$MODEL"
