# Opus 4.7 baseline on swe-postcutoff-bench v0.1

**Score: 17/18 = 94.4%** (pass@1, single-shot)

Run: 2026-05-04. Harness: `claude` CLI v2.1.126 (Opus default), `--dangerously-skip-permissions`, scoped to a per-task workdir cloned at `base_commit` with `test_patch` already applied + committed.

## Per-task results

| instance_id | language | F2P | wall (s) | result |
|---|---|---|---|---|
| gohugoio__hugo-14784 | go | 1/1 | 119 | ✓ |
| gohugoio__hugo-14785 | go | 1/1 | 214 | ✓ |
| gohugoio__hugo-14793 | go | 1/1 | 182 | ✓ |
| gohugoio__hugo-14794 | go | 1/1 | 117 | ✓ |
| gohugoio__hugo-14798 | go | 1/1 | 147 | ✓ |
| gohugoio__hugo-14802 | go | 1/1 | 259 | ✓ |
| gohugoio__hugo-14808 | go | 1/1 | 199 | ✓ |
| gohugoio__hugo-14826 | go | 1/1 | 172 | ✓ |
| gohugoio__hugo-14829 | go | 1/1 | 195 | ✓ |
| gohugoio__hugo-14840 | go | 1/1 | 103 | ✓ |
| pytest-dev__pytest-14382 | python | 1/1 | 165 | ✓ |
| pytest-dev__pytest-14407 | python | 0/1 | 70 | ✗ |
| pytest-dev__pytest-14418 | python | 1/1 | 367 | ✓ |
| pytest-dev__pytest-14422 | python | 1/1 | 183 | ✓ |
| spf13__cobra-2234 | go | 1/1 | 142 | ✓ |
| spf13__cobra-2238 | go | 1/1 | 170 | ✓ |
| spf13__cobra-2241 | go | 1/1 | 123 | ✓ |
| spf13__cobra-2397 | go | 4/4 | 99 | ✓ |

## Failure analysis

The single failure is **`pytest-dev__pytest-14407`**: Opus described the correct fix in its response — extending the `--version` early-exit to also count `-V` — but `agent.diff` came back empty. Opus appears to have either thought the fix was already applied, or its Edit tool failed silently. With a stricter "verify your edits landed on disk" prompt this is plausibly recoverable, but as a clean single-shot test it counts as a miss.

The 2 earlier "cobra" failures (in the first run) were **harness bugs**, not Opus misses:
- A relative-path bug caused `test_patch` to silently fail to apply, so Opus saw a workdir without the failing tests and recreated them with the same names → "redeclared in this block" compile errors.
- Fixed by absolutising paths and committing the `test_patch` as a checkpoint, so `agent.diff` captures only Opus's source-file changes.

## What this tells us about the benchmark

A frontier model getting 94% means **v0.1 is too easy as a stress test for Opus.** It does, however, work as:

1. A **regression detection** test for harness builds and runner correctness.
2. A **stratification test** for smaller / non-frontier models — the 70-120B and ≤30B tiers will land far below 94%, giving meaningful difficulty signal.
3. A **contamination control**: 15 of 18 tasks merged after Opus's Jan-2026 cutoff, so memorization can't explain Opus's 94%.

For v0.2 we should curate **harder LH tasks** (≥3 files touched, ≥100 patch lines, security/concurrency/type-correctness categories) where Opus + good harness drops to 50-65%. That's the band where harness × model effects become visible.

## How to reproduce

```bash
cd swe-postcutoff-bench
PCB_OPUS_PARALLEL=3 bash scripts/run_opus_all.sh
# results land in bench_runs/<instance_id>/
```
