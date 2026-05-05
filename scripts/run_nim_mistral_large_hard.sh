#!/usr/bin/env bash
TASK="${1:?need task}"; MODEL="mistralai/mistral-large-3-675b-instruct-2512"; OUTDIR="nim_mistral_large"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/_nim_common.sh"
write_prompt_general
PROMPT="$(cat "$OUT/prompt.md")"
( cd "$WD" && \
  CLAUDE_CODE_USE_OPENAI=1 \
  OPENAI_BASE_URL="https://integrate.api.nvidia.com/v1" \
  OPENAI_API_KEY="$NIM_KEY" \
  OPENAI_MODEL="$MODEL" \
  NODE_TLS_REJECT_UNAUTHORIZED=0 \
  timeout 1500 openclaude \
    --bare \
    --dangerously-skip-permissions \
    --add-dir "$WD" \
    -p "$PROMPT" \
) > "$LOG" 2>&1 < /dev/null
finish_grade
