#!/usr/bin/env python3
"""developer.py — HEER Developer Agent (Phase 3.3).

Workspace-scoped source read/write + lightweight test runner.

Tools:
  code_read  (L0): read a file inside the HEER workspace (path containment)
  code_write (L1): create/modify a file with diff preview + python syntax check
  test_run   (L1): run pytest-style API smoke tests, return pass/fail summary

Demo mode: code_write returns a dry-run artifact (no real file write) unless
HEER_EXECUTION=1. code_read always works on real files. test_run in demo mode
runs a canned "test" that validates the environment reports the executable.

Run:  python3 -m agent.developer --self-test
"""

import ast
import difflib
import json
import os
import subprocess
import sys

from . import data

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _execution_enabled():
    """Real side-effects only when HEER_EXECUTION=1.

    Default (demo) mode: code_write/test_run produce dry-run plans.
    """
    return data.env("HEER_EXECUTION", "0") == "1"


def _resolve_path(rel):
    """Resolve a workspace-relative path to an absolute path.

    Enforces containment inside BASE (no .. escapes outside HEER).
    Returns None when the path escapes the workspace.
    """
    rel = (rel or "").strip().lstrip("/")
    if not rel:
        return None
    full = os.path.normpath(os.path.join(BASE, rel))
    if not full.startswith(BASE):
        return None
    return full


# ---------------------------------------------------------------------------
# code_read (L0)
# ---------------------------------------------------------------------------


def code_read(rel, business_id=None):
    """Read a workspace file (text). Returns content + metadata."""
    path = _resolve_path(rel)
    if path is None:
        return {"ok": False, "error": f"Path '{rel}' is outside the HEER workspace."}
    if not os.path.isfile(path):
        return {"ok": False, "error": f"File not found: {rel}"}
    try:
        size = os.path.getsize(path)
        if size > 2 * 1024 * 1024:
            return {"ok": False, "error": f"File too large to read ({size} bytes)."}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        return {"ok": False, "error": f"Read failed: {e}"}
    return {
        "ok": True,
        "path": rel,
        "abs_path": path,
        "size": size,
        "lines": text.count("\n") + 1,
        "content": text[:20000],  # cap transcript payloads
        "truncated": size > 20000,
    }


# ---------------------------------------------------------------------------
# code_write (L1)
# ---------------------------------------------------------------------------


def _syntax_check(path, content):
    """Python syntax check (only for .py files). Returns None or error string."""
    if not path.endswith(".py"):
        return None
    try:
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})"


def _existing_content(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def code_write(rel, content, business_id=None):
    """Create or modify a file. Returns diff preview + status.

    Real write only when HEER_EXECUTION=1. Demo mode returns the diff as a
    dry-run artifact with a `would_write` marker.
    """
    path = _resolve_path(rel)
    if path is None:
        return {"ok": False, "error": f"Path '{rel}' is outside the HEER workspace."}
    if not content:
        return {"ok": False, "error": "content is required for code_write."}

    # Syntax check .py files before writing
    if rel.endswith(".py"):
        err = _syntax_check(rel, content)
        if err:
            return {"ok": False, "error": err}

    old = _existing_content(path)
    is_new = old is None
    diff = "".join(difflib.unified_diff(
        (old or "").splitlines(keepends=True),
        content.splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}",
    ))
    if not is_new and not diff:
        return {"ok": True, "path": rel, "status": "unchanged", "diff": "",
                "mode": "write"}

    payload = {
        "ok": True,
        "path": rel,
        "abs_path": path,
        "operation": "create" if is_new else "modify",
        "bytes": len(content.encode("utf-8")),
        "diff": diff[:4000],
        "mode": "write",
    }

    if not _execution_enabled():
        payload["status"] = "dry_run"
        payload["would_write"] = True
        payload["note"] = ("HEER_EXECUTION=0 — dry-run only. Set HEER_EXECUTION=1 "
                           "and approve (L1) to write.")
        return payload

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return {"ok": False, "error": f"Write failed: {e}"}

    payload["status"] = "written"
    return payload


# ---------------------------------------------------------------------------
# test_run (L1)
# ---------------------------------------------------------------------------


