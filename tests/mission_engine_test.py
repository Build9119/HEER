#!/usr/bin/env python3
"""Unit tests for the HEER Mission Engine (Phase 3.1).

Run:  python3 tests/mission_engine_test.py            (stdlib unittest)
      python3 -m pytest tests/mission_engine_test.py  (if pytest present)
"""

import os
import sys
import unittest

# Allow running directly from anywhere: add repo root to sys.path.
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from agent import mission_engine  # noqa: E402


class MissionEngineModelTests(unittest.TestCase):
    def test_mission_fields_persist(self):
        r = mission_engine.create_mission(
            "Ship the client portal",
            priority="critical",
            created_by="Pankaj",
            context={"client": "Acme", "size": 3},
            constraints=["no overtime", "budget 30k"],
            metadata={"track": "delivery"},
        )
        self.assertTrue(r["ok"])
        m = r["mission"]
        self.assertIn("mission_id", m)
        self.assertEqual(m["objective"], "Ship the client portal")
        self.assertEqual(m["status"], "CREATED")
        self.assertEqual(m["priority"], "critical")
        self.assertEqual(m["created_by"], "Pankaj")
        self.assertEqual(m["context"], {"client": "Acme", "size": 3})
        self.assertEqual(m["constraints"], ["no overtime", "budget 30k"])
        self.assertEqual(m["metadata"], {"track": "delivery"})
        self.assertIsNone(m["result"])
        self.assertIsNone(m["error"])
        self.assertGreaterEqual(m["updated_at"], m["created_at"])

    def test_default_priority_and_created_by(self):
        r = mission_engine.create_mission("Default fields")
        self.assertTrue(r["ok"])
        m = r["mission"]
        self.assertEqual(m["priority"], "medium")
        self.assertEqual(m["created_by"], "HEER")
        self.assertEqual(m["context"], None)

    def test_get_mission_returns_none_for_unknown(self):
        self.assertIsNone(mission_engine.get_mission("mis_nope"))
        self.assertIsNone(mission_engine.get_mission(""))
        self.assertIsNone(mission_engine.get_mission(None))

    def test_list_missions_and_status_counts(self):
        r1 = mission_engine.create_mission("List demo A")
        r2 = mission_engine.create_mission("List demo B", priority="high")
        lst = mission_engine.list_missions()
        self.assertTrue(lst["ok"])
        self.assertGreaterEqual(lst["total"], 2)
        ids = {m["mission_id"] for m in lst["missions"]}
        self.assertIn(r1["mission"]["mission_id"], ids)
        self.assertIn(r2["mission"]["mission_id"], ids)
        # counts dictionary covers every valid status
        for s in mission_engine.VALID_STATUSES:
            self.assertIn(s, lst["counts"])

    def test_list_filter_by_status(self):
        r = mission_engine.create_mission("Filter demo")
        mission_engine.plan_mission(r["mission"]["mission_id"])
        lst = mission_engine.list_missions(status="PLANNED")
        self.assertTrue(lst["ok"])
        self.assertTrue(all(m["status"] == "PLANNED" for m in lst["missions"]))
        # invalid status filter rejected
        bad = mission_engine.list_missions(status="BOGUS")
        self.assertFalse(bad["ok"])

    def test_limits_are_clamped(self):
        lst = mission_engine.list_missions(limit=0)
        self.assertTrue(lst["ok"])
        self.assertEqual(len(lst["missions"]), 0)
        lst2 = mission_engine.list_missions(limit=999999)
        self.assertTrue(lst2["ok"])
        self.assertLessEqual(len(lst2["missions"]), 200)


