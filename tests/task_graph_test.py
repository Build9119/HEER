#!/usr/bin/env python3
"""Unit tests for the HEER Task Graph / DAG Engine (Phase 3.2).

Run:  python3 tests/task_graph_test.py            (stdlib unittest)
      python3 -m pytest tests/task_graph_test.py  (if pytest present)
"""

import os
import sys
import unittest

# Allow running directly from anywhere: add repo root to sys.path.
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from agent import mission_engine  # noqa: E402
from agent import task_graph  # noqa: E402


def _fresh_mission(objective="Task Graph test mission"):
    r = mission_engine.create_mission(objective, priority="high",
                                      created_by="task_graph_test")
    assert r["ok"], r.get("error")
    return r["mission"]["mission_id"]


class TaskGraphModelTests(unittest.TestCase):
    def test_task_fields_persist(self):
        mid = _fresh_mission()
        r = task_graph.create_task(
            mid,
            "Research competitors",
            description="Explore the landscape",
            priority="critical",
            assigned_agent="analyst",
            input={"focus": "AI agents"},
            metadata={"track": "intel"},
        )
        self.assertTrue(r["ok"], r.get("error"))
        t = r["task"]
        self.assertIn("task_id", t)
        self.assertEqual(t["mission_id"], mid)
        self.assertEqual(t["name"], "Research competitors")
        self.assertEqual(t["description"], "Explore the landscape")
        self.assertEqual(t["status"], "READY")  # no deps -> ready
        self.assertEqual(t["priority"], "critical")
        self.assertEqual(t["assigned_agent"], "analyst")
        self.assertEqual(t["input"], {"focus": "AI agents"})
        self.assertEqual(t["metadata"], {"track": "intel"})
        self.assertIsNone(t["output"])
        self.assertIsNone(t["error"])
        self.assertEqual(t["dependencies"], [])
        self.assertGreaterEqual(t["updated_at"], t["created_at"])

    def test_task_defaults(self):
        mid = _fresh_mission()
        r = task_graph.create_task(mid, "Default task")
        self.assertTrue(r["ok"])
        t = r["task"]
        self.assertEqual(t["description"], "")
        self.assertEqual(t["priority"], "medium")
        self.assertEqual(t["assigned_agent"], "")
        self.assertEqual(t["dependencies"], [])
        self.assertIsNone(t["input"])
        self.assertIsNone(t["metadata"])

    def test_get_task_returns_none_for_unknown(self):
        mid = _fresh_mission()
        self.assertIsNone(task_graph.get_task(mid, "tsk_nope"))
        self.assertIsNone(task_graph.get_task("mis_nope", "tsk_whatever"))
        self.assertIsNone(task_graph.get_task("", ""))
        self.assertIsNone(task_graph.get_task(None, None))
        self.assertIsNone(task_graph.get_task(mid, None))

    def test_list_tasks_insertion_order_and_ownership(self):
        mid = _fresh_mission()
        t1 = task_graph.create_task(mid, "First")
        t2 = task_graph.create_task(mid, "Second")
        lst = task_graph.list_tasks(mid)
        self.assertTrue(lst["ok"])
        self.assertEqual(lst["total"], 2)
        self.assertEqual([t["task_id"] for t in lst["tasks"]],
                         [t1["task"]["task_id"], t2["task"]["task_id"]])
        # unknown mission rejected
        self.assertFalse(task_graph.list_tasks("mis_nope")["ok"])


class TaskGraphValidationTests(unittest.TestCase):
    def test_input_validation(self):
        mid = _fresh_mission()
        self.assertFalse(task_graph.create_task(mid, "")["ok"])
        self.assertFalse(task_graph.create_task(mid, "   ")["ok"])
        self.assertFalse(task_graph.create_task(mid, None)["ok"])
        self.assertFalse(
            task_graph.create_task(mid, "x" * (task_graph.MAX_NAME + 1))["ok"]
        )
        self.assertFalse(task_graph.create_task(mid, "bad", priority="urgent")["ok"])
        self.assertFalse(task_graph.create_task(mid, "bad", priority=123)["ok"])
        self.assertFalse(
            task_graph.create_task(mid, "bad", dependencies="not-a-list")["ok"]
        )
        self.assertFalse(
            task_graph.create_task(mid, "bad", input=object())["ok"]
        )
        self.assertFalse(
            task_graph.create_task(mid, "bad", metadata=object())["ok"]
        )

    def test_mission_ownership(self):
        ghost = task_graph.create_task("mis_missing", "Ghost")
        self.assertFalse(ghost["ok"])
        self.assertIn("not found", ghost["error"].lower())


