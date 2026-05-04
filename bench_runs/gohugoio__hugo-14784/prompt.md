You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

# Issue
modules: Ignore non-require blocks in go.mod rewrite

The Go 1.24 tool directive uses single-token entries inside a
tool ( ... ) block. The previous splitter treated any tab-indented
line as a require entry, causing an index out of range panic when
running hugo mod tidy on a module with a tool block.

Track the require block state explicitly so other blocks (tool,
replace, exclude, retract) are left untouched.

Fixes #14783

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
