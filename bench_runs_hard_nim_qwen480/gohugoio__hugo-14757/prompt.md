The repo `gohugoio/hugo` is cloned in this workdir. Failing tests have been added to the test files.

# Issue
Fix filename dimension identifiers (_role_X_, _version_X_) to replace mount config

Filename identifiers for roles and versions were parsed but never applied
to the SitesMatrix. Now they replace the mount's configuration for that
dimension, matching how language identifiers already worked.

Fixes #14756

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>

# Task
1. `git diff HEAD` to see the new failing tests.
2. Read them — they show what behavior is expected.
3. Edit source files (NOT tests) to make them pass.
4. Verify with the project's test command if you can.

# Constraints
- Tests already exist; never duplicate them.
- Source files only — no test additions.
