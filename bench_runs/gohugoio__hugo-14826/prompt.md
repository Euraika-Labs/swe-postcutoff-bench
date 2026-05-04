You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

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
1. Read the failing test(s) in this repo to understand what's expected.
2. Investigate the relevant source files.
3. Fix the bug by editing source files (NOT the tests — they're already correct).
4. Run the test suite locally if possible to confirm your fix.
5. When you are done, just stop — your final source-file edits are graded by an automated runner.

Constraints:
- You may freely read, write, and execute commands in the workdir.
- Do not modify the existing tests; only fix the source code.
- Stay focused: fix only what the issue describes; no refactors or unrelated changes.
