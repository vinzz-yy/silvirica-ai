from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

from silvirica.core.project import ProjectBrain
from silvirica.mcp.server import MCPServer
from silvirica.mcp.tools import MCPToolRegistry


class TestMCPComprehensive(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.brain = ProjectBrain(self.root)
        self.brain.init()

        # Write sample app.py
        (self.root / "app.py").write_text(
            "def calculate_total(price, quantity):\n"
            "    return price * quantity\n",
            encoding="utf-8",
        )
        self.server = MCPServer(self.root)
        self.registry = MCPToolRegistry(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_all_14_mcp_tools_registered(self) -> None:
        tools = self.registry.get_tool_definitions()
        self.assertEqual(len(tools), 14)
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "silvirica_project",
            "silvirica_search",
            "silvirica_symbol",
            "silvirica_graph",
            "silvirica_memory",
            "silvirica_recall",
            "silvirica_skill",
            "silvirica_security",
            "silvirica_context",
            "silvirica_route",
            "silvirica_impact",
            "silvirica_git",
            "silvirica_stats",
            "silvirica_health",
        ]
        for expected in expected_tools:
            self.assertIn(expected, tool_names)

    def test_all_14_mcp_tools_callable(self) -> None:
        test_calls = [
            ("silvirica_project", {}),
            ("silvirica_search", {"query": "calculate"}),
            ("silvirica_symbol", {"name": "calculate_total"}),
            ("silvirica_graph", {"query": "calculate_total"}),
            ("silvirica_memory", {"query": "architecture"}),
            ("silvirica_recall", {"topic": "database timeout", "type": "all"}),
            ("silvirica_skill", {"skill_name": "coding-core", "level": 1}),
            ("silvirica_security", {}),
            ("silvirica_context", {"task": "Refactor checkout flow"}),
            ("silvirica_route", {"task": "Fix SQL injection", "risk": "HIGH"}),
            ("silvirica_impact", {"node_id": "file:app.py"}),
            ("silvirica_git", {}),
            ("silvirica_stats", {}),
            ("silvirica_health", {}),
        ]
        for name, args in test_calls:
            with self.subTest(tool=name):
                result = self.registry.call_tool(name, args)
                self.assertIsNotNone(result)

    def test_oversized_input_handling(self) -> None:
        huge_text = "A" * 150_000
        # Should truncate / handle gracefully without crashing
        res = self.registry.call_tool("silvirica_search", {"query": huge_text})
        self.assertIsNotNone(res)

        res2 = self.registry.call_tool("silvirica_context", {"task": huge_text})
        self.assertIsNotNone(res2)

    def test_malformed_inputs(self) -> None:
        # Non-dict arguments handled safely
        res = self.registry.call_tool("silvirica_project", "not a dict")  # type: ignore
        self.assertIsNotNone(res)

        # Unknown tool raises ValueError
        with self.assertRaises(ValueError):
            self.registry.call_tool("nonexistent_tool_12345", {})

    def test_path_traversal_blocked(self) -> None:
        res = self.registry.call_tool("silvirica_security", {"file_path": "../../../../outside_secret.py"})
        self.assertTrue(isinstance(res, list))
        self.assertTrue(any("Access denied" in str(item) for item in res))

    def test_secret_redaction_in_output(self) -> None:
        # Mock memory with secret
        self.registry.vault.write_note("secret_note", "TOKEN=sk-proj-1234567890abcdef1234567890")
        res = self.registry.call_tool("silvirica_memory", {"query": "TOKEN"})
        serialized = json.dumps(res)
        self.assertNotIn("sk-proj-1234567890", serialized)
        self.assertIn("[REDACTED_SECRET]", serialized)

    def test_json_rpc_server_integration(self) -> None:
        # 1. initialize
        init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        init_resp = json.loads(self.server.handle_request(init_req))
        self.assertIn("capabilities", init_resp["result"])

        # 2. tools/list
        list_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        list_resp = json.loads(self.server.handle_request(list_req))
        self.assertEqual(len(list_resp["result"]["tools"]), 14)

        # 3. tools/call
        call_req = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "silvirica_health", "arguments": {}},
        })
        call_resp = json.loads(self.server.handle_request(call_req))
        self.assertNotIn("error", call_resp)
        self.assertIn("content", call_resp["result"])


if __name__ == "__main__":
    unittest.main()
