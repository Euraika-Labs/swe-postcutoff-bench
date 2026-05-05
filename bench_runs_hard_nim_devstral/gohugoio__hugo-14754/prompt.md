The repo `gohugoio/hugo` is cloned in this workdir. Failing tests have been added to the test files.

# Issue
Add a more flexible filename identifier scheme that also allows setting roles and versions

Fixes #14750

# Task
1. `git diff HEAD` to see the new failing tests.
2. Read them — they show what behavior is expected.
3. Edit source files (NOT tests) to make them pass.
4. Verify with the project's test command if you can.

# Constraints
- Tests already exist; never duplicate them.
- Source files only — no test additions.
