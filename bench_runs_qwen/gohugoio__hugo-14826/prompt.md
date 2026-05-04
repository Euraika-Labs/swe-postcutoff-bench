You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
config/security: Adjust Node permissions after user feedback

The previous "! @" deny rule rejected any URL containing "@",
including legitimate version-pinned imports such as
https://cdn.jsdelivr.net/npm/mermaid@latest/dist/mermaid.esm.min.mjs.
Tighten it to "! (?i)^https?://[^/?#]*@" so only "@" inside the
authority section (i.e. real userinfo) is blocked.

Fixes #14825

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
