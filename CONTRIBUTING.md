# Contributing tasks

We welcome PRs adding tasks. The bar is methodological rigor — see [SCHEMA.md](./SCHEMA.md) for the format.

## Quick start: curate one task

1. Find a closed bug-fix PR in a target repo, filed after 2024-10-31:
   ```
   gh search prs "repo:django/django created:>2024-10-31 is:merged label:bug" \
     --json number,title,createdAt,mergeCommit | head -20
   ```

2. From the PR, extract:
   - `base_commit` — parent of the merge commit
   - `patch` — the diff of source files in the PR
   - `test_patch` — the diff of test files in the PR
   - `FAIL_TO_PASS` — tests added/modified in `test_patch` that the issue says should fail
   - `PASS_TO_PASS` — random sample of 5-50 existing passing tests in the affected modules

3. Verify locally:
   ```bash
   git clone <repo>
   git checkout <base_commit>
   <runner.install>           # e.g. pip install -e .[test]
   <runner.test_cmd> <FAIL_TO_PASS>   # → should FAIL
   git apply patch.diff
   <runner.test_cmd> <FAIL_TO_PASS>   # → should PASS
   <runner.test_cmd> <PASS_TO_PASS>   # → should PASS
   ```

4. Save as `tasks/<instance_id>.json`, save the verification log as `tasks/<instance_id>.verify.txt`, open a PR.

## Curation tooling (auto-curator)

`scripts/curate.py` semi-automates step 1-2 for repos with conventional `bug` labels and `Closes #N` PR descriptions:

```bash
scripts/curate.py --repo django/django --since 2024-11-01 --max 30 \
  --output tasks/
```

Manual review still required before submission — the script proposes tasks, doesn't accept them.

## Task quality bar

Reject if:

- Issue is not a bug (feature request, refactor, doc-only)
- Fix is trivial (1-line typo) — these are not interesting agentic-coding signal
- Fix touches > 10 files (likely a refactor sprawl, not a focused bug fix)
- Tests added by the fix PR aren't deterministic (flaky, network-dependent, time-dependent)
- Issue describes the fix in technical detail (gives the agent the answer)
- Multiple reasonable correct fixes exist without canonical test coverage

Aim for the median: 30-300 line patches across 1-3 files, with clearly-failing tests that pass after a focused fix. This matches SWE-bench Verified's distribution.
