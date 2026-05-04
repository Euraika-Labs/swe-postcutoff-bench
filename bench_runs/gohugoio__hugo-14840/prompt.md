You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

# Issue
security: Allow hostnames starting with digits in default http.urls

Domains like 1password.com and 37signals.com were blocked by the default
allow rule '^https?://[a-z]'. Allow [a-z0-9] for the first hostname char
and add an explicit deny for hosts whose first label is all-digit (IP
literals like 127.0.0.1) to retain the prior SSRF protections.

Fixes #14837

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
