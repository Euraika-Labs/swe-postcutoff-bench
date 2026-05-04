You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

# Issue
resources: Honor Retry-After header in resources.GetRemote retries

When the server returns a temporary HTTP error (e.g. 429 or 503)
together with a Retry-After header, use that value as the next sleep
duration instead of the default exponential backoff. The Retry-After
value is also surfaced in the retry-timeout error message.

Fixes #14828

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