def test_run(target=None, business_id=None):
    """Run workspace tests (pytest-style) or canned validation.

    target: optional rel path to a test module or directory.
    Real run only when HEER_EXECUTION=1. Demo mode returns a canned
    environment check.
    """
    if not _execution_enabled():
        # Demo-mode self-check: verify the interpreter + project are importable
        checks = []
        ok = True
        try:
            import agent.mission  # noqa: F401
            checks.append({"check": "import agent.mission", "status": "pass"})
        except Exception as e:  # noqa: BLE001
            ok = False
            checks.append({"check": "import agent.mission", "status": "fail",
                           "detail": str(e)[:200]})
        return {
            "ok": ok,
            "mode": "dry_run",
            "summary": "Demo test run (HEER_EXECUTION=0)",
            "checks": checks,
            "passed": sum(1 for c in checks if c["status"] == "pass"),
            "failed": sum(1 for c in checks if c["status"] != "pass"),
        }

    # Real mode: try pytest-like discovery
    target = target or "tests"
    tpath = _resolve_path(target)
    if tpath is None:
        return {"ok": False, "error": f"Test target '{target}' is outside the workspace."}
    if not os.path.exists(tpath):
        return {"ok": False, "error": f"Test target not found: {target}"}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--disable-warnings", target],
            capture_output=True, text=True, timeout=120,
        )
    except FileNotFoundError:
        return {"ok": False, "error": "pytest not installed."}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Test run timed out after 120s."}
    return {
        "ok": proc.returncode == 0,
        "mode": "executed",
        "target": target,
        "returncode": proc.returncode,
        "summary": (proc.stdout or proc.stderr)[-2000:],
    }


# ---------------------------------------------------------------------------
# Tool dispatch (name -> fn matching tools.py contract)
# ---------------------------------------------------------------------------


def call_developer_tool(name, args=None, business_id=None):
    """Dispatch a developer tool. Returns {"tool", "ok", ...}."""
    args = args or {}
    if name == "code_read":
        r = code_read(args.get("path") or args.get("file") or "", business_id)
        return {"tool": name, **r}
    if name == "code_write":
        rel = args.get("path") or args.get("file") or ""
        content = args.get("content") or args.get("text") or ""
        r = code_write(rel, content, business_id)
        return {"tool": name, **r}
    if name == "test_run":
        r = test_run(args.get("target"), business_id)
        return {"tool": name, **r}
    return {"tool": name, "ok": False, "error": f"Unknown developer tool '{name}'."}


DEVELOPER_TOOLS = {
    "code_read": {
        "desc": "Read a workspace source file (returned as text).",
        "params": {"path": "string — workspace-relative file path"},
        "fn": lambda name, args, business_id=None: call_developer_tool(name, args, business_id),
    },
    "code_write": {
        "desc": "Create or modify a workspace file with diff preview. Python files are syntax-checked before write.",
        "params": {
            "path": "string — workspace-relative file path",
            "content": "string — full new file content",
        },
        "fn": lambda name, args, business_id=None: call_developer_tool(name, args, business_id),
    },
    "test_run": {
        "desc": "Run the workspace test suite (pytest-style) or demo validation.",
        "params": {"target": "string (optional) — path to tests"},
        "fn": lambda name, args, business_id=None: call_developer_tool(name, args, business_id),
    },
}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _self_test():
    print("HEER Developer Agent self-test\n" + "-" * 40)
    results = []

    # Scenario 1: code_read on an existing file
    r1 = code_read("HEER_ARCHITECTURE.md", None)
    ok1 = r1.get("ok") is True and r1.get("size", 0) > 0 and "content" in r1
    results.append(("code_read existing file", ok1))

    # Scenario 2: code_read on a missing file
    r2 = code_read("does/not/exist.py", None)
    ok2 = r2.get("ok") is False and "not found" in r2.get("error", "")
    results.append(("code_read missing file fails cleanly", ok2))

    # Scenario 3: path traversal blocked
    r3 = code_read("../../etc/passwd", None)
    ok3 = r3.get("ok") is False and "outside" in r3.get("error", "")
    results.append(("code_read blocks path traversal", ok3))

    # Scenario 4: code_write dry-run (demo mode default)
    r4 = code_write("tmp/_dev_selftest.py", "def hello():\n    return 'hi'\n", None)
    ok4 = (r4.get("ok") is True and r4.get("mode") == "write"
           and r4.get("status") in ("dry_run", "written")
           and "diff" in r4)
    results.append(("code_write dry-run or write", ok4))

    # Scenario 5: code_write syntax error rejected
    r5 = code_write("tmp/_bad.py", "def broken(:\n    pass\n", None)
    ok5 = r5.get("ok") is False and "SyntaxError" in r5.get("error", "")
    results.append(("code_write rejects invalid python", ok5))

    # Scenario 6: test_run demo validation
    r6 = test_run(None, None)
    ok6 = r6.get("ok") is True and r6.get("mode") == "dry_run"
    results.append(("test_run demo validation", ok6))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())