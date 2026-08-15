#!/usr/bin/env python3
"""main.py — HTTP server + API for HEER.

Stdlib only. Serves the UI and the graph API.
Voice endpoints (/api/speak, /api/listen) are included.

Run:  python3 -m agent.main
"""

import json
import os
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import approvals
from . import audit
from . import business
from . import data
from . import execution_engine
from . import heer
from . import mission
from . import mission_engine
from . import orchestrator
from . import registry
from . import task_graph
from . import tools
from . import voice
from . import vault
from .chat import respond

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE, "ui")
PORT = int(os.environ.get("HEER_PORT", "8000"))

# Pre-build the offline macOS speech helper so the first /api/listen
# request doesn't pay a multi-second compile cost.
voice.prebuild_asr()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _vault():
    """The active business's vault (lazily built + cached per business).

    Returns an empty Vault when no business is active so callers can
    always treat the result as a Vault (never None).
    """
    v = vault.get_vault()
    if v is None:
        return vault.Vault()
    return v


def node_payload(node):
    """Lightweight node for the graph payload (no full text)."""
    v = _vault()
    return {
        "id": node["id"],
        "title": node["title"],
        "type": node["type"],
        "rel": node["rel"],
        "size": node["size"],
        "degree": len(v.neighbors(node["id"])) if v else 0,
    }


def graph_payload():
    v = _vault()
    return {
        "nodes": [node_payload(n) for n in v.nodes.values()],
        "links": [{"source": a, "target": b} for a, b in v.links],
        "demo": data.demo_mode(),
        "counts": {
            t: sum(1 for n in v.nodes.values() if n["type"] == t)
            for t in sorted({n["type"] for n in v.nodes.values()})
        },
    }


def node_detail(node_id):
    v = _vault()
    node = v.nodes.get(node_id)
    if not node:
        return None
    return {
        "id": node["id"],
        "title": node["title"],
        "type": node["type"],
        "rel": node["rel"],
        "text": node["text"],
        "size": node["size"],
        "neighbors": [v.nodes[n]["title"] for n in v.neighbors(node_id)],
    }


def search_payload(query, limit=8):
    v = _vault()
    results = v.search(query, limit=limit)
    return [
        {
            "id": n["id"],
            "title": n["title"],
            "type": n["type"],
            "rel": n["rel"],
            "snippet": n["text"][:300],
        }
        for n in results
    ]


