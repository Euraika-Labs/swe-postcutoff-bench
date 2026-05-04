You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
tpl/collections: Honor the Eqer interface in where comparisons

The where function previously fell through to a no-op when comparing
two values whose kinds were not handled by the primitive type switches
(e.g. two Page interface values). This made `where pages "Parent" $page`
return an empty list, while the equivalent `range pages` + `if eq` worked.

Use compare.Eqer for equality operators when either side implements it,
matching the behavior of the eq/ne template funcs.

Fixes #14777

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>

# Your task
1. **First**: `git diff HEAD` in the workdir to see what tests are already present. They are the FAIL_TO_PASS tests you need to make pass — do NOT re-create them.
2. Read those tests to understand what behavior is expected.
3. Investigate the relevant source files (NOT test files).
4. Fix the bug by editing source files only.
5. Run the test suite locally to confirm your fix.
6. Stop — your final source-file edits are graded by an automated runner.

# Hard constraints
- The failing tests are ALREADY in the repo. Do not add tests with the same name — that causes "redeclared in this block" or "duplicate test" errors.
- Edit source files only. Never edit, add to, or duplicate test files.
- Stay focused: fix only what the issue describes; no refactors or unrelated changes.
