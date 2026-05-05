The repo `gohugoio/hugo` is cloned in this workdir. Failing tests have been added to the test files.

# Issue
Fix panic on edit of legacy mapped template names that's also a valid path in the new setup

This mapping was added in Hugo `v0.146.0`.

Fixes #14740

# Task
1. `git diff HEAD` to see the new failing tests.
2. Read them — they show what behavior is expected.
3. Edit source files (NOT tests) to make them pass.
4. Verify with the project's test command if you can.

# Constraints
- Tests already exist; never duplicate them.
- Source files only — no test additions.
