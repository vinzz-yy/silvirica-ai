from __future__ import annotations
import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union
from urllib.parse import parse_qs, urlparse

from silvirica.core.config import load_config
from silvirica.core.project import ProjectBrain
from silvirica.mcp.tools import MCPToolRegistry


class SilviricaDaemonHandler(BaseHTTPRequestHandler):
    registry: MCPToolRegistry = None
    auth_token: Optional[str] = None
    allowed_origins: Set[str] = {
        "http://localhost",
        "http://127.0.0.1",
        "vscode-webview://",
        "silvirica://",
    }

    @classmethod
    def _is_origin_allowed(cls, origin: Optional[str]) -> bool:
        if not origin:
            return True
        origin_lower = origin.lower()
        return any(origin_lower.startswith(allowed) for allowed in cls.allowed_origins)

    def _validate_auth(self) -> bool:
        # If no auth token configured, allow localhost loopback
        if not self.auth_token:
            return True

        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if secrets.compare_digest(token, self.auth_token):
                return True

        x_token = self.headers.get("X-Silvirica-Token", "").strip()
        if x_token and secrets.compare_digest(x_token, self.auth_token):
            return True

        return False

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)

        origin = self.headers.get("Origin")
        if origin and self._is_origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")

        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Silvirica-Token")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_headers(204)

    def do_GET(self) -> None:
        origin = self.headers.get("Origin")
        if origin and not self._is_origin_allowed(origin):
            self._set_headers(403)
            self.wfile.write(json.dumps({"error": "Forbidden: Untrusted cross-origin request rejected."}).encode("utf-8"))
            return

        if not self._validate_auth():
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized: Valid Bearer token required."}).encode("utf-8"))
            return

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
        origin = self.headers.get("Origin")
        if origin and not self._is_origin_allowed(origin):
            self._set_headers(403)
            self.wfile.write(json.dumps({"error": "Forbidden: Untrusted cross-origin request rejected."}).encode("utf-8"))
            return

        if not self._validate_auth():
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Unauthorized: Valid Bearer token required."}).encode("utf-8"))
            return

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
    auth_token: Optional[str] = None,
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
    SilviricaDaemonHandler.auth_token = auth_token

    server_address = ("127.0.0.1", eff_port)
    httpd = HTTPServer(server_address, SilviricaDaemonHandler)
    print(f"Silvirica Daemon listening securely on http://127.0.0.1:{eff_port} (Root: {root})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Silvirica Daemon...")
        httpd.server_close()
