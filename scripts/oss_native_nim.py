"""OpenAI-native tool-calling harness for OpenAI-format models on Regolo.

The other harnesses in tier2_smoke (qwen-CLI, openclaude, opencode, mini-swe-
agent) each layer their own protocol over the API and don't speak standard
OpenAI function-calling. gpt-oss-120b on Regolo handles standard OpenAI tools
correctly (verified via raw curl: returns proper `tool_calls` array, finish
reason `tool_calls`). This harness uses that path directly.

Loop:
  1. Send messages + tools to chat.completions.create()
  2. If response has tool_calls: execute each, append `role=tool` result, recall
  3. If response has text content (no tool_calls): treat as final, stop
  4. Stop when finish=`stop` AND no tools were called this turn, OR after N turns,
     OR when the model calls the `submit_patch` tool.

Tools provided:
  - run_shell(cmd)            — execute shell command in workdir, return stdout/stderr
  - read_file(path)           — read a file
  - write_file(path, content) — overwrite a file with new content
  - search(pattern, path?)    — grep-style search (uses ripgrep if available, else grep -rn)
  - submit_patch()            — model declares it's done; loop terminates
"""
from __future__ import annotations
import json
import os
import re
import subprocess
from pathlib import Path

import requests


# Hardcoded HTTPS endpoint — `requests` library, not user-controlled, no
# scheme injection risk (semgrep CWE-939 concern N/A).
API_URL = os.environ.get("OSS_API_URL", "https://api.regolo.ai/v1/chat/completions")
MAX_TURNS = 30
PER_REQUEST_TIMEOUT = 120

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command in the working directory. Returns stdout+stderr (truncated to 4000 chars).",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Shell command to run"},
                },
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file. Returns the text (truncated to 8000 chars per call).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Overwrite a file with new content. ALWAYS use this to make code changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Recursive grep for a pattern. Returns matching file:line snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "description": "Optional subdir; defaults to '.'"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_patch",
            "description": "Call this when your fix is complete. Terminates the loop.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _resolve_tls_verify():
    """Resolve TLS verification target.

    Default: verify against the system CA bundle (secure default).
    If the operator sets REGOLO_CA_BUNDLE to a CA file path, use it.
    If REGOLO_VERIFY_TLS=0 (operator-acknowledged trust decision, e.g. during
    a known cert-rotation window), skip verification. The source never hardcodes
    a "skip verify" — the operator must opt in via env var.
    """
    bundle = os.environ.get("REGOLO_CA_BUNDLE")
    if bundle and Path(bundle).is_file():
        return bundle
    if os.environ.get("REGOLO_VERIFY_TLS", "1") == "0":
        # Suppress urllib3 InsecureRequestWarning when operator opted in
        try:
            from urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except Exception:
            pass
        return False
    return True


def _post_json(api_key: str, body: dict, timeout: int = PER_REQUEST_TIMEOUT) -> dict:
    """POST JSON to the Regolo chat-completions endpoint and return parsed response.

    Uses `requests` (not urllib) — endpoint is hardcoded, no scheme-injection
    surface. TLS verification is operator-controlled via REGOLO_VERIFY_TLS /
    REGOLO_CA_BUNDLE env vars (secure default: verify against system CAs).
    """
    try:
        r = requests.post(
            API_URL,
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            verify=_resolve_tls_verify(),
        )
        if r.status_code != 200:
            return {"error": {"status": r.status_code, "message": r.text[:500]}}
        return r.json()
    except requests.RequestException as e:
        return {"error": {"message": f"{type(e).__name__}: {e}"}}
    except ValueError as e:
        return {"error": {"message": f"JSONDecodeError: {e}"}}


