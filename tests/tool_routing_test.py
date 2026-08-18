#!/usr/bin/env python3
"""Unit tests for HEER tool naming repair (Phase C).

Run:  python3 tests/tool_routing_test.py
"""

import os
import sys
import unittest

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from agent import registry, tools, orchestrator


class ToolRoutingRegressionTests(unittest.TestCase):
    def test_short_name_dispatches_to_developer_tools(self):
        r = tools.call_tool("code_read", {"path": "README.md"})
        self.assertNotEqual(r.get("error"), "Unknown tool 'code_read'.")

    def test_short_name_dispatches_to_github_tools(self):
        r = tools.call_tool("github_read", {"resource": "repos"})
        self.assertNotEqual(r.get("error"), "Unknown tool 'github_read'.")

    def test_short_name_dispatches_to_n8n_tools(self):
        r = tools.call_tool("n8n", {"trigger": "manual"})
        self.assertNotEqual(r.get("error"), "Unknown tool 'n8n'.")

    def test_short_name_dispatches_to_deploy_tools(self):
        r = tools.call_tool("docker", {"image": "test"})
        self.assertNotEqual(r.get("error"), "Unknown tool 'docker'.")

    def test_short_name_dispatches_to_terminal_tools(self):
        r = tools.call_tool("terminal_exec", {"command": "ls"})
        self.assertNotEqual(r.get("error"), "Unknown tool 'terminal_exec'.")

    def test_prefixed_name_is_not_registered(self):
        r = tools.call_tool("developer_code_read", {"path": "x"})
        self.assertEqual(r.get("code"), "TOOL_NOT_REGISTERED")


class ToolRegistryConsistencyTests(unittest.TestCase):
    def test_every_tool_registry_entry_exists_in_tools(self):
        missing = [n for n, (r, a, e) in registry.TOOL_REGISTRY.items()
                   if n not in tools.TOOLS and e]
        self.assertEqual(missing, [], f"TOOL_REGISTRY entries missing from TOOLS: {missing}")

    def test_every_phase3_module_tool_has_registry_entry(self):
        module_tools = [n for n, t in tools.TOOLS.items()
                        if t.get("module") in ("developer", "github", "n8n", "deploy", "terminal")]
        missing = [n for n in module_tools if n not in registry.TOOL_REGISTRY]
        self.assertEqual(missing, [], f"Phase-3 module tools missing from TOOL_REGISTRY: {missing}")

    def test_tool_descriptions_include_module_metadata(self):
        module_tools = [t for t in tools.tool_descriptions() if t.get("module") != "core"]
        self.assertGreaterEqual(len(module_tools), 8)


class ApprovalGateTests(unittest.TestCase):
    def test_code_write_approval_level_is_1(self):
        tdef = registry.tool_def("code_write")
        self.assertEqual(tdef["approval_level"], 1)

    def test_terminal_exec_approval_level_is_3(self):
        tdef = registry.tool_def("terminal_exec")
        self.assertEqual(tdef["approval_level"], 3)

    def test_docker_approval_level_is_2(self):
        tdef = registry.tool_def("docker")
        self.assertEqual(tdef["approval_level"], 2)


class OrchestratorPlanTests(unittest.TestCase):
    def test_developer_agent_plans_short_tool_names(self):
        steps = orchestrator.plan("developer", "read a file")
        tool_names = [t for t, _ in steps]
        self.assertIn("code_read", tool_names)
        self.assertNotIn("developer_code_read", tool_names)

    def test_github_agent_plans_short_tool_names(self):
        steps = orchestrator.plan("github", "list issues")
        tool_names = [t for t, _ in steps]
        self.assertIn("github_read", tool_names)
        self.assertNotIn("github_github_read", tool_names)

    def test_devops_agent_plans_short_tool_names(self):
        steps = orchestrator.plan("devops", "build a docker image")
        tool_names = [t for t, _ in steps]
        self.assertIn("docker", tool_names)
        self.assertIn("terminal_exec", tool_names)
        self.assertNotIn("deploy_docker", tool_names)
        self.assertNotIn("terminal_terminal_exec", tool_names)


class DiagnosticTests(unittest.TestCase):
    def test_unknown_tool_returns_tool_not_registered(self):
        r = tools.call_tool("unknown_tool_xyz", {})
        self.assertEqual(r.get("code"), "TOOL_NOT_REGISTERED")
        self.assertEqual(r.get("tool"), "unknown_tool_xyz")
        self.assertEqual(r.get("ok"), False)
        self.assertIn("error", r)
        self.assertEqual(r.get("reason"), "not_registered")

    def test_disabled_tool_returns_tool_unavailable(self):
        r = tools.call_tool("web_search", {})
        self.assertEqual(r.get("code"), "TOOL_UNAVAILABLE")
        self.assertEqual(r.get("reason"), "disabled")

    def test_execute_unknown_tool_includes_agent(self):
        steps = [("nonexistent_tool", {})]
        result = orchestrator.execute(steps, "test_biz", "req-1", agent_id="developer")
        self.assertEqual(result["results"][0]["code"], "TOOL_NOT_REGISTERED")
        self.assertEqual(result["results"][0]["agent"], "developer")
        self.assertFalse(result["results"][0].get("ok", True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
