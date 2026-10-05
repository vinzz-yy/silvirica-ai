from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import SecurityFinding
from silvirica.security.audit_logger import SecurityAuditLogger
from silvirica.security.rules import scan_code_for_vulnerabilities
from silvirica.security.sandbox import PathSandbox
from silvirica.security.secret_scanner import SecretScanner


class SecurityEngine:
    def __init__(self, root_path: Path, config: Optional[ProjectConfig] = None):
        self.root_path = root_path.resolve()
        self.config = config or load_config(self.root_path)
        self.audit_logger = SecurityAuditLogger(self.root_path)

    def scan_repository(self, target_path: Optional[str] = None) -> Dict[str, Any]:
        all_findings: List[SecurityFinding] = []
        files_scanned = 0

        scan_root = self.root_path
        if target_path:
            scan_root = PathSandbox.resolve_safe_path(target_path, self.root_path)

        if scan_root.is_file():
            items = [scan_root]
        else:
            items = list(scan_root.rglob("*"))

        for item in items:
            if item.is_file():
                # Directory depth check
                try:
                    rel = str(item.relative_to(self.root_path)).replace("\\", "/")
                    if len(item.relative_to(self.root_path).parts) > PathSandbox.MAX_DIRECTORY_DEPTH:
                        continue
                except ValueError:
                    continue

                if any(part in [".git", ".silvirica", "node_modules", "vendor", "__pycache__", "venv", ".venv", "dist", "build"] for part in item.parts):
                    continue

                # File size limit & binary check
                if not PathSandbox.check_file_size_limit(item):
                    continue
                if PathSandbox.is_binary_file(item):
                    continue

                files_scanned += 1
                all_findings.extend(SecretScanner.scan_file(item, rel))

                if item.suffix.lower() in [".py", ".js", ".ts", ".php", ".jsx", ".tsx", ".sql", ".rb", ".go", ".rs", ".java"]:
                    try:
                        content = item.read_text(encoding="utf-8", errors="ignore")
                        all_findings.extend(scan_code_for_vulnerabilities(content, rel))
                    except Exception:
                        pass

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}
        for f in all_findings:
            severity_counts[f.severity.value] += 1

        self.audit_logger.log_event(
            event_type=SecurityAuditLogger.EVENT_SECURITY_SCAN,
            action="scan_repository",
            status="SUCCESS",
            details={
                "files_scanned": files_scanned,
                "total_findings": len(all_findings),
                "severity_counts": severity_counts,
            },
        )

        return {
            "files_scanned": files_scanned,
            "total_findings": len(all_findings),
            "severity_counts": severity_counts,
            "findings": all_findings,
        }