class MissionEngineValidationTests(unittest.TestCase):
    def test_objective_required_and_length(self):
        self.assertFalse(mission_engine.create_mission("")["ok"])
        self.assertFalse(mission_engine.create_mission("   ")["ok"])
        self.assertFalse(mission_engine.create_mission(None)["ok"])
        self.assertFalse(
            mission_engine.create_mission(
                "x" * (mission_engine.MAX_OBJECTIVE + 1)
            )["ok"]
        )

    def test_priority_validation(self):
        ok = mission_engine.create_mission("ok", priority="high")
        self.assertTrue(ok["ok"])
        # case-insensitive
        ok2 = mission_engine.create_mission("ok2", priority="CRITICAL")
        self.assertTrue(ok2["ok"])
        # invalid
        bad = mission_engine.create_mission("bad", priority="urgent")
        self.assertFalse(bad["ok"])
        bad2 = mission_engine.create_mission("bad2", priority=123)
        self.assertFalse(bad2["ok"])

    def test_json_serializable_validation(self):
        self.assertFalse(mission_engine.create_mission("x", metadata=object())["ok"])
        self.assertFalse(mission_engine.create_mission("x", context=object())["ok"])
        self.assertFalse(mission_engine.create_mission("x", constraints=object())["ok"])
        # state transition result must also be serializable
        r = mission_engine.create_mission("json check")
        mid = r["mission"]["mission_id"]
        mission_engine.plan_mission(mid)
        mission_engine.ready_mission(mid)
        mission_engine.start_mission(mid)
        bad = mission_engine.complete_mission(mid, result=object())
        self.assertFalse(bad["ok"])

    def test_sql_injection_safe(self):
        r = mission_engine.create_mission("x'; DROP TABLE missions; --")
        self.assertTrue(r["ok"])
        # mission still readable (table wasn't dropped)
        self.assertIsNotNone(mission_engine.get_mission(r["mission"]["mission_id"]))
        # filtering by injected value matches nothing instead of crashing
        lst = mission_engine.list_missions(status="x'; DROP TABLE missions; --")
        self.assertFalse(lst["ok"])


