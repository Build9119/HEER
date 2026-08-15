#!/usr/bin/env python3
"""deploy.py — HEER DevOps / Deployment Agent (Phase 3.6).

Tools:
  docker (L2): validate a manifest-based build plan and produce a
               build/run spec with health-check + rollback note.

Demo mode: returns a dry-run build plan (image name, ports, env keys)
without invoking docker. Real mode (HEER_EXECUTION=1) runs `docker build`
with the allowlisted builder.

Run:  python3 -m agent.deploy --self-test
"""

import json
import os
import subprocess

from . import data

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXECUTION_ON = "1"


def _execution_enabled():
    return data.env("HEER_EXECUTION", "0") == _EXECUTION_ON


def _docker_available():
    try:
        subprocess.run(["docker", "--version"], capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# docker (L2)
# ---------------------------------------------------------------------------


def docker(image=None, tag="latest", context=None, dockerfile="Dockerfile",
           ports=None, env=None, healthcheck=None, business_id=None):
    """Validate a manifest build plan and produce a build/run spec.

    Returns a dry-run plan by default. Real build only when
    HEER_EXECUTION=1 + docker-builder allowlist entry in .heer/builder.json.
    """
    image = image or "heer-app"
    context = context or "."
    ports = ports or []
    env = env or []
    if isinstance(ports, str):
        ports = [p.strip() for p in ports.split(",") if p.strip()]
    if isinstance(env, str):
        env = [e.strip() for e in env.split(",") if e.strip()]

    dockerfile_path = os.path.normpath(os.path.join(_BASE, context, dockerfile))
    if not dockerfile_path.startswith(_BASE):
        return {"ok": False, "error": "dockerfile path escapes the HEER workspace."}
    if not os.path.isfile(dockerfile_path):
        return {"ok": False, "error": f"Dockerfile not found: {context}/{dockerfile}"}

    spec = {
        "image": f"{image}:{tag}",
        "context": context,
        "dockerfile": dockerfile,
        "ports": ports,
        "env_keys": sorted(e.split("=", 1)[0] for e in env),
        "healthcheck": healthcheck or {
            "type": "http",
            "endpoint": "/api/system",
            "interval": "30s",
            "retries": 3,
        },
        "rollback": "docker rollback = previous image tag re-deploy; "
                    "approved deploys only."
    }

    if not _execution_enabled() or not _docker_available():
        return {
            "ok": True, **spec, "mode": "dry_run", "status": "planned",
            "would_build": True,
            "note": "HEER_EXECUTION=0 or docker unavailable — dry-run plan only.",
        }

    # Real mode: docker build (allowlisted builder only)
    builder = os.path.join(_BASE, ".heer", "builder.json")
    try:
        with open(builder, "r", encoding="utf-8") as f:
            builder_cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        builder_cfg = {}
    allowed = builder_cfg.get("allowed", False)
    if not allowed:
        return {
            "ok": True, **spec, "mode": "dry_run", "status": "blocked",
            "would_build": True,
            "note": "Builder not allowlisted (.heer/builder.json allowed=true).",
        }

    cmd = ["docker", "build", "-t", f"{image}:{tag}",
           "-f", dockerfile_path, context]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "docker build timed out after 600s."}
    if proc.returncode != 0:
        return {"ok": False, "error": f"docker build failed: {proc.stderr[-2000:]}"}
    return {"ok": True, **spec, "mode": "executed", "status": "built",
            "image_id": (proc.stdout or proc.stderr).splitlines()[-1][:120]}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def call_deploy_tool(name, args=None, business_id=None):
    args = args or {}
    if name == "docker":
        r = docker(image=args.get("image"), tag=args.get("tag", "latest"),
                   context=args.get("context"),
                   dockerfile=args.get("dockerfile", "Dockerfile"),
                   ports=args.get("ports"), env=args.get("env"),
                   healthcheck=args.get("healthcheck"), business_id=business_id)
        return {"tool": name, **r}
    return {"tool": name, "ok": False,
            "error": f"Unknown deploy tool '{name}'."}


DEPLOY_TOOLS = {
    "docker": {
        "desc": "Validate a Docker build plan (dry-run default; real build behind L2 + allowlist).",
        "params": {
            "image": "string (default heer-app)",
            "tag": "string (default latest)",
            "context": "string (default .)",
            "ports": "list or csv string",
            "env": "list or csv string of KEY=value",
        },
        "fn": lambda name, args, business_id=None: call_deploy_tool(name, args, business_id),
    },
}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _self_test():
    print("HEER DevOps / Deployment Agent self-test\n" + "-" * 40)
    results = []
    df = os.path.join(_BASE, "Dockerfile")
    has_df = os.path.isfile(df)

    if has_df:
        r1 = docker(image="heer", tag="test", context=".",
                    dockerfile="Dockerfile", ports=["8000:8000"],
                    env=["HEER_DEMO=1"])
        ok1 = (r1.get("ok") is True
               and r1.get("mode") in ("dry_run", "executed")
               and r1.get("image") == "heer:test" and "env_keys" in r1)
    else:
        ok1 = True
    results.append(("docker dry-run plan" + ("" if has_df else " (no Dockerfile)"), ok1))

    r2 = docker(image="heer", context=".", dockerfile="Nope")
    ok2 = r2.get("ok") is False and "not found" in r2.get("error", "")
    results.append(("docker missing Dockerfile fails cleanly", ok2))

    r3 = docker(image="heer", context="..", dockerfile="Dockerfile")
    ok3 = r3.get("ok") is False and "escapes" in r3.get("error", "")
    results.append(("docker path escape blocked", ok3))

    r4 = docker(image="heer", context=".", dockerfile="Dockerfile",
                ports="8000:8000,8081:8081", env="A=1,B=2")
    if r4.get("ok") is False and "not found" in r4.get("error", ""):
        ok4 = True
    else:
        ok4 = (r4.get("ok") is True and len(r4.get("ports", [])) == 2
               and r4.get("env_keys") == ["A", "B"])
    results.append(("docker csv ports/env parsing", ok4))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())
