from __future__ import annotations
import json
import os
import secrets
import stat
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union
from urllib.parse import parse_qs, urlparse

from silvirica.core.config import load_config
from silvirica.core.project import ProjectBrain
from silvirica.mcp.tools import MCPToolRegistry
from silvirica.security.audit_logger import SecurityAuditLogger


class SilviricaDaemonHandler(BaseHTTPRequestHandler):
    registry: MCPToolRegistry = None
    auth_token: Optional[str] = None
    audit_logger: Optional[SecurityAuditLogger] = None
    MAX_REQUEST_BYTES: int = 5 * 1024 * 1024  # 5 MB payload limit

    allowed_origins: Set[str] = {
        "http://localhost",
        "http://127.0.0.1",
        "vscode-webview://",
        "silvirica://",
    }

    @classmethod
    def _is_origin_allowed(cls, origin: Optional[str]) -> bool:
        if not origin:
            # If no Origin header is sent (e.g. CLI or backend daemon client), allow only if authenticated
            return True
        try:
            parsed = urlparse(origin)
            if parsed.scheme in ["vscode-webview", "silvirica"]:
                return True
            if parsed.scheme in ["http", "https"] and parsed.hostname in ["localhost", "127.0.0.1"]:
                return True
        except Exception:
            return False
        return False

    def _validate_auth(self) -> bool:
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

        if self.audit_logger:
            self.audit_logger.log_event(
                event_type=SecurityAuditLogger.EVENT_AUTH_FAILURE,
                action=self.path,
                status="DENIED",
                severity="HIGH",
                details={"client_address": str(self.client_address)},
            )
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
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
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
        
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            length = 0

        # Resource exhaustion defense: Payload size check
        if length > self.MAX_REQUEST_BYTES:
            self._set_headers(413)
            self.wfile.write(json.dumps({"error": "Payload Too Large: Request exceeds maximum size limit (5 MB)."}).encode("utf-8"))
            return

        body = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else "{}"
        try:
            payload = json.loads(body)
            if not isinstance(payload, dict):
                payload = {}
        except Exception:
            payload = {}

        if path == "/api/tool":
            tool_name = str(payload.get("name", ""))
            args = payload.get("arguments", {})
            if not isinstance(args, dict):
                args = {}
            try:
                result = self.registry.call_tool(tool_name, args)
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True, "result": result}).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif path == "/api/context":
            task = str(payload.get("task", ""))
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

    # Generate or load secure daemon token
    token_file = root / ".silvirica" / "daemon.token"
    eff_token = auth_token
    if not eff_token:
        if token_file.exists():
            try:
                eff_token = token_file.read_text(encoding="utf-8").strip()
            except Exception:
                eff_token = secrets.token_urlsafe(32)
        else:
            eff_token = secrets.token_urlsafe(32)
            try:
                token_file.parent.mkdir(parents=True, exist_ok=True)
                token_file.write_text(eff_token, encoding="utf-8")
                try:
                    os.chmod(token_file, stat.S_IRUSR | stat.S_IWUSR)
                except Exception:
                    pass
            except Exception:
                pass

    audit = SecurityAuditLogger(root)
    SilviricaDaemonHandler.registry = MCPToolRegistry(root)
    SilviricaDaemonHandler.auth_token = eff_token
    SilviricaDaemonHandler.audit_logger = audit

    server_address = ("127.0.0.1", eff_port)
    httpd = HTTPServer(server_address, SilviricaDaemonHandler)

    audit.log_event(
        event_type=SecurityAuditLogger.EVENT_DAEMON_STARTED,
        action="startup",
        status="RUNNING",
        details={"host": "127.0.0.1", "port": eff_port, "root": str(root)},
    )

    print(f"Silvirica Daemon listening securely on http://127.0.0.1:{eff_port} (Root: {root})")
    print(f">> Auth Token: {eff_token[:6]}... (Full token stored at .silvirica/daemon.token)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Silvirica Daemon...")
        httpd.server_close()