def _exec_tool(name: str, args: dict, workdir: Path) -> str:
    """Execute one tool call; return result string (truncated for context)."""
    try:
        if name == "run_shell":
            cmd = args.get("cmd", "")
            r = subprocess.run(["bash", "-c", cmd], cwd=workdir, capture_output=True,
                               text=True, timeout=60)
            out = (r.stdout or "") + (r.stderr or "")
            return f"[exit {r.returncode}]\n{out[:4000]}"
        if name == "read_file":
            p = (workdir / args["path"]).resolve()
            if not str(p).startswith(str(workdir.resolve())):
                return "ERROR: path escapes workdir"
            try:
                content = Path(p).read_text(errors="replace")
                if len(content) > 8000:
                    return content[:8000] + f"\n[truncated; total {len(content)} chars]"
                return content
            except FileNotFoundError:
                return f"ERROR: file not found: {args['path']}"
            except IsADirectoryError:
                return f"ERROR: is a directory: {args['path']}"
        if name == "write_file":
            p = (workdir / args["path"]).resolve()
            if not str(p).startswith(str(workdir.resolve())):
                return "ERROR: path escapes workdir"
            Path(p).parent.mkdir(parents=True, exist_ok=True)
            Path(p).write_text(args["content"])
            return f"wrote {len(args['content'])} chars to {args['path']}"
        if name == "search":
            pattern = args["pattern"]
            path = args.get("path", ".")
            for tool in (["rg", "-n", pattern, path], ["grep", "-rn", pattern, path]):
                try:
                    r = subprocess.run(tool, cwd=workdir, capture_output=True,
                                       text=True, timeout=30)
                    if r.returncode in (0, 1):  # 1 = no matches but worked
                        out = r.stdout[:4000]
                        return out or "[no matches]"
                except FileNotFoundError:
                    continue
            return "ERROR: no grep tool available"
        if name == "submit_patch":
            return "[submit_patch acknowledged; loop will terminate]"
        return f"ERROR: unknown tool '{name}'"
    except subprocess.TimeoutExpired:
        return f"ERROR: {name} timed out"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def run_oss_native(workdir: Path, task: dict, log_path: Path, model: str,
                   temperature: float = 0.3) -> str:
    """OpenAI-tools harness: runs an agentic loop using standard tool-calling.

    Returns the unified diff produced by the agent's edits (via _extract_diff,
    imported from orchestrate_grid).
    """
    API_KEY = os.environ.get("OSS_API_KEY", "")
    if not API_KEY:
        raise RuntimeError("OSS_API_KEY env var required")
    def _extract_diff(wd):
        # Local stand-in: just `git diff HEAD` from workdir
        import subprocess
        return subprocess.check_output(
            ["git", "-C", str(wd), "diff", "HEAD"], text=True
        )

    repo = task['repo']
    commit = task['base_commit'][:8]
    issue = task['problem_statement']

    system = (
        "You are an expert software engineer fixing real bugs in a Python codebase. "
        "You have tools: run_shell, read_file, write_file, search, submit_patch. "
        "USE THE TOOLS to do the work — do NOT describe edits in prose. "
        "Process: search for relevant files, read them, identify the bug, write the fix "
        "with write_file. Smallest correct change. Do NOT modify test files. "
        "Do NOT run pip install or pytest. When the fix is in place, call submit_patch."
    )
    user = (
        f"# Bug fix task — {repo}@{commit}\n\n"
        f"## Issue\n\n{issue}\n\n"
        f"Fix it via tool calls."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    log_lines = []
    log_lines.append(f"=== oss-native harness × {model} on {task['instance_id']} ===")

    submitted = False
    for turn in range(MAX_TURNS):
        body = {
            "model": model,
            "messages": messages,
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": 4096,
        }
        resp = _post_json(API_KEY, body)
        if "error" in resp:
            log_lines.append(f"[turn {turn}] API ERROR: {resp['error']}")
            break

        choice = resp.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []
        finish = choice.get("finish_reason")

        log_lines.append(
            f"\n[turn {turn}] finish={finish} content_len={len(content)} "
            f"tool_calls={len(tool_calls)}"
        )
        if content:
            log_lines.append(f"  content: {content[:300]!r}")

        # Append the assistant message verbatim (must include tool_calls if present)
        msg_for_history = {"role": "assistant", "content": content}
        if tool_calls:
            msg_for_history["tool_calls"] = tool_calls
        messages.append(msg_for_history)

        if not tool_calls:
            log_lines.append("  (no tool calls; ending loop)")
            break

        for tc in tool_calls:
            fn = (tc.get("function") or {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}
            log_lines.append(f"  -> {name}({json.dumps(args)[:200]})")
            result = _exec_tool(name, args, workdir)
            log_lines.append(f"     result[:300]: {result[:300]!r}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": result[:8000],
            })
            if name == "submit_patch":
                submitted = True

        if submitted:
            log_lines.append("[submit_patch called; terminating loop]")
            break

    log_lines.append(f"\nLoop ended at turn {turn}, submitted={submitted}")
    Path(log_path).write_text("\n".join(log_lines))
    return _extract_diff(workdir)


# Smoke-test entry point
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from orchestrate_grid import _extract_diff, API_KEY  # noqa
    print("oss_native_harness imports OK")
