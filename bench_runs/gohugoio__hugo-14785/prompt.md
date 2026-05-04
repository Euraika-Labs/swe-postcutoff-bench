You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

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
1. Read the failing test(s) in this repo to understand what's expected.
2. Investigate the relevant source files.
3. Fix the bug by editing source files (NOT the tests — they're already correct).
4. Run the test suite locally if possible to confirm your fix.
5. When you are done, just stop — your final source-file edits are graded by an automated runner.

Constraints:
- You may freely read, write, and execute commands in the workdir.
- Do not modify the existing tests; only fix the source code.
- Stay focused: fix only what the issue describes; no refactors or unrelated changes.
