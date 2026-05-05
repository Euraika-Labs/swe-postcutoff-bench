#!/usr/bin/env bash
TASK="${1:?need task}"
MODEL="qwen/qwen3-coder-480b-a35b-instruct"
OUTDIR="nim_qwen480_oss"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/_nim_common.sh"
write_prompt_coder

# Run via Python harness using OpenAI-native tool calling
START_TS=$(date +%s)
( cd "$WD" && \
  OSS_API_URL="https://integrate.api.nvidia.com/v1/chat/completions" \
  OSS_API_KEY="$NIM_KEY" \
  python3 - <<PYEOF > "$LOG" 2>&1 < /dev/null
import json, sys, os
sys.path.insert(0, "$ROOT/scripts")
from pathlib import Path
import oss_native_nim as oss
task = json.loads(open("$TASK").read())
diff = oss.run_oss_native(Path("$WD"), task, Path("$LOG"), "$MODEL", 0.3)
PYEOF
)
finish_grade
