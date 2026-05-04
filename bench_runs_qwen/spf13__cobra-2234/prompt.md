You are debugging a real GitHub issue in the `spf13/cobra` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

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
