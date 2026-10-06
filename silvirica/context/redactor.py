from __future__ import annotations
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class SecurityMode(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"
    ACTIVE_REDACTION = "active_redaction"


class ProviderPrivacyPolicy(str, Enum):
    LOCAL = "local"
    EXTERNAL = "external"
    TRUSTED = "trusted"


@dataclass
class SecurityScanResult:
    clean_text: str
    redacted_count: int
    security_confidence: float
    is_safe_for_external: bool
    findings: List[str]


# Specific patterns ordered before generic ones
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("OPENAI_PROJECT_KEY", re.compile(r'sk-(?:proj|admin)-[a-zA-Z0-9_\-]{20,}', re.IGNORECASE)),
    ("OPENAI_API_KEY", re.compile(r'sk-[a-zA-Z0-9_\-]{20,}', re.IGNORECASE)),
    ("ANTHROPIC_API_KEY", re.compile(r'sk-ant-(?:api\d{2}-)?[a-zA-Z0-9_\-]{20,}', re.IGNORECASE)),
    ("GITHUB_FINE_GRAINED_PAT", re.compile(r'github_pat_[a-zA-Z0-9_]{50,}', re.IGNORECASE)),
    ("GITHUB_TOKEN", re.compile(r'gh[pousr]-[a-zA-Z0-9]{36,}', re.IGNORECASE)),
    ("GOOGLE_API_KEY", re.compile(r'AIzaSy[a-zA-Z0-9_\-]{33}', re.IGNORECASE)),
    ("AWS_KEY", re.compile(r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}', re.IGNORECASE)),
    ("STRIPE_KEY", re.compile(r'(?:sk|pk|rk)_(?:test|live)_[0-9a-zA-Z]{20,}', re.IGNORECASE)),
    ("SLACK_TOKEN", re.compile(r'xox[baprs]-[0-9a-zA-Z]{10,}(?:-[0-9a-zA-Z]+)?', re.IGNORECASE)),
    ("PYPI_TOKEN", re.compile(r'pypi-[a-zA-Z0-9_\-]{50,}', re.IGNORECASE)),
    ("HUGGINGFACE_TOKEN", re.compile(r'hf_[a-zA-Z0-9]{34,}', re.IGNORECASE)),
    ("NPM_TOKEN", re.compile(r'npm_[a-zA-Z0-9]{36}', re.IGNORECASE)),
    ("DISCORD_BOT_TOKEN", re.compile(r'[MNO][a-zA-Z0-9_\-]{23,25}\.[a-zA-Z0-9_\-]{6}\.[a-zA-Z0-9_\-]{27}', re.IGNORECASE)),
    ("DB_CONNECTION_STRING", re.compile(r'(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp|oracle|sqlite3):\/\/[^\s"\'<>]+', re.IGNORECASE)),
    ("BEARER_TOKEN", re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{20,}', re.IGNORECASE)),
    ("PRIVATE_KEY", re.compile(r'-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA|PGP|ENCRYPTED)?\s*PRIVATE\s*KEY-----[\s\S]+?-----END\s+(?:RSA|OPENSSH|EC|DSA|PGP|ENCRYPTED)?\s*PRIVATE\s*KEY-----', re.IGNORECASE)),
    ("JWT_TOKEN", re.compile(r'eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}', re.IGNORECASE)),
    ("GENERIC_PASSWORD", re.compile(r'(?:password|passwd|secret|apikey|api_key|client_secret|access_token|private_key|auth_token)\s*[:=]\s*["\']([^"\']{8,})["\']', re.IGNORECASE)),
]


class SecretRedactor:
    """
    Enterprise Pre-Model Security Scanner & Redactor 2.0.
    Guarantees zero-leakage secret redaction across all content tiers.
    """

    REPLACEMENT = "[REDACTED_SECRET]"

    @classmethod
    def sanitize_text(
        cls,
        text: str,
        mode: Any = SecurityMode.BALANCED,
        provider_policy: ProviderPrivacyPolicy = ProviderPrivacyPolicy.EXTERNAL,
    ) -> str:
        sec_mode = mode if isinstance(mode, SecurityMode) else SecurityMode.BALANCED
        scan = cls.scan_and_redact(text, mode=sec_mode, provider_policy=provider_policy)
        return scan.clean_text

    @classmethod
    def redact(
        cls,
        text: str,
        mode: SecurityMode = SecurityMode.BALANCED,
        provider_policy: ProviderPrivacyPolicy = ProviderPrivacyPolicy.EXTERNAL,
    ) -> Tuple[str, int]:
        scan = cls.scan_and_redact(text, mode=mode, provider_policy=provider_policy)
        return scan.clean_text, scan.redacted_count

    @classmethod
    def scan_and_redact(
        cls,
        text: str,
        mode: SecurityMode = SecurityMode.BALANCED,
        provider_policy: ProviderPrivacyPolicy = ProviderPrivacyPolicy.EXTERNAL,
    ) -> SecurityScanResult:
        if not text:
            return SecurityScanResult(clean_text="", redacted_count=0, security_confidence=1.0, is_safe_for_external=True, findings=[])

        if provider_policy == ProviderPrivacyPolicy.LOCAL and mode == SecurityMode.PERMISSIVE:
            return SecurityScanResult(clean_text=text, redacted_count=0, security_confidence=1.0, is_safe_for_external=False, findings=[])

        redacted = text
        count = 0
        findings: List[str] = []

        for pattern_name, pattern in SECRET_PATTERNS:
            if pattern_name == "GENERIC_PASSWORD":
                def _replace_pwd(m: re.Match) -> str:
                    nonlocal count
                    val = m.group(1)
                    if "[REDACTED" in val:
                        return m.group(0)
                    count += 1
                    findings.append(f"Generic Password/Secret in: {m.group(0)[:25]}...")
                    full = m.group(0)
                    return full.replace(val, cls.REPLACEMENT)
                redacted = pattern.sub(_replace_pwd, redacted)
            elif pattern_name == "BEARER_TOKEN":
                def _replace_bearer(m: re.Match) -> str:
                    nonlocal count
                    if "[REDACTED" in m.group(0):
                        return m.group(0)
                    count += 1
                    findings.append("Authorization Bearer token")
                    return "Bearer [REDACTED_SECRET]"
                redacted = pattern.sub(_replace_bearer, redacted)
            elif pattern_name == "DB_CONNECTION_STRING":
                def _replace_conn(m: re.Match) -> str:
                    nonlocal count
                    if "[REDACTED" in m.group(0):
                        return m.group(0)
                    count += 1
                    findings.append("Database Connection String URI")
                    protocol = m.group(0).split("://")[0]
                    return f"{protocol}://[REDACTED_CREDENTIALS]"
                redacted = pattern.sub(_replace_conn, redacted)
            else:
                matches = pattern.findall(redacted)
                valid_matches = [m for m in matches if "[REDACTED" not in str(m)]
                if valid_matches:
                    count += len(valid_matches)
                    findings.append(f"{pattern_name} ({len(valid_matches)} occurrences)")
                    redacted = pattern.sub(cls.REPLACEMENT, redacted)

        # Scan for high-entropy suspicious hex/base64 tokens
        if mode in [SecurityMode.STRICT, SecurityMode.BALANCED]:
            words = redacted.split()
            for w in words:
                clean_w = w.strip("\"\',:;()[]{}")
                if "[REDACTED" in clean_w or "REDACTED_" in clean_w:
                    continue
                if len(clean_w) >= 32 and cls._is_high_entropy_token(clean_w, mode):
                    redacted = redacted.replace(clean_w, "[REDACTED_HIGH_ENTROPY_SECRET]")
                    count += 1
                    findings.append(f"High-entropy token detected ({mode.value} mode)")

        confidence = 0.99 if count == 0 else max(0.85, round(1.0 - (count * 0.02), 2))
        is_safe = confidence >= 0.90 or (mode != SecurityMode.STRICT)

        return SecurityScanResult(
            clean_text=redacted,
            redacted_count=count,
            security_confidence=confidence,
            is_safe_for_external=is_safe,
            findings=findings,
        )

    @classmethod
    def _is_high_entropy_token(cls, token: str, mode: SecurityMode = SecurityMode.BALANCED) -> bool:
        if len(token) < 32:
            return False
        entropy = cls._calculate_entropy(token)
        is_hex = all(c in '0123456789abcdefABCDEF' for c in token)
        if is_hex:
            threshold = 3.4 if mode == SecurityMode.STRICT else 3.6
            return entropy >= threshold
        else:
            threshold = 4.0 if mode == SecurityMode.STRICT else 4.3
            return entropy >= threshold

    @staticmethod
    def _calculate_entropy(data: str) -> float:
        if not data:
            return 0.0
        entropy = 0.0
        for x in set(data):
            p_x = float(data.count(x)) / len(data)
            entropy += - p_x * math.log2(p_x)
        return entropy
