from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.types import SecurityFinding
from silvirica.security.rules import scan_code_for_vulnerabilities
from silvirica.security.secret_scanner import SecretScanner

class SecurityEngine:
    def __init__(self, root_path: Path, config: Optional[ProjectConfig] = None):
        self.root_path = root_path.resolve()
        self.config = config or load_config(self.root_path)

    def scan_repository(self) -> Dict[str, Any]:
        all_findings: List[SecurityFinding] = []
        files_scanned = 0
        for item in self.root_path.rglob("*"):
            if item.is_file():
                rel = str(item.relative_to(self.root_path)).replace("\\", "/")
                if any(part in [".git", ".silvirica", "node_modules", "vendor", "__pycache__", "venv", ".venv"] for part in item.parts):
                    continue
                files_scanned += 1
                all_findings.extend(SecretScanner.scan_file(item, rel))
                if item.suffix.lower() in [".py", ".js", ".ts", ".php", ".jsx", ".tsx", ".sql"]:
                    try:
                        content = item.read_text(encoding="utf-8", errors="ignore")
                        all_findings.extend(scan_code_for_vulnerabilities(content, rel))
                    except Exception:
                        pass

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}
        for f in all_findings:
            severity_counts[f.severity.value] += 1
        return {"files_scanned": files_scanned, "total_findings": len(all_findings), "severity_counts": severity_counts, "findings": all_findings}
