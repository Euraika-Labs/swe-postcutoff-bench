The repo `gohugoio/hugo` is cloned in this workdir. Failing tests have been added to the test files.

# Issue
Fix panic when passthrough elements are used in headings

Fixes #14677

Co-Authored-By: bep <bjorn.erik.pedersen@gmail.com>
Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>

# Task
1. `git diff HEAD` to see the new failing tests.
2. Read them — they show what behavior is expected.
3. Edit source files (NOT tests) to make them pass.
4. Verify with the project's test command if you can.

# Constraints
- Tests already exist; never duplicate them.
- Source files only — no test additions.
