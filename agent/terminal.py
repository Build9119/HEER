#!/usr/bin/env python3
"""terminal.py — HEER Terminal Executor (Phase 3.7, L3-critical).

Tools:
  terminal_exec (L3): run an allowlisted command and capture output.

The allowlist is a fixed set of safe, read-only/self-test commands.
Every invocation routes through the L3 approval gate. Real execution
requires HEER_EXECUTION=1; otherwise returns a dry-run artifact.

Run:  python3 -m agent.terminal --self-test
"""

import shlex
import subprocess
import sys

from . import data

# Closed-set allowlist — nothing outside these exact tokens executes.
ALLOWLIST = {
    "git status --short",
    "git branch --show-current",
    "git log --oneline -10",
    "python3 -m pytest -q",
    "python3 -m agent.mission --self-test",
    "python3 -m agent.developer --self-test",
    "python3 -m agent.github_agent --self-test",
    "python3 -m agent.n8n --self-test",
    "python3 -m agent.deploy --self-test",
    "python3 -m agent.terminal --self-test",
    "docker --version",
    "docker compose config",
    "ls",
}

_EXECUTION_ON = "1"


def _execution_enabled():
    return data.env("HEER_EXECUTION", "0") == _EXECUTION_ON


def terminal_exec(command, timeout=60, business_id=None):
    """Run an allowlisted command. Returns output + metadata.

    command: exact string (shlex-normalized) present in ALLOWLIST.
    """
    cmd = (command or "").strip()
    if not cmd:
        return {"ok": False, "error": "command is required."}
    # Normalize whitespace to allow multi-space variants
    normalized = " ".join(cmd.split())
    if normalized not in ALLOWLIST:
        return {"ok": False,
                "error": f"Command blocked — not in allowlist: '{cmd}'"}

    if not _execution_enabled():
        return {
            "ok": True, "command": normalized, "mode": "dry_run",
            "would_run": True, "status": "blocked",
            "note": "HEER_EXECUTION=0 — dry-run only. Set HEER_EXECUTION=1 + "
                    "L3 approval to execute.",
        }

    try:
        proc = subprocess.run(normalized, shell=False, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Command timed out after {timeout}s."}
    return {
        "ok": proc.returncode == 0,
        "command": normalized,
        "mode": "executed",
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "")[-4000:],
        "stderr": (proc.stderr or "")[-1000:],
    }


def allowlist_payload():
    """Expose the allowlist (read-only metadata)."""
    return {"commands": sorted(ALLOWLIST), "count": len(ALLOWLIST),
            "note": "Closed-set allowlist. All runs require L3 approval."}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def call_terminal_tool(name, args=None, business_id=None):
    args = args or {}
    if name == "terminal_exec":
        r = terminal_exec(args.get("command") or "",
                          timeout=int(args.get("timeout", 60)), business_id=business_id)
        return {"tool": name, **r}
    return {"tool": name, "ok": False, "error": f"Unknown terminal tool '{name}'."}


TERMINAL_TOOLS = {
    "terminal_exec": {
        "desc": "Run an allowlisted command (L3 approval). Closed-set allowlist only.",
        "params": {"command": "exact allowlisted command string"},
        "fn": lambda name, args, business_id=None: call_terminal_tool(name, args, business_id),
    },
}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _self_test():
    print("HEER Terminal Executor self-test\n" + "-" * 40)
    results = []

    r1 = terminal_exec("git status --short")
    ok1 = (r1.get("ok") is True and r1.get("mode") == "dry_run"
           and r1.get("would_run") is True)
    results.append(("terminal_exec dry-run (L3 gated)", ok1))

    r2 = terminal_exec("rm -rf /")
    ok2 = r2.get("ok") is False and "allowlist" in r2.get("error", "")
    results.append(("terminal_exec blocks non-allowlisted command", ok2))

    r3 = terminal_exec("", )
    ok3 = r3.get("ok") is False and "required" in r3.get("error", "")
    results.append(("terminal_exec requires command", ok3))

    r4 = allowlist_payload()
    ok4 = r4.get("count", 0) >= 5 and "git status --short" in r4["commands"]
    results.append(("allowlist_payload lists commands", ok4))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())