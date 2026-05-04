You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and **the failing tests are already added to the test files**.

# Issue
config/security: Add "! " negation to Whitelist, harden default http.urls

Whitelist now treats any pattern prefixed with "! " (the same negation
prefix used by hglob/predicate) as a deny rule. Deny matches take
precedence over allow, and a whitelist made up exclusively of deny
rules implicitly allows everything it does not deny.

The default security.http.urls now reads:

    urls = ['^https?://[a-z]', '! (?i)localhost', '! @']

i.e. allow URLs whose host starts with a letter (the common
"https://example.com/" shape), deny anything that looks like localhost,
and deny URLs with userinfo to foil "http://user@127.0.0.1/" bypasses.
Public IP literals are collateral blocks; users who need them (or their
own private hosts) override security.http.urls as before, mixing allow
and deny rules with the same "! " prefix, e.g.

    [security.http]
    urls = ['.*', '! ^https?://evil\.example\.com']

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
