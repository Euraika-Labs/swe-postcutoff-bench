You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
Fix auto-creation of root sections in multilingual sites

Fixes #14681

Co-authored-by: Joe Mooring <joe@mooring.com>

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
