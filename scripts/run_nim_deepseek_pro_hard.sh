#!/usr/bin/env bash
TASK="${1:?need task}"; MODEL="deepseek-ai/deepseek-v4-pro"; OUTDIR="nim_deepseek_pro"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/_nim_common.sh"
write_prompt_general
PROMPT="$(cat "$OUT/prompt.md")"
( cd "$WD" && \
  NODE_TLS_REJECT_UNAUTHORIZED=0 \
  timeout 1500 qwen -y -m "$MODEL" \
    --openai-base-url "https://integrate.api.nvidia.com/v1" \
    --openai-api-key "$NIM_KEY" \
    --auth-type openai \
    -p "$PROMPT" \
) > "$LOG" 2>&1 < /dev/null
finish_grade
