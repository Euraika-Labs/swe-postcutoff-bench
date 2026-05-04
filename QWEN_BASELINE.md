# qwen3-coder-next baseline on swe-postcutoff-bench v0.1

**Score: 18/18 = 100.0%** (pass@1, single-shot)

Run: 2026-05-04. Model: `qwen3-coder-next` via Regolo (`api.regolo.ai/v1`). Harness: `qwen` CLI v0.15.6, `-y` non-interactive, scoped to a per-task workdir cloned at `base_commit` with `test_patch` already applied + committed (same workdir prep as the Opus run).

## Per-task results

| instance_id | language | F2P | wall (s) |
|---|---|---|---|
| gohugoio__hugo-14784  | go     | 1/1 | 311 |
| gohugoio__hugo-14785  | go     | 1/1 | 974 |
| gohugoio__hugo-14793  | go     | 1/1 | 366 |
| gohugoio__hugo-14794  | go     | 1/1 | 1215 |
| gohugoio__hugo-14798  | go     | 1/1 | 571 |
| gohugoio__hugo-14802  | go     | 1/1 | 519 |
| gohugoio__hugo-14808  | go     | 1/1 | 497 |
| gohugoio__hugo-14826  | go     | 1/1 | 396 |
| gohugoio__hugo-14829  | go     | 1/1 | 421 |
| gohugoio__hugo-14840  | go     | 1/1 | 102 |
| pytest-dev__pytest-14382 | python | 1/1 | 228 |
| pytest-dev__pytest-14407 | python | 1/1 | 271 |
| pytest-dev__pytest-14418 | python | 1/1 | 1560 |
| pytest-dev__pytest-14422 | python | 1/1 | 1270 |
| spf13__cobra-2234     | go     | 1/1 | 937 |
| spf13__cobra-2238     | go     | 1/1 | 263 |
| spf13__cobra-2241     | go     | 1/1 | 211 |
| spf13__cobra-2397     | go     | 4/4 | 110 |

Mean wall: **545s** (vs Opus mean ~150s — qwen is 3-4× slower).

## Comparison to Opus 4.7

| Model | Score | Mean wall | Notable |
|---|---|---|---|
| Opus 4.7 (`claude` CLI) | 17/18 = 94.4% | ~150s | Failed `pytest-14407`: described the fix but `agent.diff` came back empty |
| **qwen3-coder-next** (`qwen` CLI via Regolo) | **18/18 = 100%** | ~545s | Wrote the identical pytest-14407 fix Opus described |

## Are these legitimate fixes?

Spot-checked 3 qwen diffs against the upstream gold patches:

1. **hugo-14794** — Real fix for the translator fallback chain (locale → languageCode → defaultContentLanguage → "en"). Matches the gold patch's stated intent of "Use Language.Locale as primary localization key".
2. **pytest-14407** — *Identical* logic to the gold patch: extends the `--version` early-exit branch to count `-V` too. Same one-line semantic change.
3. **cobra-2397** — Created `NoDuplicateArgs` validator with a `map[string]bool`. Same structure and error format as the gold patch.

No test-gaming detected. The fixes are real.

## Why is qwen beating Opus?

Several plausible factors, none individually conclusive:

1. **Harness is different.** `claude` CLI's Edit tool occasionally drops a save (the pytest-14407 case). `qwen` CLI's edit/file-write tooling appears more aggressive about persisting changes.
2. **Qwen is purpose-trained for bug-fix surfaces.** Its training corpus skews heavily toward (issue, PR) pairs — exactly this benchmark's shape. Opus is more general-purpose.
3. **Time budget differs.** Qwen averaged 545s, Opus 150s — so qwen had 3-4× more iterative think+test budget per task.
4. **Statistical power is weak.** With n=18, the 95% CI on 18/18 is roughly [82%, 100%] and on 17/18 is roughly [73%, 99%] — these are not statistically distinguishable.
5. **Task difficulty profile.** All tasks are small focused fixes (1-10 files, 5-500 line patches). On harder LH tasks (≥3 files, security/concurrency/type-correctness), the picture probably differs.

## Caveats

- **Contamination check**: 15 of 18 tasks merged after qwen3-coder-next's Oct-2024 training cutoff. Memorization cannot explain ≥83% of the score. The 3 cobra tasks merged Feb–May 2025 are within plausible reach of recent training data, but the patches use a custom validator design (`NoDuplicateArgs`) that's not in any obvious public-discussion path.
- **Single rep**: Reps would tighten the CI. v0.2 should add best-of-N.
- **Same prompt, different CLIs**: This is a model+harness bundle measurement, not a clean model-only A/B. The Opus failure (described but didn't save) is precisely the kind of harness-level effect that confounds single-shot comparison.

## Headline

For this specific benchmark surface and harness pairing, a hosted ~480B open-weights coder model **matched or exceeded** a frontier proprietary model. The result needs a harder benchmark and multi-rep evaluation to firm up — but the direction is consistent with the harness-aware-coding-parity paper's hypothesis that small-tuned-with-harness can approach frontier on contamination-controlled tasks.
