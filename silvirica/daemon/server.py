from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import parse_qs, urlparse

from silvirica.core.config import load_config
from silvirica.core.project import ProjectBrain
from silvirica.mcp.tools import MCPToolRegistry


class SilviricaDaemonHandler(BaseHTTPRequestHandler):
    registry: MCPToolRegistry = None

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_headers(204)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        if path == "/api/health":
            res = self.registry.call_tool("silvirica_health", {})
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/stats":
            res = self.registry.call_tool("silvirica_stats", {})
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/project":
            res = self.registry.call_tool("silvirica_project", {})
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/search":
            q = query_params.get("q", [""])[0]
            res = self.registry.call_tool("silvirica_search", {"query": q})
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": f"Endpoint not found: {path}"}).encode("utf-8"))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/tool":
            tool_name = payload.get("name", "")
            args = payload.get("arguments", {})
            try:
                result = self.registry.call_tool(tool_name, args)
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True, "result": result}).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/context":
            task = payload.get("task", "")
            res = self.registry.call_tool("silvirica_context", {"task": task})
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": f"Endpoint not found: {path}"}).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        pass


def run_daemon(
    arg1: Optional[Union[Path, int]] = None,
    port: int = 7458,
    root_path: Optional[Path] = None,
) -> None:
    if isinstance(arg1, Path):
        root = arg1.resolve()
        eff_port = port
    elif isinstance(arg1, int):
        eff_port = arg1
        root = (root_path or Path.cwd()).resolve()
    else:
        eff_port = port
        root = (root_path or Path.cwd()).resolve()

    SilviricaDaemonHandler.registry = MCPToolRegistry(root)
    server_address = ("127.0.0.1", eff_port)
    httpd = HTTPServer(server_address, SilviricaDaemonHandler)
    print(f"Silvirica Daemon listening on http://127.0.0.1:{eff_port} (Root: {root})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Silvirica Daemon...")
        httpd.server_close()
