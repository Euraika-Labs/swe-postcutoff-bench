You are debugging a real GitHub issue in the `spf13/cobra` repository. The repo has been cloned for you and the failing tests are already present.

# Issue
fix CompletionFunc implementation

- **chore: add missing non-regression test for completions**
- **fix: completion helper retro-compatibility**

This PR is about this
- Fixes code implemented in https://github.com/spf13/cobra/pull/2220
- discussion that occurred here https://github.com/spf13/cobra/pull/2231#issuecomment-2661510587
- breaking changes reported here: https://github.com/docker/cli/pull/5827
- possible fix tried on docker-cli: https://github.com/docker/cli/issues/5828

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
