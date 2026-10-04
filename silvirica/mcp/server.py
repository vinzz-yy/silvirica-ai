from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from silvirica.mcp.protocol import JsonRpcRequest, JsonRpcResponse
from silvirica.mcp.tools import MCPToolRegistry


class MCPServer:
    """
    Standard I/O MCP (Model Context Protocol) Server.
    Enables zero-friction connection with Cursor, Windsurf, Claude Desktop, Antigravity IDE, Roo, Cline, Continue.
    """

    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = (root_path or Path.cwd()).resolve()
        self.registry = MCPToolRegistry(self.root_path)

    def handle_request(self, raw_line: str) -> Optional[str]:
        if not raw_line.strip():
            return None
        try:
            data = json.loads(raw_line)
            req = JsonRpcRequest.from_dict(data)
        except Exception as e:
            res = JsonRpcResponse(id=None, error={"code": -32700, "message": f"Parse error: {str(e)}"})
            return res.to_json()

        # Handle MCP protocol methods
        if req.method == "initialize":
            res = JsonRpcResponse(
                id=req.id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "silvirica-mcp-server", "version": "0.1.0"},
                },
            )
            return res.to_json()

        elif req.method == "tools/list":
            tools = self.registry.get_tool_definitions()
            res = JsonRpcResponse(id=req.id, result={"tools": tools})
            return res.to_json()

        elif req.method == "tools/call":
            params = req.params or {}
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                result_content = self.registry.call_tool(tool_name, arguments)
                res = JsonRpcResponse(
                    id=req.id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_content, indent=2) if not isinstance(result_content, str) else result_content,
                            }
                        ]
                    },
                )
                return res.to_json()
            except Exception as e:
                res = JsonRpcResponse(
                    id=req.id,
                    error={"code": -32603, "message": f"Tool execution failed: {str(e)}"},
                )
                return res.to_json()

        elif req.method == "notifications/initialized":
            return None  # No response needed for notification

        elif req.method == "ping":
            return JsonRpcResponse(id=req.id, result={}).to_json()

        else:
            res = JsonRpcResponse(
                id=req.id,
                error={"code": -32601, "message": f"Method not found: {req.method}"},
            )
            return res.to_json()

    def run_stdio(self) -> None:
        """
        Runs the server listening on sys.stdin and writing to sys.stdout.
        """
        for line in sys.stdin:
            response = self.handle_request(line)
            if response:
                sys.stdout.write(response + "\n")
                sys.stdout.flush()
