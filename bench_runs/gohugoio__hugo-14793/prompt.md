You are debugging a real GitHub issue in the `gohugoio/hugo` repository. The repo has been cloned for you and the failing tests are already present.

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
1. Read the failing test(s) in this repo to understand what's expected.
2. Investigate the relevant source files.
3. Fix the bug by editing source files (NOT the tests — they're already correct).
4. Run the test suite locally if possible to confirm your fix.
5. When you are done, just stop — your final source-file edits are graded by an automated runner.

Constraints:
- You may freely read, write, and execute commands in the workdir.
- Do not modify the existing tests; only fix the source code.
- Stay focused: fix only what the issue describes; no refactors or unrelated changes.
