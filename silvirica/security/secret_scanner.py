from __future__ import annotations
from pathlib import Path
from typing import List
from silvirica.core.types import FindingSeverity, SecurityFinding
from silvirica.context.redactor import SECRET_PATTERNS

class SecretScanner:
    @classmethod
    def scan_file(cls, file_path: Path, rel_path: str) -> List[SecurityFinding]:
        if not file_path.exists() or not file_path.is_file():
            return []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []
        findings: List[SecurityFinding] = []
        lines = content.splitlines()
        for pat_name, pattern in SECRET_PATTERNS:
            for idx, line in enumerate(lines, 1):
                if "REDACTED_SECRET" in line or "SECRET_PATTERNS" in line:
                    continue
                if pattern.search(line):
                    finding = SecurityFinding(
                        rule_id=f"SEC-SECRET-{pat_name}", title=f"Potential Hardcoded Secret: {pat_name}",
                        severity=FindingSeverity.CRITICAL, location=f"{rel_path}:{idx}", file_path=rel_path,
                        line_number=idx, evidence="[SECRET DETECTED - REDACTED]",
                        risk_description="Hardcoded secrets can be compromised.",
                        recommendation="Store secrets in environment variables.", cwe_id="CWE-798",
                        owasp_category="A07:2021-Identification and Authentication Failures",
                    )
                    findings.append(finding)
        return findings