class TaskGraphDagTests(unittest.TestCase):
    def test_diamond_dag_valid_and_deterministic(self):
        mid = _fresh_mission()
        a = task_graph.create_task(mid, "Research")
        b = task_graph.create_task(mid, "Discovery",
                                   dependencies=[a["task"]["task_id"]])
        c = task_graph.create_task(mid, "Analysis",
                                   dependencies=[a["task"]["task_id"]])
        e = task_graph.create_task(
            mid, "Qualification",
            dependencies=[b["task"]["task_id"], c["task"]["task_id"]],
        )
        self.assertTrue(a["ok"] and b["ok"] and c["ok"] and e["ok"])
        self.assertEqual(a["task"]["status"], "READY")
        self.assertEqual(b["task"]["status"], "PENDING")

        v = task_graph.validate_graph(mid)
        self.assertTrue(v["ok"])
        self.assertTrue(v["valid"])
        self.assertEqual(v["task_count"], 4)
        self.assertEqual(v["edge_count"], 4)
        self.assertEqual(v["errors"], [])
        self.assertEqual(v["order"][0], a["task"]["task_id"])
        self.assertEqual(v["order"][-1], e["task"]["task_id"])
        self.assertEqual(set(v["order"][1:3]),
                         {b["task"]["task_id"], c["task"]["task_id"]})
        # deterministic: same result twice
        self.assertEqual(v["order"], task_graph.validate_graph(mid)["order"])

    def test_self_dependency_rejected(self):
        mid = _fresh_mission()
        a = task_graph.create_task(mid, "A")
        bad = task_graph.create_task(
            mid, "B", dependencies=[a["task"]["task_id"], a["task"]["task_id"]],
        )
        self.assertFalse(bad["ok"])
        self.assertIn("duplicate dependency", bad["error"])

    def test_unknown_dependency_rejected(self):
        mid = _fresh_mission()
        bad = task_graph.create_task(mid, "B", dependencies=["tsk_nonexistent"])
        self.assertFalse(bad["ok"])
        self.assertIn("unknown dependency", bad["error"])

    def test_add_dependency_cycle_rejected_safely(self):
        mid = _fresh_mission()
        a = task_graph.create_task(mid, "A")
        b = task_graph.create_task(mid, "B", dependencies=[a["task"]["task_id"]])
        before = task_graph.validate_graph(mid)
        # adding a <- b creates a cycle (a depends on b while b depends on a)
        bad = task_graph.add_dependency(mid, a["task"]["task_id"],
                                        b["task"]["task_id"])
        self.assertFalse(bad["ok"])
        self.assertIn("cycle", bad["error"].lower())
        # graph unchanged after rejection
        after = task_graph.validate_graph(mid)
        self.assertTrue(after["valid"])
        self.assertEqual(after["order"], before["order"])

    def test_add_dependency_self_rejected(self):
        mid = _fresh_mission()
        a = task_graph.create_task(mid, "A")
        bad = task_graph.add_dependency(mid, a["task"]["task_id"],
                                        a["task"]["task_id"])
        self.assertFalse(bad["ok"])
        self.assertIn("itself", bad["error"])

    def test_sql_injection_safe(self):
        mid = _fresh_mission()
        r = task_graph.create_task(mid, "x'; DROP TABLE tasks; --")
        self.assertTrue(r["ok"])
        t = task_graph.get_task(mid, r["task"]["task_id"])
        self.assertIsNotNone(t)
        self.assertEqual(t["name"], "x'; DROP TABLE tasks; --")
        # graph still intact after hostile input
        self.assertTrue(task_graph.validate_graph(mid)["valid"])