class MissionEngineStateMachineTests(unittest.TestCase):
    def test_state_machine_shape(self):
        sm = mission_engine.state_machine()
        self.assertIn("CREATED", sm)
        self.assertIn("COMPLETED", sm)
        self.assertIn("FAILED", sm)
        self.assertIn("CANCELLED", sm)
        # terminal states have no outgoing transitions
        self.assertEqual(sm["COMPLETED"], [])
        self.assertEqual(sm["FAILED"], [])
        self.assertEqual(sm["CANCELLED"], [])

    def test_can_transition_rules(self):
        tests = [
            ("CREATED", "PLANNED", True),
            ("CREATED", "CANCELLED", True),
            ("CREATED", "READY", False),
            ("CREATED", "RUNNING", False),
            ("CREATED", "COMPLETED", False),
            ("PLANNED", "READY", True),
            ("PLANNED", "CANCELLED", True),
            ("PLANNED", "RUNNING", False),
            ("READY", "RUNNING", True),
            ("READY", "CANCELLED", True),
            ("READY", "PLANNED", False),
            ("RUNNING", "PAUSED", True),
            ("RUNNING", "COMPLETED", True),
            ("RUNNING", "FAILED", True),
            ("RUNNING", "CANCELLED", True),
            ("RUNNING", "READY", False),
            ("PAUSED", "RUNNING", True),
            ("PAUSED", "CANCELLED", True),
            ("PAUSED", "COMPLETED", False),
            ("COMPLETED", "CANCELLED", False),
            ("FAILED", "RETRY", False),
        ]
        for current, target, expected in tests:
            allowed, _ = mission_engine.can_transition(current, target)
            self.assertEqual(allowed, expected, f"{current} -> {target}")

    def test_unknown_statuses_rejected(self):
        self.assertFalse(mission_engine.can_transition("BOGUS", "CREATED")[0])
        self.assertFalse(mission_engine.can_transition("CREATED", "BOGUS")[0])

    def test_happy_path_lifecycle(self):
        r = mission_engine.create_mission("Happy path")
        mid = r["mission"]["mission_id"]
        self.assertTrue(mission_engine.plan_mission(mid)["ok"])
        self.assertTrue(mission_engine.ready_mission(mid)["ok"])
        st = mission_engine.start_mission(mid)
        self.assertTrue(st["ok"])
        self.assertEqual(st["mission"]["status"], "RUNNING")
        done = mission_engine.complete_mission(mid, result={"ok": True})
        self.assertTrue(done["ok"])
        self.assertEqual(done["mission"]["status"], "COMPLETED")
        self.assertEqual(done["mission"]["result"], {"ok": True})
        self.assertIsNone(done["mission"]["error"])

    def test_pause_resume(self):
        r = mission_engine.create_mission("Pause/resume")
        mid = r["mission"]["mission_id"]
        mission_engine.plan_mission(mid)
        mission_engine.ready_mission(mid)
        mission_engine.start_mission(mid)
        p = mission_engine.pause_mission(mid)
        self.assertTrue(p["ok"])
        self.assertEqual(p["mission"]["status"], "PAUSED")
        res = mission_engine.resume_mission(mid)
        self.assertTrue(res["ok"])
        self.assertEqual(res["mission"]["status"], "RUNNING")

    def test_fail_path(self):
        r = mission_engine.create_mission("Fail path")
        mid = r["mission"]["mission_id"]
        mission_engine.plan_mission(mid)
        mission_engine.ready_mission(mid)
        mission_engine.start_mission(mid)
        # fail requires non-empty error
        self.assertFalse(mission_engine.fail_mission(mid, "")["ok"])
        self.assertFalse(mission_engine.fail_mission(mid, "   ")["ok"])
        f = mission_engine.fail_mission(mid, "API credentials missing")
        self.assertTrue(f["ok"])
        self.assertEqual(f["mission"]["status"], "FAILED")
        self.assertEqual(f["mission"]["error"], "API credentials missing")
        self.assertIsNone(f["mission"]["result"])

    def test_cancel_from_all_active_states(self):
        for state in ("CREATED", "PLANNED", "READY", "RUNNING", "PAUSED"):
            r = mission_engine.create_mission(f"Cancel from {state}")
            mid = r["mission"]["mission_id"]
            if state in ("PLANNED", "READY", "RUNNING", "PAUSED"):
                mission_engine.plan_mission(mid)
            if state in ("READY", "RUNNING", "PAUSED"):
                mission_engine.ready_mission(mid)
            if state in ("RUNNING", "PAUSED"):
                mission_engine.start_mission(mid)
            if state == "PAUSED":
                mission_engine.pause_mission(mid)
            c = mission_engine.cancel_mission(mid)
            self.assertTrue(c["ok"], f"cancel from {state}")
            self.assertEqual(c["mission"]["status"], "CANCELLED")

    def test_invalid_transitions_rejected(self):
        r = mission_engine.create_mission("Invalid transitions")
        mid = r["mission"]["mission_id"]
        # CREATED cannot jump straight to RUNNING / COMPLETED
        self.assertFalse(mission_engine.transition(mid, "RUNNING")["ok"])
        self.assertFalse(mission_engine.transition(mid, "COMPLETED")["ok"])
        self.assertFalse(mission_engine.transition(mid, "FAILED")["ok"])
        self.assertFalse(mission_engine.transition(mid, "BOGUS")["ok"])
        self.assertFalse(mission_engine.transition(mid, "")["ok"])
        # mission row is untouched after a rejected transition
        self.assertEqual(mission_engine.get_mission(mid)["status"], "CREATED")

    def test_terminal_states_reject_further_transitions(self):
        r = mission_engine.create_mission("Terminal")
        mid = r["mission"]["mission_id"]
        mission_engine.plan_mission(mid)
        mission_engine.ready_mission(mid)
        mission_engine.start_mission(mid)
        self.assertTrue(mission_engine.complete_mission(mid)["ok"])
        # completed -> cancelled is rejected
        self.assertFalse(mission_engine.cancel_mission(mid)["ok"])
        # completed -> failed is rejected
        self.assertFalse(mission_engine.fail_mission(mid, "late failure")["ok"])
        self.assertEqual(mission_engine.get_mission(mid)["status"], "COMPLETED")

    def test_transition_unknown_mission(self):
        r = mission_engine.transition("mis_missing", "PLANNED")
        self.assertFalse(r["ok"])
        self.assertIn("not found", r["error"])

    def test_complete_clears_error_fail_clears_result(self):
        r = mission_engine.create_mission("Result/error cleanup")
        mid = r["mission"]["mission_id"]
        mission_engine.plan_mission(mid)
        mission_engine.ready_mission(mid)
        mission_engine.start_mission(mid)
        f = mission_engine.fail_mission(mid, "boom")
        self.assertEqual(f["mission"]["error"], "boom")
        self.assertIsNone(f["mission"]["result"])

    def test_updated_at_monotonic(self):
        r = mission_engine.create_mission("Monotonic timestamps")
        mid = r["mission"]["mission_id"]
        created = r["mission"]["created_at"]
        r2 = mission_engine.plan_mission(mid)
        self.assertGreaterEqual(r2["mission"]["updated_at"], created)
        r3 = mission_engine.ready_mission(mid)
        self.assertGreaterEqual(r3["mission"]["updated_at"], r2["mission"]["updated_at"])


