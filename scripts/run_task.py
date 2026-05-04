#!/usr/bin/env python3
"""Runner: execute one task with a candidate patch and emit grade.json.

Steps per task:
  1. Clone repo at base_commit into a temp workdir (or reuse cached).
  2. Apply test_patch (so FAIL_TO_PASS tests exist).
  3. Apply candidate patch (the agent's submission).
  4. Install deps per runner.install.
  5. Run runner.test_cmd, scoped to FAIL_TO_PASS test ids when possible.
  6. Parse pass/fail per test id and write grade.json.

Supports python (pytest), go (go test), typescript (vitest/jest via runner).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile
import time
from typing import Any


def sh(cmd: str | list[str], *, cwd: pathlib.Path | None = None,
       env: dict[str, str] | None = None, timeout: int = 600,
       capture: bool = True) -> tuple[int, str]:
    """Run a shell command, return (returncode, combined_stdout_stderr)."""
    if isinstance(cmd, str):
        cmd = ["bash", "-lc", cmd]
    p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                       capture_output=capture, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def clone_at(repo: str, sha: str, workdir: pathlib.Path) -> None:
    """Shallow-clone `repo` at `sha` into workdir (which must not yet exist)."""
    workdir.parent.mkdir(parents=True, exist_ok=True)
    if workdir.exists():
        return  # cached
    rc, out = sh(["git", "clone", "--quiet", f"https://github.com/{repo}.git",
                  str(workdir)], timeout=600, capture=True)
    if rc != 0:
        raise RuntimeError(f"clone failed: {out[:400]}")
    rc, out = sh(["git", "checkout", "--quiet", sha], cwd=workdir,
                 timeout=120, capture=True)
    if rc != 0:
        raise RuntimeError(f"checkout {sha[:8]} failed: {out[:400]}")


def apply_patch(workdir: pathlib.Path, diff: str, label: str) -> tuple[bool, str]:
    """Apply a unified diff via `git apply`. Return (ok, log)."""
    if not diff.strip():
        return True, f"[{label}] empty patch — skipped"
    p = subprocess.run(["git", "apply", "--whitespace=nowarn", "--reject", "-"],
                       cwd=workdir, input=diff, text=True,
                       capture_output=True, timeout=60)
    log = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        # Try 3-way as a fallback
        p2 = subprocess.run(["git", "apply", "--3way", "--whitespace=nowarn", "-"],
                            cwd=workdir, input=diff, text=True,
                            capture_output=True, timeout=60)
        log += "\n[3way] " + (p2.stdout or "") + (p2.stderr or "")
        if p2.returncode != 0:
            return False, log
    return True, log


# ----- Language runners ---------------------------------------------------

def run_python(task: dict, workdir: pathlib.Path,
               timeout: int) -> tuple[dict[str, bool], str]:
    """Install + pytest. Returns (test_id → passed, log)."""
    runner = task["runner"]
    install = runner.get("install", "pip install -e .")
    test_cmd = runner.get("test_cmd", "pytest -p no:cacheprovider --tb=short -v")

    # Use a venv per task to isolate
    venv = workdir / ".pcb_venv"
    if not venv.exists():
        sh(["python3", "-m", "venv", str(venv)], timeout=60)
    py = str(venv / "bin" / "python")
    pip = str(venv / "bin" / "pip")
    sh([pip, "install", "--upgrade", "pip", "setuptools", "wheel"],
       cwd=workdir, timeout=120)

    rc, install_log = sh(f". {venv}/bin/activate && {install}",
                         cwd=workdir, timeout=600)
    log = f"[install rc={rc}]\n{install_log[-2000:]}\n"
    if rc != 0:
        return {}, log + "[abort: install failed]"

    fail_to_pass = task.get("FAIL_TO_PASS", [])
    pass_to_pass = task.get("PASS_TO_PASS", [])
    test_args = " ".join(shlex.quote(t) for t in fail_to_pass + pass_to_pass)
    if test_args:
        cmd = f". {venv}/bin/activate && {test_cmd} {test_args}"
    else:
        cmd = f". {venv}/bin/activate && {test_cmd}"
    rc, test_log = sh(cmd, cwd=workdir, timeout=timeout)
    log += f"[test rc={rc}]\n{test_log[-3000:]}\n"

    # Parse pytest output for per-test status. Pytest may emit:
    #   path::test_name PASSED                       (non-parametrized)
    #   path::test_name[param] PASSED                (parametrized)
    #   path::Class::test_name PASSED                (class)
    #   path::Class::test_name[param] PASSED         (class + parametrized)
    # We accept any line that starts with the tid and ends in PASSED.
    results: dict[str, bool] = {}
    for tid in fail_to_pass + pass_to_pass:
        # Match tid optionally followed by [...] or any chars then whitespace + PASSED
        passed_re = re.compile(rf"{re.escape(tid)}(\[[^\]]*\])?\s+PASSED")
        failed_re = re.compile(rf"{re.escape(tid)}(\[[^\]]*\])?\s+(FAILED|ERROR)")
        passed_count = len(passed_re.findall(test_log))
        failed_count = len(failed_re.findall(test_log))
        if passed_count > 0 and failed_count == 0:
            results[tid] = True
        elif failed_count > 0:
            results[tid] = False
        else:
            results[tid] = False  # not collected
    return results, log


def run_go(task: dict, workdir: pathlib.Path,
           timeout: int) -> tuple[dict[str, bool], str]:
    """go test ./pkg -run ^TestName$ for each FAIL_TO_PASS, parse results."""
    runner = task["runner"]
    install = runner.get("install", "go mod download")
    rc, install_log = sh(install, cwd=workdir, timeout=300)
    log = f"[install rc={rc}]\n{install_log[-1500:]}\n"
    if rc != 0:
        return {}, log + "[abort: install failed]"

    results: dict[str, bool] = {}
    for tid in task.get("FAIL_TO_PASS", []) + task.get("PASS_TO_PASS", []):
        # tid format: "path/to/pkg/TestName" or just "TestName"
        if "/" in tid:
            pkg, name = tid.rsplit("/", 1)
            pkg_arg = "./" + pkg if not pkg.startswith(".") else pkg
        else:
            pkg_arg = "./..."
            name = tid
        cmd = f"go test {shlex.quote(pkg_arg)} -run '^{re.escape(name)}$' -count=1 -v"
        rc, out = sh(cmd, cwd=workdir, timeout=timeout)
        log += f"[{tid}] rc={rc}\n{out[-800:]}\n---\n"
        results[tid] = (rc == 0 and re.search(rf"--- PASS: {re.escape(name)}", out) is not None)
    return results, log


def run_typescript(task: dict, workdir: pathlib.Path,
                   timeout: int) -> tuple[dict[str, bool], str]:
    """pnpm install + run vitest/jest. Coarse: test_cmd over the whole repo."""
    runner = task["runner"]
    install = runner.get("install", "pnpm install --frozen-lockfile")
    test_cmd = runner.get("test_cmd", "pnpm test")

    rc, install_log = sh(install, cwd=workdir, timeout=900)
    log = f"[install rc={rc}]\n{install_log[-1500:]}\n"
    if rc != 0:
        return {}, log + "[abort: install failed]"

    rc, out = sh(test_cmd, cwd=workdir, timeout=timeout)
    log += f"[test rc={rc}]\n{out[-3000:]}\n"

    results: dict[str, bool] = {}
    for tid in task.get("FAIL_TO_PASS", []) + task.get("PASS_TO_PASS", []):
        # tid: "path/file.test.ts > test name"
        name = tid.split(" > ", 1)[-1]
        # Vitest reports "✓ name" / "✗ name" or "FAIL name"
        if re.search(rf"(?:✓|PASS)\s+.*{re.escape(name)}", out):
            results[tid] = True
        else:
            results[tid] = False
    return results, log


RUNNERS = {
    "python": run_python,
    "go": run_go,
    "typescript": run_typescript,
    "javascript": run_typescript,
}


def grade(results: dict[str, bool], task: dict) -> dict[str, Any]:
    f2p = [t for t in task["FAIL_TO_PASS"] if results.get(t, False)]
    p2p_total = len(task.get("PASS_TO_PASS", []))
    p2p_pass = sum(1 for t in task.get("PASS_TO_PASS", []) if results.get(t, False))
    return {
        "instance_id": task["instance_id"],
        "fail_to_pass_passed": len(f2p),
        "fail_to_pass_total": len(task["FAIL_TO_PASS"]),
        "pass_to_pass_passed": p2p_pass,
        "pass_to_pass_total": p2p_total,
        "passed": (len(f2p) == len(task["FAIL_TO_PASS"]) and len(task["FAIL_TO_PASS"]) > 0
                   and p2p_pass == p2p_total),
        "results": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--task-file", required=True)
    ap.add_argument("--patch", default=None,
                    help="Path to candidate diff (defaults to gold patch from task)")
    ap.add_argument("--workdir-root", default="/tmp/pcb_workdirs")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--keep-workdir", action="store_true")
    ap.add_argument("--out", default=None,
                    help="Path for grade.json (defaults: alongside the patch)")
    args = ap.parse_args()

    task = json.loads(pathlib.Path(args.task_file).read_text())
    lang = task["language"]
    runner_fn = RUNNERS.get(lang)
    if not runner_fn:
        print(f"language '{lang}' not yet supported by runner", file=sys.stderr)
        return 2

    if args.patch is None:
        candidate_diff = task["patch"]   # gold sanity-check
        candidate_label = "GOLD"
    else:
        candidate_diff = pathlib.Path(args.patch).read_text()
        candidate_label = pathlib.Path(args.patch).name

    workdir_root = pathlib.Path(args.workdir_root)
    wd = workdir_root / task["instance_id"]
    if wd.exists():
        sh(["rm", "-rf", str(wd)], timeout=60)

    t0 = time.time()
    log_parts: list[str] = []
    try:
        clone_at(task["repo"], task["base_commit"], wd)
        log_parts.append(f"[clone {task['repo']}@{task['base_commit'][:8]} ok]")
        ok, plog = apply_patch(wd, task.get("test_patch", ""), "test_patch")
        log_parts.append(plog)
        if not ok:
            raise RuntimeError("test_patch did not apply at base_commit")
        ok, plog = apply_patch(wd, candidate_diff, candidate_label)
        log_parts.append(plog)
        if not ok:
            log_parts.append(f"[{candidate_label} apply failed; running tests anyway]")

        results, run_log = runner_fn(task, wd, args.timeout)
        log_parts.append(run_log)
    except subprocess.TimeoutExpired as e:
        log_parts.append(f"[timeout: {e}]")
        results = {}
    except Exception as e:
        log_parts.append(f"[ERROR: {e}]")
        results = {}

    grade_obj = grade(results, task)
    grade_obj["agent_seconds"] = time.time() - t0
    grade_obj["candidate_label"] = candidate_label

    out_path = pathlib.Path(args.out) if args.out else \
        pathlib.Path(args.task_file).parent.parent / "grades" / \
        f"{task['instance_id']}__{candidate_label}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(grade_obj, indent=2))

    log_path = out_path.with_suffix(".log")
    log_path.write_text("\n\n".join(log_parts))

    if not args.keep_workdir:
        sh(["rm", "-rf", str(wd)], timeout=60)

    print(json.dumps(grade_obj, indent=2))
    return 0 if grade_obj["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
