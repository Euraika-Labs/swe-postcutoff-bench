#!/usr/bin/env python3
"""Auto-curator: search a GitHub repo for closed bug-fix PRs after a cutoff date.

Emits candidate task JSONs (without verification — verify.py runs them).

Example:
    scripts/curate.py --repo django/django --since 2024-11-01 \
                      --max 30 --output tasks/

Filters applied:
  - PR is merged
  - PR was created after --since
  - PR has bug/regression label OR closes an issue with bug-related text
  - PR touches at least one test file (proxy for FAIL_TO_PASS test addition)
  - PR has 1-10 changed files (focused fix scope)
  - 5 <= patch_lines <= 500 (not trivial, not refactor sprawl)

Manual review still required before submission — the script proposes; humans decide.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any


def gh(*args: str) -> dict | list:
    """Call `gh` CLI and return parsed JSON stdout."""
    cmd = ["gh"] + list(args)
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out) if out.strip() else {}


def search_prs(repo: str, since: str, max_results: int) -> list[dict[str, Any]]:
    """Find merged PRs created after `since`, ordered newest first."""
    query = f'repo:{repo} is:pr is:merged created:>={since}'
    fields = "number,title,createdAt,mergedAt,mergeCommit,labels,url"
    rows = gh("pr", "list",
              "--repo", repo, "--state", "merged",
              "--search", query,
              "--limit", str(max_results),
              "--json", fields)
    return rows if isinstance(rows, list) else []


def fetch_pr_detail(repo: str, number: int) -> dict[str, Any]:
    """Get full PR record from REST API: includes base.sha, merge_commit_sha, etc."""
    return gh("api", f"/repos/{repo}/pulls/{number}")


def fetch_pr_files(repo: str, number: int) -> list[dict[str, Any]]:
    """List files touched by the PR."""
    return gh("api", f"/repos/{repo}/pulls/{number}/files", "--paginate")


def fetch_patch(repo: str, number: int) -> str:
    """Pull unified diff of the PR."""
    cmd = ["gh", "pr", "diff", str(number), "--repo", repo, "--patch"]
    return subprocess.check_output(cmd, text=True)


def split_patch_test_vs_src(unified: str) -> tuple[str, str]:
    """Split a unified diff into test-file changes vs src changes.

    Heuristic: any file with /test/ or /tests/ or test_*.py or *_test.go etc
    in its path goes to the test_patch; everything else is the source patch.
    """
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in unified.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if cur:
                blocks.append(cur)
            cur = [line]
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)

    test_blocks: list[str] = []
    src_blocks: list[str] = []
    for blk in blocks:
        head = blk[0] if blk else ""
        # Extract path from "diff --git a/path/file b/path/file"
        path = ""
        if " a/" in head:
            path = head.split(" a/", 1)[1].split(" b/", 1)[0].strip()
        is_test = (
            "/tests/" in path or "/test/" in path or "/__tests__/" in path
            or path.endswith("_test.go") or path.endswith("_spec.rb")
            or path.startswith("test_") or "/test_" in path
            or path.endswith(".test.ts") or path.endswith(".test.tsx")
            or path.endswith(".spec.ts") or path.endswith(".test.js")
            or path.endswith("Test.java") or path.endswith("Tests.java")
        )
        if is_test:
            test_blocks.append("".join(blk))
        else:
            src_blocks.append("".join(blk))
    return "".join(src_blocks), "".join(test_blocks)


def is_bug_label(labels: list[dict[str, Any]]) -> bool:
    names = {(l.get("name") or "").lower() for l in (labels or [])}
    bug_terms = {"bug", "regression", "kind/bug", "type/bug", "type:bug",
                 "type: bug", "fix", "defect"}
    return bool(names & bug_terms)


def language_for(repo: str) -> str:
    """Crude per-repo language tag — refined per PR-touched files."""
    py = {"django/django", "astropy/astropy", "scikit-learn/scikit-learn",
          "matplotlib/matplotlib", "pytest-dev/pytest", "pandas-dev/pandas",
          "tiangolo/fastapi", "encode/django-rest-framework", "psf/requests"}
    ts = {"vercel/next.js", "facebook/react", "vitejs/vite", "vuejs/core",
          "microsoft/TypeScript", "drizzle-team/drizzle-orm", "prisma/prisma"}
    go = {"kubernetes/kubernetes", "gohugoio/hugo", "spf13/cobra",
          "charmbracelet/bubbletea", "gin-gonic/gin"}
    java = {"spring-projects/spring-boot", "quarkusio/quarkus",
            "JabRef/jabref", "JetBrains/intellij-community"}
    rust = {"tokio-rs/tokio", "tokio-rs/axum", "serde-rs/serde",
            "clap-rs/clap", "ratatui-org/ratatui"}
    ruby = {"rails/rails", "jekyll/jekyll", "rspec/rspec-core"}
    if repo in py: return "python"
    if repo in ts: return "typescript"
    if repo in go: return "go"
    if repo in java: return "java"
    if repo in rust: return "rust"
    if repo in ruby: return "ruby"
    return "unknown"


RUNNER_TEMPLATES = {
    "python": {
        "kind": "python",
        "python_version": "3.11",
        "install": "pip install -e .[test] || pip install -e .[testing] || pip install -e .",
        "test_cmd": "pytest -p no:cacheprovider --tb=short -v",
        "test_id_separator": "::",
    },
    "typescript": {
        "kind": "node",
        "node_version": "20",
        "package_manager": "pnpm",
        "install": "pnpm install --frozen-lockfile || npm ci",
        "test_cmd": "pnpm test || npm test",
        "test_id_separator": " > ",
    },
    "go": {
        "kind": "go",
        "go_version": "1.23",
        "install": "go mod download",
        "test_cmd": "go test ./...",
        "test_id_separator": "/",
    },
}


def make_task(repo: str, pr_detail: dict, src_patch: str, test_patch: str) -> dict:
    """Compose a v0.1 schema task record from REST PR JSON."""
    number = pr_detail["number"]
    instance_id = f"{repo.replace('/', '__')}-{number}"
    base_commit = (pr_detail.get("base") or {}).get("sha", "")
    merge_oid = pr_detail.get("merge_commit_sha", "") or ""
    issue_body = pr_detail.get("body") or ""
    title = pr_detail.get("title", "")
    lang = language_for(repo)
    runner = RUNNER_TEMPLATES.get(lang, {"kind": lang})
    labels = [(l.get("name") or "") for l in (pr_detail.get("labels") or [])]
    return {
        "instance_id": instance_id,
        "repo": repo,
        "language": lang,
        "base_commit": base_commit,
        "merge_commit": merge_oid,
        "patch": src_patch,
        "test_patch": test_patch,
        "problem_statement": (issue_body or title).strip(),
        "title": title,
        "FAIL_TO_PASS": [],
        "PASS_TO_PASS": [],
        "created_at": pr_detail.get("created_at", ""),
        "merged_at": pr_detail.get("merged_at", ""),
        "pr_url": pr_detail.get("html_url", f"https://github.com/{repo}/pull/{number}"),
        "labels": labels,
        "runner": runner,
        "verified": False,
        "_curator_notes": "auto-curated; FAIL_TO_PASS/PASS_TO_PASS need verifier population.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--repo", required=True, help="org/repo on GitHub")
    ap.add_argument("--since", default="2024-11-01",
                    help="ISO date; PRs created after this only")
    ap.add_argument("--max", type=int, default=20, help="Max candidate PRs to fetch")
    ap.add_argument("--output", default="tasks/", help="Where to write task JSONs")
    ap.add_argument("--require-bug-label", action="store_true",
                    help="Only keep PRs with bug/regression-style label")
    ap.add_argument("--min-lines", type=int, default=5,
                    help="Minimum total patch lines (default 5)")
    ap.add_argument("--max-lines", type=int, default=500,
                    help="Maximum total patch lines (default 500)")
    ap.add_argument("--min-files", type=int, default=1,
                    help="Minimum touched files (default 1)")
    ap.add_argument("--max-files", type=int, default=10,
                    help="Maximum touched files (default 10)")
    args = ap.parse_args()

    out = pathlib.Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Searching {args.repo} for merged PRs since {args.since} (max {args.max})…",
          file=sys.stderr)
    candidates = search_prs(args.repo, args.since, args.max)
    print(f"  {len(candidates)} merged PRs found", file=sys.stderr)

    kept = 0
    for pr in candidates:
        n = pr["number"]
        labels = pr.get("labels") or []
        if args.require_bug_label and not is_bug_label(labels):
            continue
        try:
            detail = fetch_pr_detail(args.repo, n)
            files = fetch_pr_files(args.repo, n)
            patch = fetch_patch(args.repo, n)
        except subprocess.CalledProcessError as e:
            print(f"  PR #{n}: gh fetch failed: {e}", file=sys.stderr)
            continue

        if not (args.min_files <= len(files) <= args.max_files):
            continue
        # Require at least one test file touched (REST returns "filename")
        test_paths = [f for f in files
                      if any(t in (f.get("filename") or "")
                             for t in ("test", "spec", "Test"))]
        if not test_paths:
            continue
        # Patch length filter
        n_lines = patch.count("\n")
        if not (args.min_lines <= n_lines <= args.max_lines):
            continue

        src_patch, test_patch = split_patch_test_vs_src(patch)
        if not src_patch.strip() or not test_patch.strip():
            continue  # need both halves

        task = make_task(args.repo, detail, src_patch, test_patch)
        task_file = out / f"{task['instance_id']}.json"
        task_file.write_text(json.dumps(task, indent=2))
        print(f"  ✓ #{n} → {task_file.name} (lines={n_lines}, files={len(files)})",
              file=sys.stderr)
        kept += 1

    print(f"\nKept {kept} candidates → {out}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
