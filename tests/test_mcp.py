from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from silvirica.core.project import ProjectBrain
from silvirica.mcp.server import MCPServer
from silvirica.mcp.tools import MCPToolRegistry


class TestMCPServer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.brain = ProjectBrain(self.root)
        self.brain.init()
        self.server = MCPServer(self.root)
        self.registry = MCPToolRegistry(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_mcp_initialize(self) -> None:
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        raw_resp = self.server.handle_request(req)
        self.assertIsNotNone(raw_resp)
        resp = json.loads(raw_resp)
        self.assertEqual(resp["id"], 1)
        self.assertIn("capabilities", resp["result"])

    def test_mcp_list_tools(self) -> None:
        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        raw_resp = self.server.handle_request(req)
        resp = json.loads(raw_resp)
        tools = resp["result"]["tools"]
        self.assertEqual(len(tools), 14)

        names = [t["name"] for t in tools]
        self.assertIn("silvirica_project", names)
        self.assertIn("silvirica_search", names)
        self.assertIn("silvirica_symbol", names)
        self.assertIn("silvirica_graph", names)
        self.assertIn("silvirica_memory", names)
        self.assertIn("silvirica_security", names)
        self.assertIn("silvirica_context", names)
        self.assertIn("silvirica_route", names)

    def test_mcp_call_project_tool(self) -> None:
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "silvirica_project", "arguments": {}},
        })
        raw_resp = self.server.handle_request(req)
        resp = json.loads(raw_resp)
        self.assertIn("content", resp["result"])
        text = resp["result"]["content"][0]["text"]
        self.assertIn("name", text)


if __name__ == "__main__":
    unittest.main()
