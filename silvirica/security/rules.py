from __future__ import annotations
import re
from typing import List
from silvirica.core.types import FindingSeverity, SecurityFinding

SECURITY_RULES = [
    {
        "id": "SEC-SQLI-001",
        "title": "Raw SQL String Concatenation / Format Injection",
        "severity": FindingSeverity.CRITICAL,
        "cwe_id": "CWE-89",
        "owasp": "A03:2021-Injection",
        "pattern": re.compile(
            r'(?:f["\']\s*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b|'
            r'(?:execute|raw|query)\s*\(\s*(?:f["\']|["\'].*?%s|["\'].*?\+|sql|query))',
            re.IGNORECASE,
        ),
        "description": "SQL query formed by direct string interpolation or concatenation.",
        "recommendation": "Use parameterized queries or ORM query builders.",
    },
    {
        "id": "SEC-EVAL-001",
        "title": "Unsafe Dynamic Code Evaluation",
        "severity": FindingSeverity.CRITICAL,
        "cwe_id": "CWE-95",
        "owasp": "A03:2021-Injection",
        "pattern": re.compile(r'\b(?:eval|exec)\s*\([^)]+\)', re.IGNORECASE),
        "description": "Direct dynamic code execution allows arbitrary code execution.",
        "recommendation": "Avoid eval/exec; use safe parsing or structured dispatchers.",
    },
    {
        "id": "SEC-XSS-001",
        "title": "Unescaped HTML Output / XSS",
        "severity": FindingSeverity.HIGH,
        "cwe_id": "CWE-79",
        "owasp": "A03:2021-Injection",
        "pattern": re.compile(r'(?:dangerouslySetInnerHTML|v-html|{!!\s*.*?\s*!!}|\.innerHTML\s*=)', re.IGNORECASE),
        "description": "Raw unescaped HTML content injected into DOM.",
        "recommendation": "Sanitize HTML using DOMPurify or framework auto-escaping.",
    },
    {
        "id": "SEC-CMD-001",
        "title": "Command Injection via Shell Execution",
        "severity": FindingSeverity.CRITICAL,
        "cwe_id": "CWE-78",
        "owasp": "A03:2021-Injection",
        "pattern": re.compile(r'(?:os\.system\s*\(|subprocess\.Popen\s*\(.*?shell\s*=\s*True|shell_exec\s*\(|system\s*\()', re.IGNORECASE),
        "description": "Direct shell execution with untrusted parameters.",
        "recommendation": "Pass command arguments as structured array without shell=True.",
    },
    {
        "id": "SEC-CSRF-001",
        "title": "CSRF Protection Disabled",
        "severity": FindingSeverity.HIGH,
        "cwe_id": "CWE-352",
        "owasp": "A01:2021-Broken Access Control",
        "pattern": re.compile(r'@csrf_exempt|VerifyCsrfToken::class.*?except', re.IGNORECASE),
        "description": "CSRF token verification is disabled on route or controller.",
        "recommendation": "Enable CSRF protection for all state-changing endpoints.",
    },
    {
        "id": "SEC-CORS-001",
        "title": "Permissive Wildcard CORS Configuration",
        "severity": FindingSeverity.MEDIUM,
        "cwe_id": "CWE-942",
        "owasp": "A05:2021-Security Misconfiguration",
        "pattern": re.compile(r'Access-Control-Allow-Origin["\']?\s*[:=]\s*["\']\*["\']', re.IGNORECASE),
        "description": "Wildcard CORS allow origin header exposes data to untrusted origins.",
        "recommendation": "Restrict allowed origins to explicit trusted domains.",
    },
]


def scan_code_for_vulnerabilities(content: str, file_path: str) -> List[SecurityFinding]:
    findings: List[SecurityFinding] = []
    lines = content.splitlines()
    for rule in SECURITY_RULES:
        pattern: re.Pattern = rule["pattern"]
        for idx, line in enumerate(lines, 1):
            if pattern.search(line):
                if "SEC-" in line and "pattern" in line:
                    continue
                finding = SecurityFinding(
                    rule_id=rule["id"],
                    title=rule["title"],
                    severity=rule["severity"],
                    location=f"{file_path}:{idx}",
                    file_path=file_path,
                    line_number=idx,
                    evidence=line.strip()[:200],
                    risk_description=rule["description"],
                    recommendation=rule["recommendation"],
                    cwe_id=rule["cwe_id"],
                    owasp_category=rule["owasp"],
                    verification_status="STATIC_MATCH",
                )
                findings.append(finding)
    return findings
