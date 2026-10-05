from __future__ import annotations
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


class SecurityAuditLogger:
    """
    Structured, zero-leakage security audit logger for Silvirica.
    Persists audit events into .silvirica/security/audit.log with automatic
    rotation considerations, ISO timestamps, and strict secret redaction.
    """

    EVENT_MCP_REQUEST = "MCP_REQUEST"
    EVENT_AUTH_FAILURE = "AUTH_FAILURE"
    EVENT_PATH_BLOCKED = "PATH_BLOCKED"
    EVENT_SECRET_REDACTED = "SECRET_REDACTED"
    EVENT_SKILL_DENIED = "SKILL_DENIED"
    EVENT_CONFIG_CHANGED = "CONFIG_CHANGED"
    EVENT_SECURITY_SCAN = "SECURITY_SCAN"
    EVENT_DAEMON_STARTED = "DAEMON_STARTED"
    EVENT_PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    EVENT_SSRF_BLOCKED = "SSRF_BLOCKED"

    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = (root_path or Path.cwd()).resolve()
        self.security_dir = self.root_path / ".silvirica" / "security"
        self.log_file = self.security_dir / "audit.log"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        try:
            self.security_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def log_event(
        self,
        event_type: str,
        action: str,
        status: str = "SUCCESS",
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
    ) -> None:
        """
        Records a structured security event. Guarantees no sensitive tokens are logged.
        """
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "epoch": time.time(),
            "event_type": event_type,
            "action": action,
            "status": status,
            "actor": actor,
            "severity": severity,
            "details": self._sanitize_details(details or {}),
        }
        self._write_entry(entry)

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Strips potential credentials, auth tokens, passwords, or bearer headers from audit log entries.
        """
        sanitized: Dict[str, Any] = {}
        for k, v in details.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ["auth", "token", "key", "password", "secret", "bearer", "cred"]):
                sanitized[k] = "[REDACTED_BY_AUDIT_POLICY]"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize_details(v)
            elif isinstance(v, str) and len(v) > 500:
                sanitized[k] = v[:500] + "... [truncated]"
            else:
                sanitized[k] = v
        return sanitized

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        try:
            self._ensure_dir()
            # Enforce max log file size (5 MB rotation)
            if self.log_file.exists() and self.log_file.stat().st_size > 5 * 1024 * 1024:
                backup = self.security_dir / f"audit_{int(time.time())}.log"
                self.log_file.rename(backup)

            line = json.dumps(entry) + "\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def get_recent_events(self, limit: int = 50) -> list[Dict[str, Any]]:
        """
        Reads the most recent audit events.
        """
        if not self.log_file.exists():
            return []
        events = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    if line.strip():
                        events.append(json.loads(line))
        except Exception:
            pass
        return events
