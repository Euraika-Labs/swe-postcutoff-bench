The repo `pytest-dev/pytest` is cloned in this workdir. Failing tests have been added to the test files.

# Issue
[PR #14343/95d8423b backport][9.0.x] tmpdir: fix insecure temporary directory vulnerability (CVE-2025-71176)

**This is a backport of PR #14343 as merged into main (95d8423bd24992deea5b9df32555fa1741679e2c).**

This is my proposed alternative to #13669 as discussed in the issue. I think we should go with the simple fix for now. I think this one should be safe to backport.

A previous fix for insecure temporary directory issue c49100cef8073c5de117199d17d632cfd8cb11c1 wasn't sufficient because it followed symlinks.
    
Stop following symlinks, and reject if a symlink; we know it shouldn't be.
    
Fix #14279.
    
[0] https://www.openwall.com/lists/oss-security/2026/01/21/5

# Task
1. `git diff HEAD` to see the new failing tests.
2. Read them — they show what behavior is expected.
3. Edit source files (NOT tests) to make them pass.
4. Verify with the project's test command if you can.

# Constraints
- Tests already exist; never duplicate them.
- Source files only — no test additions.
