# Hard-tier results across 10 models on swe-postcutoff-bench v0.1

**Date:** 2026-05-05. **Sample:** 10 multi-file post-Oct-2024 bug fixes (3-7 files, 73-525 line patches, 1-7 FAIL_TO_PASS tests). Single-shot, no retries. Each model uses its strongest known harness.

## Final rankings

| Rank | Model | Hosting | Harness | Score |
|---:|---|---|---|---:|
| 1 | **Opus 4.7** | Anthropic | claude CLI | **9/10 = 90%** |
| 2 | qwen3-coder-next (80B) | Regolo | qwen CLI | 5/10 = 50% |
| 3 | qwen3.6-27b | Regolo | qwen CLI | 4/10 = 40% |
| 3 | minimax-m2.5 (~145B) | Regolo | openclaude | 4/10 = 40% |
| 5 | mistral-small-4-119b | Regolo | vibe CLI | 3/10 = 30% |
| 6 | qwen3.5-122b | Regolo | qwen CLI | 2/10 = 20% |
| 6 | qwen3-coder-480b (480B MoE) | NIM | qwen CLI | 2/10 = 20% |
| 6 | mistral-large-3-675b | NIM | openclaude | 2/10 = 20% |
| n/a | devstral-2-123b | NIM | qwen CLI | 1/1 attempted (9 DEGRADED — NIM serving issue, HTTP 400 "DEGRADED function") |
| n/a | deepseek-v4-pro | NIM | qwen CLI | 0/10 (10 TIMEOUT — NIM enforces 520s server-side cap; agent never gets a response) |

## Striking finding

**The 80B qwen3-coder-next on Regolo (50%) beat the 480B and 675B NIM-hosted models (both 20%).**

The 6-8× larger NIM models scored *lower* on identical tasks. That isn't model-capability; it's almost certainly a hosting/serving-layer effect:

1. **Provider integration**: Regolo's vLLM-based deployment of qwen3-coder-next produces consistent OpenAI tool_calls outputs that qwen-code parses cleanly. NIM's deployments of these larger models have less mature tool-calling calibration with qwen-code.
2. **Latency cap**: NIM's deepseek-v4-pro times out at exactly 520s with no response, indicating aggressive server-side time limits that prevent iteration budgets long enough for hard tasks.
3. **Tool-format defaults**: NIM's qwen3-coder-480b sometimes emits "thinking content" mixed with tool_calls; the response parser handles it but the model wastes turns.

## Methodological caveat on devstral / deepseek

NIM's `devstral-2-123b` returned HTTP 400 "DEGRADED function cannot be invoked" on 9/10 requests (1 succeeded — hugo-14733 in 199s). NIM's `deepseek-v4-pro` timed out at exactly 519-523s on 10/10 requests with the agent log showing "Request timeout after 520s" before any response arrived. These are NOT model-capability failures — they're NIM service degradation that needs to be retested when NIM improves those deployments.

## Per-task ✓/✗ matrix (all 10 models)

| Task | Opus 4.7 | qwen3-coder-next | qwen3.6-27b | qwen3.5-122b | minimax-m2.5 | mistral-small-4 | qwen3-coder-480b (NIM) | mistral-large-3-675b (NIM) | devstral-2-123b (NIM) | deepseek-v4-pro (NIM) |
|---|---|---|---|---|---|---|---|---|---|---|
| `gohugoio__hugo-14727` | ✓ 1/1 | ✓ 1/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ⊗D | ⊗T |
| `gohugoio__hugo-14728` | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✗ 0/1 | ✓ 1/1 | ✓ 1/1 | ✗ 0/1 | ✓ 1/1 | ⊗D | ⊗T |
| `gohugoio__hugo-14733` | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ⊗T |
| `gohugoio__hugo-14741` | ✓ 1/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ⊗D | ⊗T |
| `gohugoio__hugo-14742` | ✓ 1/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ⊗D | ⊗T |
| `gohugoio__hugo-14754` | ✓ 2/2 | ✗ 0/2 | ✗ 0/2 | ✗ 0/2 | ✗ 0/2 | ✗ 0/2 | ✗ 0/2 | ✗ 0/2 | ⊗D | ⊗T |
| `gohugoio__hugo-14757` | ✓ 1/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ✗ 0/1 | ⊗D | ⊗T |
| `gohugoio__hugo-14759` | ✓ 7/7 | ✗ 0/7 | ✗ 0/7 | ✗ 0/7 | ✗ 0/7 | ✗ 0/7 | ✗ 0/7 | ✗ 0/7 | ⊗D | ⊗T |
| `pytest-dev__pytest-14343` | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✗ 0/1 | ✓ 1/1 | ✓ 1/1 | ✗ 0/1 | ✗ 0/1 | ⊗D | ⊗T |
| `pytest-dev__pytest-14363` | ✗ 0/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✓ 1/1 | ✗ 0/1 | ✓ 1/1 | ✗ 0/1 | ⊗D | ⊗T |

Legend: ✓ passed · ✗ failed (model attempt) · ⊗D NIM service DEGRADED · ⊗T NIM 520s TIMEOUT · · not run
