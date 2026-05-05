You are debugging a real GitHub issue in the `pytest-dev/pytest` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
tmpdir: fix insecure temporary directory vulnerability (CVE-2025-71176)

This is my proposed alternative to #13669 as discussed in the issue. I think we should go with the simple fix for now. I think this one should be safe to backport.

A previous fix for insecure temporary directory issue c49100cef8073c5de117199d17d632cfd8cb11c1 wasn't sufficient because it followed symlinks.
    
Stop following symlinks, and reject if a symlink; we know it shouldn't be.
    
Fix #14279.
    
[0] https://www.openwall.com/lists/oss-security/2026/01/21/5

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
