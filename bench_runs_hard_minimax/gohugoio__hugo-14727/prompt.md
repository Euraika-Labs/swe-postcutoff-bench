You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
Fix auto-creation of root sections in multilingual sites

Fixes #14681

Co-authored-by: Joe Mooring <joe@mooring.com>

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
