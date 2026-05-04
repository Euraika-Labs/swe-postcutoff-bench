You are debugging a real GitHub issue in the `pytest-dev/pytest` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
Fix duplicate values in Config.known_args_namespace for append actions

Ran into #13484 while looking at the config parsing code. The third `parse_known_args` call passes `self.known_args_namespace` as the namespace, which already has values from the second parse. For `action="append"` options like `-W`, this causes duplicates.

Fix is to use `copy.copy(self.option)` instead, same as the first two calls. This way each parse starts from a clean namespace and `append` actions don't accumulate across multiple parses.

Not sure if there was a reason the third call used `known_args_namespace` directly, but from what I can tell the only new things after the second parse are plugin-registered options, and those would still be picked up correctly with a fresh namespace.

Closes #13484

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