class MissionEngineApiTest(unittest.TestCase):
    """HTTP-level tests over the live handler (no server process needed)."""

    def setUp(self):
        import json

        import agent.main as main_mod

        self.main_mod = main_mod
        self.json = json

        class FakeWfile:
            def __init__(self):
                self.buf = b""

            def write(self, data):
                self.buf += data

        class _Spoofed(main_mod.Handler):
            def __init__(self, method, path, body=None, ctype="application/json"):
                self.command = method
                self.path = path
                self.rfile = type("R", (), {"read": lambda s, n=-1: (body or b"")})()
                self.headers = type("H", (), {"get": lambda s, k, d=None: ctype if k == "Content-Type" else d})()
                self.wfile = FakeWfile()
                self.server = None
                self.request = None
                self.client_address = ("127.0.0.1", 0)

            def send_response(self, code, message=None):
                self._status = code

            def send_header(self, *args, **kwargs):
                pass

            def end_headers(self):
                pass

        self.Handler = _Spoofed

    def _request(self, method, path, body=None):
        h = self.Handler(method, path, body)
        try:
            if method == "GET":
                self.main_mod.Handler.do_GET(h)
            else:
                self.main_mod.Handler.do_POST(h)
        except Exception:
            self.fail("handler raised")
        payload = self.json.loads(h.wfile.buf.decode("utf-8")) if h.wfile.buf else None
        return getattr(h, "_status", 200), payload

    def test_get_state_machine(self):
        status, payload = self._request("GET", "/api/mission-engine/state-machine")
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("CREATED", payload["state_machine"])

    def test_create_get_list_transition_via_api(self):
        body = self.json.dumps({
            "objective": "API mission",
            "priority": "high",
            "created_by": "tester",
            "context": {"source": "unit test"},
            "metadata": {"suite": "api"},
        }).encode("utf-8")
        status, payload = self._request("POST", "/api/mission-engine/missions", body)
        self.assertEqual(status, 201)
        self.assertTrue(payload["ok"])
        mid = payload["mission"]["mission_id"]

        # GET single
        status, payload = self._request("GET", f"/api/mission-engine/missions/{mid}")
        self.assertEqual(status, 200)
        self.assertEqual(payload["mission"]["mission_id"], mid)
        self.assertEqual(payload["mission"]["status"], "CREATED")

        # GET list
        status, payload = self._request("GET", "/api/mission-engine/missions")
        self.assertEqual(status, 200)
        self.assertTrue(any(m["mission_id"] == mid for m in payload["missions"]))

        # POST transition PLANNED
        status, payload = self._request(
            "POST",
            f"/api/mission-engine/missions/{mid}/transition",
            self.json.dumps({"status": "PLANNED"}).encode("utf-8"),
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["mission"]["status"], "PLANNED")

        # Invalid transition -> 409
        status, payload = self._request(
            "POST",
            f"/api/mission-engine/missions/{mid}/transition",
            self.json.dumps({"status": "RUNNING"}).encode("utf-8"),
        )
        self.assertEqual(status, 409)
        self.assertIn("invalid transition", payload["error"])

        # Transition unknown mission -> 404
        status, payload = self._request(
            "POST",
            "/api/mission-engine/missions/mis_nope/transition",
            self.json.dumps({"status": "PLANNED"}).encode("utf-8"),
        )
        self.assertEqual(status, 404)

    def test_create_validation_via_api(self):
        status, payload = self._request(
            "POST",
            "/api/mission-engine/missions",
            self.json.dumps({"objective": ""}).encode("utf-8"),
        )
        self.assertEqual(status, 400)
        self.assertIn("objective", payload["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)