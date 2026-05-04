You are debugging a real GitHub issue in the `pytest-dev/pytest` repository. The repo has been cloned for you and the failing tests are already present.

# Issue
Fix duplicate values in Config.known_args_namespace for append actions

Ran into #13484 while looking at the config parsing code. The third `parse_known_args` call passes `self.known_args_namespace` as the namespace, which already has values from the second parse. For `action="append"` options like `-W`, this causes duplicates.

Fix is to use `copy.copy(self.option)` instead, same as the first two calls. This way each parse starts from a clean namespace and `append` actions don't accumulate across multiple parses.

Not sure if there was a reason the third call used `known_args_namespace` directly, but from what I can tell the only new things after the second parse are plugin-registered options, and those would still be picked up correctly with a fresh namespace.

Closes #13484

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