def parse_multipart(content_type, body):
    """Return {field_name: (value_or_bytes, filename_or_None)}.

    Minimal multipart/form-data parser (stdlib only). Supports the parts
    the voice endpoints send: JSON 'text' fields and one binary 'audio'.
    """
    m = re.search(r'boundary="?([^";]+)"?', content_type or "")
    if not m:
        return {}
    boundary = b"--" + m.group(1).encode("utf-8")
    parts = {}
    for raw in body.split(boundary):
        raw = raw.strip(b"\r\n")
        if not raw or raw in (b"--", b""):
            continue
        head, _, content = raw.partition(b"\r\n\r\n")
        disp = re.search(rb'name="([^"]+)"', head)
        fname = re.search(rb'filename="([^"]*)"', head)
        if not disp:
            continue
        name = disp.group(1).decode("utf-8")
        parts[name] = (content, fname.group(1).decode("utf-8") if fname else None)
    return parts


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write("[heer] %s\n" % (format % args))

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self._send_json({"error": "not found"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # ---- Business API ----
        if path == "/api/businesses":
            self._send_json(
                {
                    "businesses": business.list_businesses(),
                    "current": business.current_business(),
                }
            )
            return

        if path == "/api/business/current":
            self._send_json(business.current_business())
            return

        # ---- HEER command center API ----
        if path == "/api/status":
            self._send_json(heer.status_payload())
            return

        if path == "/api/system":
            v = _vault()
            self._send_json(
                {
                    "demo": data.demo_mode(),
                    "model": "multi-model",
                    "tts": voice.speak_capability(),
                    "asr": voice.asr_configured(),
                    "elevenlabs": bool(data.elevenlabs_key()),
                    "edge_tts": voice.speak_capability() == "edge",
                    "nodes": len(v.nodes),
                    "links": len(v.links),
                    "business": business.current_business(),
                }
            )
            return

        if path == "/api/briefing":
            self._send_json(heer.briefing_payload())
            return

        if path == "/api/agents":
            self._send_json(heer.agents_payload())
            return

        if path == "/api/skills":
            self._send_json(heer.skills_payload())
            return

        if path == "/api/learning":
            self._send_json(heer.learning_payload())
            return

        if path == "/api/opportunities":
            self._send_json(heer.opportunities_payload())
            return

        if path == "/api/activity":
            self._send_json(heer.activity_payload())
            return

        if path == "/api/clients":
            self._send_json(heer.clients_payload())
            return

        if path == "/api/projects":
            self._send_json(heer.projects_payload())
            return

        if path == "/api/business":
            self._send_json(heer.business_payload())
            return

        if path == "/api/automations":
            self._send_json(heer.automations_payload())
            return

        if path == "/api/network":
            self._send_json(heer.network_payload())
            return

        # ---- Operational orchestration / registry / approvals / audit ----
        if path == "/api/registry":
            self._send_json(registry.registry_payload())
            return

        if path == "/api/approvals":
            self._send_json(approvals.approvals_payload())
            return

        if path == "/api/executions":
            self._send_json(audit.executions_payload())
            return

        # ---- Mission & Task-Graph API (Phase 3.10) ----
        if path == "/api/missions":
            self._send_json(mission.missions_payload())
            return

        if path == "/api/tools":
            self._send_json({"tools": tools.tool_descriptions()})
            return

        if path.startswith("/api/missions/"):
            mid = urllib.parse.unquote(path[len("/api/missions/"):])
            payload = mission.mission_payload(mid)
            if payload is None:
                self._send_json({"error": "mission not found"}, 404)
                return
            self._send_json(payload)
            return

        # ---- Mission Engine API (Phase 3.1 — business-level missions) ----
        if path == "/api/mission-engine/state-machine":
            self._send_json({"ok": True, "state_machine": mission_engine.state_machine()})
            return

        if path == "/api/mission-engine/missions":
            status_filter = query.get("status", [""])[0].strip() or None
            try:
                limit = int(query.get("limit", ["50"])[0])
            except (TypeError, ValueError):
                limit = 50
            payload = mission_engine.list_missions(status=status_filter, limit=limit)
            if not payload["ok"]:
                self._send_json({"error": payload["error"]}, 400)
                return
            self._send_json(payload)
            return

        if path.startswith("/api/mission-engine/missions/"):
            # Phase 3.1 single-mission GET: only exact /missions/{id}
            rest = path[len("/api/mission-engine/missions/"):]
            if "/" not in rest:
                mid = urllib.parse.unquote(rest)
                m = mission_engine.get_mission(mid)
                if m is None:
                    self._send_json({"error": "mission not found"}, 404)
                    return
                self._send_json({"ok": True, "mission": m})
                return

        # ---- Parallel Execution Engine API (Phase 3.3) ----
        if path == "/api/execution/executions":
            self._send_json(execution_engine.list_executions(
                mission_id=query.get("mission_id", [None])[0],
                task_id=query.get("task_id", [None])[0],
                status=query.get("status", [None])[0],
                limit=int(query.get("limit", ["100"])[0]),
            ))
            return

        if path == "/api/execution/events":
            self._send_json(execution_engine.list_events(
                mission_id=query.get("mission_id", [None])[0],
                execution_id=query.get("execution_id", [None])[0],
                event_type=query.get("event_type", [None])[0],
                limit=int(query.get("limit", ["200"])[0]),
            ))
            return

        if path == "/api/execution/metrics":
            self._send_json(execution_engine.metrics())
            return

        if path == "/api/execution/scheduler":
            self._send_json(execution_engine.scheduler_status())
            return

        # ---- Task Graph / DAG API (Phase 3.2 — tasks belong to missions) ----
        prefix = "/api/mission-engine/missions/"
        if path.startswith(prefix):
            rest = path[len(prefix):]
            parts = rest.split("/")
            if len(parts) == 2 and all(p for p in parts):
                mid = urllib.parse.unquote(parts[0])
                kind = urllib.parse.unquote(parts[1])
                if kind == "tasks":
                    # GET /api/mission-engine/missions/{mission_id}/tasks
                    payload = task_graph.list_tasks(mid)
                    if not payload["ok"]:
                        self._send_json({"error": payload["error"]}, 404)
                        return
                    self._send_json(payload)
                    return
            if len(parts) == 3:
                mid = urllib.parse.unquote(parts[0])
                kind = urllib.parse.unquote(parts[1])
                tid = urllib.parse.unquote(parts[2])
                if kind == "tasks" and tid:
                    # GET /api/mission-engine/missions/{mission_id}/tasks/{task_id}
                    task = task_graph.get_task(mid, tid)
                    if task is None:
                        self._send_json({"error": "task not found"}, 404)
                        return
                    self._send_json({"ok": True, "task": task})
                    return
                if kind == "tasks" and tid == "state-machine":
                    self._send_json({"ok": True,
                                     "state_machine": task_graph.task_state_machine()})
                    return
                if kind == "graph":
                    # GET /api/mission-engine/missions/{mission_id}/graph/{action}
                    action = tid
                    if action == "validate":
                        payload = task_graph.validate_graph(mid, audit_failure=True)
                        self._send_json(payload)
                        return
                    if action == "ready":
                        payload = task_graph.ready_tasks(mid)
                        if not payload["ok"]:
                            self._send_json({"error": payload["error"]}, 404)
                            return
                        self._send_json(payload)
                        return
                    if action == "blocked":
                        payload = task_graph.blocked_tasks(mid)
                        if not payload["ok"]:
                            self._send_json({"error": payload["error"]}, 404)
                            return
                        self._send_json(payload)
                        return
                    if action == "state-machine":
                        self._send_json({"ok": True,
                                         "state_machine": task_graph.task_state_machine()})
                        return

        # ---- Knowledge graph API ----
        if path == "/api/graph":
            self._send_json(graph_payload())
            return

        if path == "/api/search":
            q = query.get("q", [""])[0].strip()
            if not q:
                self._send_json({"results": []})
                return
            self._send_json({"results": search_payload(q)})
            return

        if path.startswith("/api/node/"):
            node_id = urllib.parse.unquote(path[len("/api/node/"):])
            detail = node_detail(node_id)
            if detail is None:
                self._send_json({"error": "not found"}, 404)
                return
            self._send_json(detail)
            return

        if path == "/api/hubs":
            v = _vault()
            hubs = [
                {"id": nid, "title": v.nodes[nid]["title"], "degree": deg}
                for nid, deg in v.hubs(10)
            ]
            self._send_json({"hubs": hubs})
            return

        if path == "/api/path":
            v = _vault()
            a = query.get("a", [""])[0]
            b = query.get("b", [""])[0]
            path_ids = v.shortest_path(a, b)
            self._send_json(
                {
                    "path": path_ids,
                    "titles": [v.nodes[n]["title"] for n in (path_ids or [])],
                }
            )
            return

        # Static files
        if path == "/" or path == "":
            path = "/index.html"
        rel = path.lstrip("/")
        full = os.path.normpath(os.path.join(UI_DIR, rel))
        if not full.startswith(UI_DIR):
            self._send_json({"error": "forbidden"}, 403)
            return
        ext = os.path.splitext(full)[1].lower()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }.get(ext, "application/octet-stream")
        self._send_file(full, ctype)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/business/switch":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                business_id = (body.get("business_id") or "").strip()
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not business_id:
                self._send_json({"error": "business_id required"}, 400)
                return
            b = business.switch_business(business_id)
            if b is None:
                self._send_json({"error": f"Business '{business_id}' not found."}, 404)
                return
            self._send_json({"ok": True, "business": b})
            return

        if path == "/api/business/add":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            name = (body.get("name") or "").strip()
            if not name:
                self._send_json({"error": "name required"}, 400)
                return
            b = business.add_business(
                name=name,
                business_type=(body.get("type") or "").strip(),
                data_root=(body.get("data_root") or "").strip(),
                icon=(body.get("icon") or "🏢").strip(),
                color=(body.get("color") or "#4d9fff").strip(),
                tagline=(body.get("tagline") or "").strip(),
            )
            if b is None:
                self._send_json({"error": "Could not add business."}, 400)
                return
            self._send_json({"ok": True, "business": b})
            return

        if path == "/api/business/update":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            business_id = (body.get("business_id") or "").strip()
            if not business_id:
                self._send_json({"error": "business_id required"}, 400)
                return
            fields = {k: v for k, v in body.items() if k != "business_id"}
            b = business.update_business(business_id, **fields)
            if b is None:
                self._send_json({"error": f"Business '{business_id}' not found."}, 404)
                return
            self._send_json({"ok": True, "business": b})
            return

        if path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                message = (body.get("message") or "").strip()
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not message:
                self._send_json({"error": "empty message"}, 400)
                return
            cur = business.current_business()
            self._send_json(respond(message, business_id=cur["id"] if cur else None))
            return

        if path == "/api/missions":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                name = (body.get("name") or "").strip()
                goal = (body.get("goal") or "").strip()
                task_defs = body.get("tasks") or []
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not goal:
                self._send_json({"error": "goal required"}, 400)
                return
            m = mission.build_mission(name or goal[:60], goal, task_defs)
            self._send_json({"ok": True, "mission": m}, 201)
            return

        # ---- Mission Engine API (Phase 3.1 — business-level missions) ----
        if path == "/api/mission-engine/missions":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            r = mission_engine.create_mission(
                objective=body.get("objective"),
                priority=body.get("priority", "medium"),
                created_by=body.get("created_by", "HEER"),
                context=body.get("context"),
                constraints=body.get("constraints"),
                metadata=body.get("metadata"),
            )
            if not r["ok"]:
                self._send_json({"error": r["error"]}, 400)
                return
            self._send_json(r, 201)
            return

        if path.startswith("/api/mission-engine/missions/"):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            rest = path[len("/api/mission-engine/missions/"):]
            parts = rest.split("/")

            # POST /api/mission-engine/missions/{id}/transition (Phase 3.1)
            if len(parts) == 2 and parts[1] == "transition":
                mid = urllib.parse.unquote(parts[0])
                target = (body.get("status") or "").strip()
                if not target:
                    self._send_json({"error": "status (target state) required"}, 400)
                    return
                r = mission_engine.transition(
                    mid, target, result=body.get("result"),
                    error=body.get("error"),
                )
                if not r["ok"]:
                    status = 404 if "not found" in r["error"] else 409
                    self._send_json({"error": r["error"]}, status)
                    return
                self._send_json(r)
                return

            # ---- Task Graph / DAG API (Phase 3.2) ----
            if len(parts) == 2 and parts[1] == "tasks":
                mid = urllib.parse.unquote(parts[0])
                # POST /api/mission-engine/missions/{mission_id}/tasks
                r = task_graph.create_task(
                    mission_id=mid,
                    name=body.get("name"),
                    description=body.get("description"),
                    priority=body.get("priority", "medium"),
                    assigned_agent=body.get("assigned_agent"),
                    dependencies=body.get("dependencies"),
                    input=body.get("input"),
                    metadata=body.get("metadata"),
                )
                if not r["ok"]:
                    status = 404 if "not found" in r["error"] else 400
                    self._send_json({"error": r["error"]}, status)
                    return
                self._send_json(r, 201)
                return

            # POST /api/mission-engine/missions/{mission_id}/graph/validate
            if len(parts) == 3 and parts[1] == "graph" and parts[2] == "validate":
                mid = urllib.parse.unquote(parts[0])
                self._send_json(task_graph.validate_graph(mid, audit_failure=True))
                return

            # POST /api/mission-engine/missions/{mission_id}/tasks/{task_id}/transition
            if len(parts) == 4 and parts[1] == "tasks" and parts[3] == "transition":
                mid = urllib.parse.unquote(parts[0])
                tid = urllib.parse.unquote(parts[2])
                r = task_graph.transition_task(
                    mission_id=mid,
                    task_id=tid,
                    target_status=body.get("status"),
                    output=body.get("output"),
                    error=body.get("error"),
                )
                if not r["ok"]:
                    status = 404 if "not found" in r["error"] else 409
                    self._send_json({"error": r["error"]}, status)
                    return
                self._send_json(r)
                return

            self._send_json({"error": "not found"}, 404)
            return

        # ---- Parallel Execution Engine API (Phase 3.3) ----
        if path == "/api/execution/config":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            allowed = {"max_concurrent", "per_mission", "lease_ttl", "backoff_base",
                       "backoff_cap", "poll", "task_timeout", "mission_timeout"}
            kw = {k: v for k, v in body.items() if k in allowed}
            if not kw:
                self._send_json({"error": "no valid config keys supplied"}, 400)
                return
            self._send_json(execution_engine.configure(**kw))
            return

        ep = "/api/execution/missions/"
        if path.startswith(ep):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            rest = path[len(ep):]
            parts = rest.split("/")
            mid = urllib.parse.unquote(parts[0]) if parts else ""
            if not mid:
                self._send_json({"error": "mission_id required"}, 400)
                return
            if len(parts) == 2 and parts[1] == "start":
                self._send_json(execution_engine.start_mission(
                    mid, max_concurrent=body.get("max_concurrent")))
                return
            if len(parts) == 2 and parts[1] == "pause":
                self._send_json(execution_engine.pause_mission(mid))
                return
            if len(parts) == 2 and parts[1] == "resume":
                self._send_json(execution_engine.resume_mission(mid))
                return
            if len(parts) == 2 and parts[1] == "stop":
                self._send_json(execution_engine.stop_mission(mid))
                return
            if len(parts) == 4 and parts[1] == "tasks" and parts[3] == "cancel":
                tid = urllib.parse.unquote(parts[2])
                self._send_json(execution_engine.cancel_task(mid, tid))
                return
            if len(parts) == 4 and parts[1] == "tasks" and parts[3] == "retry":
                tid = urllib.parse.unquote(parts[2])
                self._send_json(execution_engine.retry_task(mid, tid, reason=body.get("reason", "manual")))
                return
            self._send_json({"error": "not found"}, 404)
            return

        if path == "/api/execution/heartbeat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                eid = (body.get("execution_id") or "").strip()
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not eid:
                self._send_json({"error": "execution_id required"}, 400)
                return
            execution_engine.heartbeat(eid, ttl=body.get("ttl"))
            self._send_json({"ok": True})
            return

        if path == "/api/orchestrate":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                message = (body.get("message") or "").strip()
                business_id = (body.get("business_id") or "").strip() or None
                request_id = (body.get("request_id") or "").strip()
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not message:
                self._send_json({"error": "message required"}, 400)
                return
            self._send_json(
                orchestrator.handle(message, business_id=business_id, request_id=request_id)
            )
            return

        if path == "/api/approvals/respond":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                approval_id = (body.get("approval_id") or "").strip()
                decision = (body.get("decision") or "").strip()
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not approval_id or decision not in ("approved", "denied"):
                self._send_json(
                    {"error": "approval_id and decision ('approved'|'denied') required"}, 400
                )
                return
            result = approvals.respond(approval_id, decision)
            if result is None:
                self._send_json({"error": "approval not found or already responded"}, 404)
                return
            self._send_json({"ok": True, **result})
            return

        if path == "/api/speak":
            ctype = self.headers.get("Content-Type", "")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            if not raw:
                self._send_json({"error": "empty request"}, 400)
                return
            if ctype.startswith("multipart/form-data"):
                parts = parse_multipart(ctype, raw)
                text = (parts.get("text") or (b"", None))[0]
                if isinstance(text, bytes):
                    text = text.decode("utf-8")
                voice_id = (parts.get("voice_id") or (b"", None))[0]
                if isinstance(voice_id, bytes):
                    voice_id = voice_id.decode("utf-8")
            else:
                try:
                    body = json.loads(raw.decode("utf-8"))
                    text = (body.get("text") or "").strip()
                    voice_id = body.get("voice_id")
                except Exception:
                    self._send_json({"error": "bad request"}, 400)
                    return
            if not text:
                self._send_json({"error": "empty text"}, 400)
                return
            audio, audio_type = voice.speak(text, voice_id or None)
            if audio is None:
                self._send_json({"error": "Text-to-speech unavailable (set ELEVENLABS_API_KEY or use macOS)."}, 501)
                return
            self.send_response(200)
            self.send_header("Content-Type", audio_type)
            self.send_header("Content-Length", str(len(audio)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(audio)
            return

        if path == "/api/listen":
            ctype = self.headers.get("Content-Type", "")
            if not ctype.startswith("multipart/form-data"):
                self._send_json({"error": "multipart/form-data required"}, 400)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                parts = parse_multipart(ctype, self.rfile.read(length))
            except Exception:
                self._send_json({"error": "bad request"}, 400)
                return
            audio, fname = parts.get("audio", (None, None))
            if not audio:
                self._send_json({"error": "missing audio"}, 400)
                return
            mime = "audio/webm"
            if fname:
                ext_map = {
                    ".wav": "audio/wav",
                    ".mp3": "audio/mpeg",
                    ".ogg": "audio/ogg",
                    ".webm": "audio/webm",
                    ".m4a": "audio/mp4",
                    ".flac": "audio/flac",
                }
                mime = ext_map.get(os.path.splitext(fname)[1].lower(), "audio/webm")
            text = voice.transcribe(audio, mime=mime)
            if text is None:
                self._send_json({"error": "Speech-to-text unavailable or failed."}, 501)
                return
            self._send_json({"text": text})
            return

        self._send_json({"error": "not implemented"}, 501)


def main():
    print(f"HEER running at http://localhost:{PORT}")
    print(f"Demo mode: {data.demo_mode()}")
    b = business.current_business()
    if b:
        print(f"Active business: {b['name']} ({b['id']})")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()