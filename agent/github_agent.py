#!/usr/bin/env python3
"""github_agent.py — HEER GitHub Agent (Phase 3.4).

Tools:
  github_read  (L0): repo list, issues, PRs, branches, CI status.
                     Uses GitHub REST API when GITHUB_TOKEN is set;
                     returns structured demo fixtures otherwise.
  github_write (L2): create/comment on issues, open draft PRs.
                     Requires HEER_EXECUTION=1 + GITHUB_TOKEN; otherwise
                     returns a dry-run artifact labelled known/inferred.

Run:  python3 -m agent.github_agent --self-test
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from . import data

API = "https://api.github.com"
_UA = "HEER/3.4 (github_agent)"


def _token():
    return (data.env("GITHUB_TOKEN", "") or "").strip()


def _execution_enabled():
    return data.env("HEER_EXECUTION", "0") == "1"


def _request(path, method="GET", body=None):
    url = API + path
    headers = {
        "User-Agent": _UA,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tok = _token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, method=method, headers=headers)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"_raw": raw[:2000]}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            pass
        return {"ok": False, "error": f"GitHub API {e.code}: {detail}".strip()}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"GitHub API unreachable: {e.reason}"}


# ---------------------------------------------------------------------------
# Demo fixtures (used when no token configured)
# ---------------------------------------------------------------------------

_DEMO_REPOS = [
    {"full_name": "ai-agency/client-portal",
     "description": "Client onboarding & proposal portal (demo)",
     "default_branch": "main", "private": True, "language": "Python",
     "open_issues_count": 3, "stargazers_count": 0, "updated_at": "2026-10-02T10:00:00Z"},
    {"full_name": "ai-agency/atlas-logistics-intel",
     "description": "Atlas Logistics market intel pipeline (demo)",
     "default_branch": "main", "private": True, "language": "Python",
     "open_issues_count": 1, "stargazers_count": 0, "updated_at": "2026-10-05T10:00:00Z"},
    {"full_name": "ai-agency/heer-core",
     "description": "HEER operating core (demo)",
     "default_branch": "main", "private": True, "language": "Python",
     "open_issues_count": 5, "stargazers_count": 0, "updated_at": "2026-10-08T10:00:00Z"},
]

_DEMO_ISSUES = [
    {"number": 12, "title": "Portal: add SSO login",
     "state": "open", "labels": ["enhancement"], "created_at": "2026-09-20T10:00:00Z",
     "assignee": None},
    {"number": 11, "title": "Pipeline: stale opportunities > 30 days",
     "state": "open", "labels": ["bug", "priority: high"],
     "created_at": "2026-09-18T10:00:00Z", "assignee": None},
    {"number": 10, "title": "Docs: seed vertical templates",
     "state": "open", "labels": ["docs"], "created_at": "2026-09-15T10:00:00Z",
     "assignee": None},
]

_DEMO_PRS = [
    {"number": 42, "title": "feat: mission task-graph executor",
     "state": "open", "draft": True, "head": {"ref": "feature/mission-graph"},
     "base": {"ref": "main"}, "created_at": "2026-10-01T10:00:00Z",
     "mergeable": True, "reviewers": ["pankaj"]},
]

_DEMO_BRANCHES = [
    {"name": "main", "protected": True},
    {"name": "feature/mission-graph", "protected": False},
    {"name": "feature/automation-n8n", "protected": False},
]

_DEMO_CI = [
    {"workflow": "tests.yml", "conclusion": "success", "status": "completed",
     "ran_at": "2026-10-08T10:00:00Z"},
    {"workflow": "build.yml", "conclusion": "success", "status": "completed",
     "ran_at": "2026-10-08T10:00:00Z"},
]


def _demo_issue(repo):
    return {"repo": repo, "issues": _DEMO_ISSUES, "source": "demo_fixture",
            "note": "No GITHUB_TOKEN configured — demo fixtures only."}


def _demo_prs(repo):
    return {"repo": repo, "pull_requests": _DEMO_PRS, "source": "demo_fixture",
            "note": "No GITHUB_TOKEN configured — demo fixtures only."}


def _demo_branches(repo):
    return {"repo": repo, "branches": _DEMO_BRANCHES,
            "current_branch": "main", "source": "demo_fixture",
            "note": "No GITHUB_TOKEN configured — demo fixtures only."}


# ---------------------------------------------------------------------------
# github_read (L0)
# ---------------------------------------------------------------------------


def github_read(repo=None, resource="repos", owner=None, token=None,
                business_id=None):
    """Read GitHub data. resource: repos | issues | pulls | branches | ci.

    When GITHUB_TOKEN + HEER_EXECUTION=1 are set, queries the live API.
    Otherwise returns structured demo fixtures with source labels.
    """
    tok = token or _token()
    is_live = bool(tok) and _execution_enabled()

    if resource == "repos":
        if is_live:
            r = _request("/user/repos?sort=updated&per_page=30")
            if r.get("ok") is False:
                return r
            return {"ok": True, "repos": r, "count": len(r), "source": "github_api_known"}
        return {"ok": True, "repos": _DEMO_REPOS, "count": len(_DEMO_REPOS),
                "source": "demo_fixture",
                "note": "HEER_EXECUTION=0 or no token — demo fixtures."}

    if resource in ("issues", "pulls", "branches", "ci"):
        # Resolve into owner/repo (split on "/" from a repo arg, or owner param)
        repo_arg = repo or ""
        if "/" in repo_arg:
            o, r = repo_arg.split("/", 1)
        else:
            o, r = owner or "ai-agency", repo_arg or "heer-core"

        if resource == "issues":
            if is_live:
                res = _request(f"/repos/{o}/{r}/issues?state=open&per_page=30")
                if res.get("ok") is False:
                    return res
                return {"ok": True, "repo": f"{o}/{r}", "issues": res,
                        "count": len(res), "source": "github_api_known"}
            return {"ok": True, **_demo_issue(f"{o}/{r}")}

        if resource == "pulls":
            if is_live:
                res = _request(f"/repos/{o}/{r}/pulls?state=open&per_page=30")
                if res.get("ok") is False:
                    return res
                return {"ok": True, "repo": f"{o}/{r}", "pull_requests": res,
                        "count": len(res), "source": "github_api_known"}
            return {"ok": True, **_demo_prs(f"{o}/{r}")}

        if resource == "branches":
            if is_live:
                res = _request(f"/repos/{o}/{r}/branches?per_page=100")
                if res.get("ok") is False:
                    return res
                return {"ok": True, "repo": f"{o}/{r}", "branches": res,
                        "count": len(res), "source": "github_api_known"}
            return {"ok": True, **_demo_branches(f"{o}/{r}")}

        if resource == "ci":
            if is_live:
                res = _request(f"/repos/{o}/{r}/actions/runs?per_page=10")
                if res.get("ok") is False:
                    return res
                runs = res.get("workflow_runs", res)
                return {"ok": True, "repo": f"{o}/{r}", "runs": runs,
                        "source": "github_api_known"}
            return {"ok": True, "repo": f"{o}/{r}", "runs": _DEMO_CI,
                    "source": "demo_fixture",
                    "note": "HEER_EXECUTION=0 or no token — demo fixtures."}

    return {"ok": False, "error": f"Unknown github_read resource '{resource}'."}


# ---------------------------------------------------------------------------
# github_write (L2)
# ---------------------------------------------------------------------------


def github_write(action="issue", repo=None, number=None, title="", body="",
                 draft=True, owner=None, token=None, business_id=None):
    """Write GitHub data. action: issue | pr.

    Requires GITHUB_TOKEN + HEER_EXECUTION=1. Otherwise returns a dry-run
    artifact with known/inferred labels.
    """
    tok = token or _token()
    repo_arg = repo or ""
    if "/" in repo_arg:
        o, r = repo_arg.split("/", 1)
    else:
        o, r = owner or "ai-agency", repo_arg or "heer-core"

    if not tok:
        return {
            "ok": True, "action": action, "repo": f"{o}/{r}",
            "status": "dry_run", "would_execute": True,
            "summary": f"Would {action} on {o}/{r}: {title or body or '(no text)'}",
            "note": "No GITHUB_TOKEN configured — dry-run only.",
            "labels": {"known": [], "inferred": [f"{action} intent"]},
        }

    if not _execution_enabled():
        return {
            "ok": True, "action": action, "repo": f"{o}/{r}",
            "status": "dry_run", "would_execute": True,
            "summary": f"Would {action} on {o}/{r}: {title or body or '(no text)'}",
            "note": "HEER_EXECUTION=0 — dry-run only. Set HEER_EXECUTION=1 + approval (L2) to execute.",
            "labels": {"known": ["token present"], "inferred": [f"{action} intent"]},
        }

    if action == "issue":
        if number:
            # Comment on existing issue
            if not body:
                return {"ok": False, "error": "body required to comment on an issue."}
            res = _request(f"/repos/{o}/{r}/issues/{number}/comments",
                           method="POST",
                           body=json.dumps({"body": body}).encode("utf-8"))
            if isinstance(res, dict) and res.get("ok") is False:
                return res
            return {"ok": True, "action": "issue_comment",
                    "repo": f"{o}/{r}", "issue": number,
                    "comment_id": res.get("id") if isinstance(res, dict) else None,
                    "status": "executed", "source": "github_api_known"}
        # Create issue
        if not title:
            return {"ok": False, "error": "title required to create an issue."}
        res = _request(f"/repos/{o}/{r}/issues", method="POST",
                       body=json.dumps({"title": title, "body": body}).encode("utf-8"))
        if isinstance(res, dict) and res.get("ok") is False:
            return res
        return {"ok": True, "action": "issue_create", "repo": f"{o}/{r}",
                "issue": res.get("number") if isinstance(res, dict) else None,
                "status": "executed", "source": "github_api_known"}

    if action == "pr":
        if number:
            # Update PR (e.g., mark ready / request review)
            if not body:
                return {"ok": False, "error": "body required for PR update."}
            res = _request(f"/repos/{o}/{r}/pulls/{number}", method="PATCH",
                           body=json.dumps({"body": body}).encode("utf-8"))
            if isinstance(res, dict) and res.get("ok") is False:
                return res
            return {"ok": True, "action": "pr_update", "repo": f"{o}/{r}",
                    "pr": number, "status": "executed", "source": "github_api_known"}
        # Open draft PR
        if not title:
            return {"ok": False, "error": "title required to open a PR."}
        head = data.env("GITHUB_HEAD", None) or "feature/heer-task"
        base = data.env("GITHUB_BASE", None) or "main"
        res = _request(f"/repos/{o}/{r}/pulls", method="POST",
                       body=json.dumps({
                           "title": title, "body": body,
                           "head": head, "base": base, "draft": draft,
                       }).encode("utf-8"))
        if isinstance(res, dict) and res.get("ok") is False:
            return res
        return {"ok": True, "action": "pr_create", "repo": f"{o}/{r}",
                "pr": res.get("number") if isinstance(res, dict) else None,
                "status": "executed", "source": "github_api_known"}

    return {"ok": False, "error": f"Unknown github_write action '{action}'."}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def call_github_tool(name, args=None, business_id=None):
    args = args or {}
    if name == "github_read":
        r = github_read(repo=args.get("repo"), resource=args.get("resource", "repos"),
                        owner=args.get("owner"), token=args.get("token"), business_id=business_id)
        return {"tool": name, **r}
    if name == "github_write":
        r = github_write(action=args.get("action", "issue"), repo=args.get("repo"),
                         number=args.get("number"), title=args.get("title") or "",
                         body=args.get("body") or "", draft=args.get("draft", True),
                         owner=args.get("owner"), token=args.get("token"), business_id=business_id)
        return {"tool": name, **r}
    return {"tool": name, "ok": False, "error": f"Unknown github tool '{name}'."}


GITHUB_TOOLS = {
    "github_read": {
        "desc": "Read GitHub data: repos, issues, pull requests, branches, CI status.",
        "params": {
            "resource": "repos|issues|pulls|branches|ci",
            "repo": "owner/repo (optional; default ai-agency/heer-core)",
        },
        "fn": lambda name, args, business_id=None: call_github_tool(name, args, business_id),
    },
    "github_write": {
        "desc": "Create/comment on issues, open/update draft PRs (L2 approval).",
        "params": {
            "action": "issue|pr",
            "repo": "owner/repo",
            "number": "issue/PR number (optional)",
            "title": "string",
            "body": "string",
            "draft": "bool (default true)",
        },
        "fn": lambda name, args, business_id=None: call_github_tool(name, args, business_id),
    },
}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _self_test():
    print("HEER GitHub Agent self-test\n" + "-" * 40)
    results = []

    # Scenario 1: read repos (demo fixtures)
    r1 = github_read(resource="repos", owner=None)
    ok1 = r1.get("ok") is True and r1.get("count", 0) >= 1 and "repos" in r1
    ok1 = ok1 and r1.get("source") in ("demo_fixture", "github_api_known")
    results.append(("github_read repos", ok1))

    # Scenario 2: read issues for a repo
    r2 = github_read(repo="ai-agency/heer-core", resource="issues")
    ok2 = r2.get("ok") is True and "issues" in r2 and r2.get("repo") == "ai-agency/heer-core"
    results.append(("github_read issues", ok2))

    # Scenario 3: read branches
    r3 = github_read(repo="client-portal", owner="ai-agency", resource="branches")
    ok3 = r3.get("ok") is True and "branches" in r3 and len(r3.get("branches", [])) >= 1
    results.append(("github_read branches", ok3))

    # Scenario 4: read CI status
    r4 = github_read(repo="ai-agency/heer-core", resource="ci")
    ok4 = r4.get("ok") is True and "runs" in r4
    results.append(("github_read ci", ok4))

    # Scenario 5: unknown resource fails cleanly
    r5 = github_read(resource="nonsense")
    ok5 = r5.get("ok") is False and "Unknown" in r5.get("error", "")
    results.append(("github_read unknown resource fails cleanly", ok5))

    # Scenario 6: write dry-run (no token) — must not execute
    r6 = github_write(action="issue", repo="ai-agency/heer-core", title="Test issue",
                      body="Self-test dry-run.")
    ok6 = (r6.get("ok") is True and r6.get("status") == "dry_run"
           and r6.get("would_execute") is True)
    results.append(("github_write dry-run safety (no token)", ok6))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())