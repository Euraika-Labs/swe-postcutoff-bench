You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
Fix panic when passthrough elements are used in headings

Fixes #14677

Co-Authored-By: bep <bjorn.erik.pedersen@gmail.com>
Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>

# Your task
1. **First**: `git diff HEAD` to see the failing tests already present.
2. Read those tests to understand what behavior is expected.
3. Investigate the relevant source files (NOT test files).
4. Fix the bug by editing source files only.
5. Run the test suite locally to confirm.
6. Stop — your final source-file edits are graded by an automated runner.

# Hard constraints
- Failing tests are ALREADY in the repo. Do not re-add them — that causes "redeclared in this block" errors.
- Edit source files only. Never modify, add to, or duplicate test files.
- Stay focused on the bug fix.
