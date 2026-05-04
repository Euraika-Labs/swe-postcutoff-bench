You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

# Issue
langs/i18n: Improve default content language fallback

The fallback order for translations is now:

1. Current language's locale (e.g., `pt-BR` => `pt-br.toml`)
2. Current language's key (e.g., `pt` =>  `pt.toml`)
3. Default language's locale (e.g., `es-AR` =>  `es-ar.toml`) <-- this is new
4. Default language's key (e.g., `es` =>  `es.toml`)

Closes #14243

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
