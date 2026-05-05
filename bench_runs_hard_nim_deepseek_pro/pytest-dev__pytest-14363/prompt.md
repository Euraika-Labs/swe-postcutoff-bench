You are debugging a real GitHub issue in the `pytest-dev/pytest` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
[PR #14343/95d8423b backport][9.0.x] tmpdir: fix insecure temporary directory vulnerability (CVE-2025-71176)

**This is a backport of PR #14343 as merged into main (95d8423bd24992deea5b9df32555fa1741679e2c).**

This is my proposed alternative to #13669 as discussed in the issue. I think we should go with the simple fix for now. I think this one should be safe to backport.

A previous fix for insecure temporary directory issue c49100cef8073c5de117199d17d632cfd8cb11c1 wasn't sufficient because it followed symlinks.
    
Stop following symlinks, and reject if a symlink; we know it shouldn't be.
    
Fix #14279.
    
[0] https://www.openwall.com/lists/oss-security/2026/01/21/5

# Step-by-step plan
1. **Locate**: `git diff HEAD` to see the failing tests already present.
2. **Understand**: read those tests carefully — they encode the expected behavior.
3. **Investigate**: find the source files responsible for the bug.
4. **Fix**: edit source files only.
5. **Verify**: run the test command if possible.
6. **Stop**: your final source-file edits are graded automatically.

# Hard constraints
- Failing tests are ALREADY in the repo. Do not duplicate them.
- Edit source files only. Never modify test files.
- Stay focused on the bug fix; no refactoring.
