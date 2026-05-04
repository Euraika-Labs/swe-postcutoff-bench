#!/usr/bin/env python3
"""Verifier: extract FAIL_TO_PASS test IDs from test_patch and (optionally)
run the test suite at base_commit and base_commit+patch to confirm pre/post
behaviour.

Heuristic FAIL_TO_PASS extraction (lightweight mode, default):
  Parse the test_patch unified diff for newly-added test functions/methods
  and emit them in the language's native test-id format.

Strict mode (--run, optional):
  Clone repo at base_commit, apply only test_patch, run test_cmd: tests added
  in test_patch should FAIL. Then apply patch on top: those tests should PASS.
  Tasks that satisfy this round-trip are marked verified=true.

Strict mode requires the project's runtime: pytest+conda for Python,
node+pnpm/npm for TS, go for Go. We do NOT do auto-Docker — keep operator
in the loop.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import Iterable

PYTHON_TEST_DEF = re.compile(r"^\+\s*def\s+(test_[A-Za-z0-9_]+)\s*\(")
PYTHON_CLASS_DEF = re.compile(r"^\+\s*class\s+(Test[A-Za-z0-9_]+)\s*[:(]")
GO_TEST_DEF = re.compile(r"^\+\s*func\s+(Test[A-Za-z0-9_]+)\s*\(")
TS_TEST_DEF = re.compile(
    r"^\+\s*(?:it|test|describe)\s*\(\s*['\"`]([^'\"`]+)['\"`]"
)


def extract_fail_to_pass(language: str, test_patch: str) -> list[str]:
    """Return language-native test IDs added in test_patch.

    For Python: `path/to/test_x.py::TestClass::test_name` (best-effort)
    For Go:     `path/to/pkg/TestName`
    For TS:     `path/to/file.test.ts > <describe...> > test name`
    """
    out: list[str] = []
    cur_file: str = ""
    cur_class: str = ""
    for line in test_patch.splitlines():
        if line.startswith("diff --git a/"):
            # Reset class scope per file
            cur_class = ""
            try:
                cur_file = line.split(" a/", 1)[1].split(" b/", 1)[0]
            except IndexError:
                cur_file = ""
            continue
        if line.startswith("+++"):
            continue
        if language == "python":
            m = PYTHON_CLASS_DEF.match(line)
            if m:
                cur_class = m.group(1)
                continue
            m = PYTHON_TEST_DEF.match(line)
            if m and cur_file:
                tid = f"{cur_file}::{cur_class}::{m.group(1)}" if cur_class \
                       else f"{cur_file}::{m.group(1)}"
                out.append(tid)
        elif language == "go":
            m = GO_TEST_DEF.match(line)
            if m and cur_file:
                # Go test ID is `pkg path/TestName`; pkg = directory of file
                pkg = "/".join(cur_file.rsplit("/", 1)[:-1]) or "."
                out.append(f"{pkg}/{m.group(1)}")
        elif language in ("typescript", "javascript"):
            m = TS_TEST_DEF.match(line)
            if m and cur_file:
                out.append(f"{cur_file} > {m.group(1)}")
    return out


def update_task(path: pathlib.Path) -> dict:
    task = json.loads(path.read_text())
    fail_to_pass = extract_fail_to_pass(task["language"], task.get("test_patch", ""))
    task["FAIL_TO_PASS"] = fail_to_pass
    task["_verifier_notes"] = (
        f"FAIL_TO_PASS extracted heuristically from test_patch ({len(fail_to_pass)} tests). "
        "PASS_TO_PASS left empty — populate from a representative sample of pre-existing tests "
        "in the touched modules. verified=False until --run round-trip succeeds."
    )
    path.write_text(json.dumps(task, indent=2))
    return task


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--tasks-dir", default="tasks/")
    ap.add_argument("--filter-lang", default=None,
                    help="Only verify tasks with this language tag")
    ap.add_argument("--run", action="store_true",
                    help="(Strict mode, slower) Actually run tests pre/post.")
    args = ap.parse_args()

    if args.run:
        print("Strict mode (--run) is reserved for the operator-in-the-loop verifier; "
              "use scripts/verify_strict.sh once that exists.", file=sys.stderr)
        return 2

    tasks_dir = pathlib.Path(args.tasks_dir)
    files = sorted(tasks_dir.glob("*.json"))
    if not files:
        print(f"No task files in {tasks_dir}", file=sys.stderr)
        return 1

    summary: dict[str, list[int]] = {}
    for f in files:
        task = json.loads(f.read_text())
        if args.filter_lang and task["language"] != args.filter_lang:
            continue
        new = update_task(f)
        n = len(new["FAIL_TO_PASS"])
        summary.setdefault(new["language"], []).append(n)
        flag = "✓" if n > 0 else "—"
        print(f"  {flag} {f.name}: FAIL_TO_PASS={n}")

    print()
    print("=== Summary ===")
    for lang, counts in sorted(summary.items()):
        nonzero = sum(1 for c in counts if c > 0)
        avg = sum(counts) / len(counts) if counts else 0
        print(f"  {lang:12s} {nonzero}/{len(counts)} tasks have FAIL_TO_PASS, "
              f"avg {avg:.1f} tests/task")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