class TaskGraphTransitionTests(unittest.TestCase):
    def test_ready_resolution_on_dependency_completion(self):
        mid = _fresh_mission()
        a = task_graph.create_task(mid, "Research")
        b = task_graph.create_task(mid, "Discovery",
                                   dependencies=[a["task"]["task_id"]])
        self.assertEqual(b["task"]["status"], "PENDING")

        r = task_graph.ready_tasks(mid)
        self.assertEqual(r["total"], 1)
        self.assertEqual(r["ready"][0]["task_id"], a["task"]["task_id"])

        task_graph.transition_task(mid, a["task"]["task_id"], "RUNNING")
        task_graph.transition_task(
            mid, a["task"]["task_id"], "COMPLETED", output={"n": 10},
        )
        r = task_graph.ready_tasks(mid)
        self.assertEqual(r["total"], 1)
        self.assertEqual(r["ready"][0]["task_id"], b["task"]["task_id"])

    def test_join_waits_for_all_dependencies(self):
        mid = _fresh_mission()
        a = task_graph.create_task(mid, "A")
        b = task_graph.create_task(mid, "B", dependencies=[a["task"]["task_id"]])
        c = task_graph.create_task(mid, "C", dependencies=[a["task"]["task_id"]])
        d = task_graph.create_task(
            mid, "D", dependencies=[b["task"]["task_id"], c["task"]["task_id"]],
        )
        # complete A -> B and C both become READY (fan-out)
        task_graph.transition_task(mid, a["task"]["task_id"], "RUNNING")
        task_graph.transition_task(mid, a["task"]["task_id"], "COMPLETED")
        r = task_graph.ready_tasks(mid)
        self.assertEqual(r["total"], 2)
        self.assertEqual(set(t["task_id"] for t in r["ready"]),
                         {b["task"]["task_id"], c["task"]["task_id"]})
        task_graph.transition_task(mid, b["task"]["task_id"], "RUNNING")
        task_graph.transition_task(mid, b["task"]["task_id"], "COMPLETED")
        # D still waits on C (join)
        r = task_graph.ready_tasks(mid)
        self.assertEqual(r["total"], 1)
        self.assertEqual(r["ready"][0]["task_id"], c["task"]["task_id"])
        task_graph.transition_task(mid, c["task"]["task_id"], "RUNNING")
        task_graph.transition_task(mid, c["task"]["task_id"], "COMPLETED")
        r = task_graph.ready_tasks(mid)
        self.assertEqual(r["total"], 1)
        self.assertEqual(r["ready"][0]["task_id"], d["task"]["task_id"])

    def test_blocked_on_failed_dependency(self):
        mid = _fresh_mission()
        x = task_graph.create_task(mid, "Research X")
        y = task_graph.create_task(mid, "Prospect Y",
                                   dependencies=[x["task"]["task_id"]])
        task_graph.transition_task(mid, x["task"]["task_id"], "RUNNING")
        f = task_graph.transition_task(mid, x["task"]["task_id"], "FAILED",
                                       error="no data")
        self.assertTrue(f["ok"])
        self.assertEqual(f["task"]["status"], "FAILED")
        blk = task_graph.blocked_tasks(mid)
        self.assertEqual(blk["total"], 1)
        self.assertEqual(blk["blocked"][0]["task_id"], y["task"]["task_id"])
        self.assertEqual(
            task_graph.get_task(mid, y["task"]["task_id"])["status"], "BLOCKED",
        )

    def test_blocked_on_cancelled_dependency(self):
        mid = _fresh_mission()
        x = task_graph.create_task(mid, "X")
        y = task_graph.create_task(mid, "Y", dependencies=[x["task"]["task_id"]])
        task_graph.transition_task(mid, x["task"]["task_id"], "CANCELLED")
        blk = task_graph.blocked_tasks(mid)
        self.assertEqual(blk["total"], 1)
        self.assertEqual(blk["blocked"][0]["task_id"], y["task"]["task_id"])

    def test_invalid_and_terminal_transitions_rejected(self):
        mid = _fresh_mission()
        # dependent task (starts PENDING) — make it READY explicitly
        dep = task_graph.create_task(mid, "dep")
        t = task_graph.create_task(mid, "T",
                                   dependencies=[dep["task"]["task_id"]])
        tid = t["task"]["task_id"]
        self.assertEqual(t["task"]["status"], "PENDING")
        # PENDING -> RUNNING invalid (must go READY first)
        self.assertFalse(
            task_graph.transition_task(mid, tid, "RUNNING")["ok"]
        )
        # PENDING -> COMPLETED invalid
        self.assertFalse(
            task_graph.transition_task(mid, tid, "COMPLETED")["ok"]
        )
        # unknown status
        self.assertFalse(
            task_graph.transition_task(mid, tid, "BOGUS")["ok"]
        )
        # complete dep -> t auto-promotes PENDING -> READY
        task_graph.transition_task(mid, dep["task"]["task_id"], "RUNNING")
        task_graph.transition_task(mid, dep["task"]["task_id"], "COMPLETED")
        self.assertEqual(task_graph.get_task(mid, tid)["status"], "READY")
        # happy path READY -> RUNNING -> COMPLETED
        r = task_graph.transition_task(mid, tid, "RUNNING")
        self.assertTrue(r["ok"])
        r = task_graph.transition_task(
            mid, tid, "COMPLETED", output={"report": "done"},
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["task"]["output"], {"report": "done"})
        # terminal: COMPLETED -> nothing
        self.assertFalse(
            task_graph.transition_task(mid, tid, "CANCELLED")["ok"]
        )
        self.assertFalse(
            task_graph.transition_task(mid, tid, "FAILED", error="late")["ok"]
        )

    def test_fail_requires_error(self):
        mid = _fresh_mission()
        t = task_graph.create_task(mid, "T")
        tid = t["task"]["task_id"]
        task_graph.transition_task(mid, tid, "RUNNING")
        self.assertFalse(task_graph.transition_task(mid, tid, "FAILED")["ok"])
        r = task_graph.transition_task(mid, tid, "FAILED", error="boom")
        self.assertTrue(r["ok"])
        self.assertEqual(r["task"]["error"], "boom")
        self.assertEqual(r["task"]["status"], "FAILED")

    def test_completed_output_must_be_json_serializable(self):
        mid = _fresh_mission()
        t = task_graph.create_task(mid, "T")
        tid = t["task"]["task_id"]
        task_graph.transition_task(mid, tid, "RUNNING")
        self.assertFalse(
            task_graph.transition_task(mid, tid, "COMPLETED", output=object())["ok"]
        )

    def test_cancel_from_every_task_state(self):
        for state, setup in (
            ("PENDING", lambda m, t: None),
            ("READY", lambda m, t: None),      # dependency-free task starts READY
            ("RUNNING", lambda m, t: task_graph.transition_task(m, t, "RUNNING")),
            ("BLOCKED", lambda m, t: None),    # created under failed dep in test
        ):
            mid = _fresh_mission()
            if state == "BLOCKED":
                x = task_graph.create_task(mid, "dep")
                r = task_graph.create_task(mid, "child",
                                           dependencies=[x["task"]["task_id"]])
                task_graph.transition_task(mid, x["task"]["task_id"], "RUNNING")
                task_graph.transition_task(mid, x["task"]["task_id"], "FAILED",
                                           error="boom")
                # re-read: PENDING -> BLOCKED after dep failure
                self.assertEqual(
                    task_graph.get_task(mid, r["task"]["task_id"])["status"],
                    "BLOCKED",
                )
            else:
                r = task_graph.create_task(mid, "task")
                setup(mid, r["task"]["task_id"])
            c = task_graph.transition_task(mid, r["task"]["task_id"], "CANCELLED")
            self.assertTrue(c["ok"], f"{state} -> CANCELLED failed: {c.get('error')}")
            self.assertEqual(c["task"]["status"], "CANCELLED")

    def test_task_state_machine_surface(self):
        sm = task_graph.task_state_machine()
        self.assertEqual(set(sm.keys()),
                         set(task_graph.VALID_TASK_STATUSES))
        self.assertIn("READY", sm["PENDING"])


if __name__ == "__main__":
    unittest.main(verbosity=2)