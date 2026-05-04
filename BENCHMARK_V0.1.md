# swe-postcutoff-bench v0.1

Auto-curated, end-to-end-verified post-Oct-2024 bug-fix tasks.
Runs in seconds-to-minutes per task on a fast machine.

## Status

| Language   | Verified | Pending (need infra) |
|------------|----------|----------------------|
| Go         | 14       | 1                    |
| Python     | 4        | 6 (Django, full pytest tasks needing test extras) |
| TypeScript | 0        | 15 (Vite/Prisma monorepo build) |
| **Total**  | **18**   | **22**               |

## Verified tasks (18) — ready for grading

The runner (`scripts/run_task.py`) clones the repo at `base_commit`, applies
`test_patch`, then applies the candidate patch, then runs `runner.test_cmd`,
parses the output for `FAIL_TO_PASS`/`PASS_TO_PASS` test results, and writes
`grade.json`. We verified end-to-end by running the gold patch:

| instance_id | language | F2P | secs (gold) |
|---|---|---|---|
| gohugoio__hugo-14784 | go | 1/1 | 18 |
| gohugoio__hugo-14785 | go | 1/1 | 25 |
| gohugoio__hugo-14793 | go | 1/1 | 13 |
| gohugoio__hugo-14794 | go | 1/1 | 19 |
| gohugoio__hugo-14798 | go | 1/1 | 35 |
| gohugoio__hugo-14802 | go | 1/1 | 33 |
| gohugoio__hugo-14808 | go | 1/1 | 32 |
| gohugoio__hugo-14826 | go | 1/1 | 12 |
| gohugoio__hugo-14829 | go | 1/1 | 25 |
| gohugoio__hugo-14840 | go | 1/1 | 13 |
| pytest-dev__pytest-14382 | python | 1/1 | 9 |
| pytest-dev__pytest-14407 | python | 1/1 | 10 |
| pytest-dev__pytest-14418 | python | 1/1 | 10 |
| pytest-dev__pytest-14422 | python | 1/1 | 10 |
| spf13__cobra-2234 | go | 1/1 | 3 |
| spf13__cobra-2238 | go | 1/1 | 2 |
| spf13__cobra-2241 | go | 1/1 | 1 |
| spf13__cobra-2397 | go | 4/4 | 2 |

## Pending tasks (need extra infra)

- **Vite tasks (3)**: monorepo `pnpm build` step required before `pnpm test`.
  Add `runner.pre_test_cmd: "pnpm build"` and re-verify.
- **Prisma tasks (4)**: similar — Nx-based monorepo with `pnpm prisma generate`
  step before tests. Per-package `pnpm --filter <pkg> test`.
- **Django tasks (3)**: `pip install -e .` succeeds but the canonical
  test runner is `python -m django test` not `pytest`. Custom runner needed.
- **Misc (2)**: `hugo-14813` parses 3/5 subtests (Go subtest naming with
  spaces); `cobra-2356` 1/2 (single subtest miscount); both just need
  refined parsing.
- **`tasks_pending/` (15)**: tasks with empty `FAIL_TO_PASS` from the
  heuristic test extractor — these need a strict run-mode verifier.

## How to run on a candidate solution

```bash
# The candidate produces a unified diff (e.g. an LLM agent's submission)
python3 scripts/run_task.py \
  --task-file tasks/spf13__cobra-2234.json \
  --patch /path/to/candidate.diff \
  --out grades/spf13__cobra-2234__candidate.json
```

The grader returns `passed: true` only when **all** `FAIL_TO_PASS` tests
pass and **all** `PASS_TO_PASS` tests still pass.

## Running the matrix on this benchmark

Combine with the harness × model matrix from
`research/papers/2026-04-coding-parity-small-tuned/experiments/tier2_smoke/HARNESS_MATRIX.md`:

- Pick a (harness, model) cell that's `working`.
- Run the harness on each verified task (it produces a `patch.diff`).
- Grade with `run_task.py --patch <patch>`.
- Aggregate pass@1 / best-of-N as the cell's score.
