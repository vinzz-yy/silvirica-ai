from __future__ import annotations
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class SecurityMode(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


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


SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("OPENAI_API_KEY", re.compile(r'sk-[a-zA-Z0-9_-]{20,}', re.IGNORECASE)),
    ("ANTHROPIC_API_KEY", re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}', re.IGNORECASE)),
    ("GITHUB_TOKEN", re.compile(r'gh[pousr]-[a-zA-Z0-9]{36,}', re.IGNORECASE)),
    ("AWS_KEY", re.compile(r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}', re.IGNORECASE)),
    ("STRIPE_KEY", re.compile(r'(?:sk|pk)_(?:test|live)_[0-9a-zA-Z]{20,}', re.IGNORECASE)),
    ("SLACK_TOKEN", re.compile(r'xox[baprs]-[0-9a-zA-Z]{10,}', re.IGNORECASE)),
    ("DB_CONNECTION_STRING", re.compile(r'(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp):\/\/[^\s"\'<>]+', re.IGNORECASE)),
    ("BEARER_TOKEN", re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{20,}', re.IGNORECASE)),
    ("PRIVATE_KEY", re.compile(r'-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA|PGP|ENCRYPTED)?\s*PRIVATE\s*KEY-----[\s\S]+?-----END\s+(?:RSA|OPENSSH|EC|DSA|PGP|ENCRYPTED)?\s*PRIVATE\s*KEY-----', re.IGNORECASE)),
    ("GENERIC_PASSWORD", re.compile(r'(?:password|secret|passwd|token|apikey|api_key|client_secret)\s*[:=]\s*["\']([^"\']{8,})["\']', re.IGNORECASE)),
    ("JWT_TOKEN", re.compile(r'eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', re.IGNORECASE)),
]


class SecretRedactor:
    """
    Enterprise Pre-Model Security Scanner & Redactor 2.0.
    Supports:
    - Multi-engine regex secret redaction
    - Shannon entropy verification
    - Security confidence scoring (0.0 to 1.0)
    - Security modes (strict, balanced, permissive)
    - Provider privacy policy enforcement (local vs external vs trusted)
    """

    REPLACEMENT = "[REDACTED_SECRET]"

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

        # If local provider and policy allows sensitive context, return raw text
        if provider_policy == ProviderPrivacyPolicy.LOCAL and mode == SecurityMode.PERMISSIVE:
            return SecurityScanResult(clean_text=text, redacted_count=0, security_confidence=1.0, is_safe_for_external=False, findings=[])

        redacted = text
        count = 0
        findings: List[str] = []

        for pattern_name, pattern in SECRET_PATTERNS:
            if pattern_name == "GENERIC_PASSWORD":
                def _replace_pwd(m):
                    nonlocal count
                    count += 1
                    findings.append(f"Generic Password in: {m.group(0)[:20]}...")
                    full = m.group(0)
                    val = m.group(1)
                    return full.replace(val, cls.REPLACEMENT)
                redacted = pattern.sub(_replace_pwd, redacted)
            elif pattern_name == "BEARER_TOKEN":
                def _replace_bearer(m):
                    nonlocal count
                    count += 1
                    findings.append("Authorization Bearer token")
                    return "Bearer [REDACTED_SECRET]"
                redacted = pattern.sub(_replace_bearer, redacted)
            elif pattern_name == "DB_CONNECTION_STRING":
                def _replace_conn(m):
                    nonlocal count
                    count += 1
                    findings.append("Database Connection String URI")
                    protocol = m.group(0).split("://")[0]
                    return f"{protocol}://[REDACTED_CREDENTIALS]"
                redacted = pattern.sub(_replace_conn, redacted)
            else:
                matches = pattern.findall(redacted)
                if matches:
                    count += len(matches)
                    findings.append(f"{pattern_name} ({len(matches)} occurrences)")
                    redacted = pattern.sub(cls.REPLACEMENT, redacted)

        # Scan for high-entropy suspicious hex/base64 tokens
        if mode in [SecurityMode.STRICT, SecurityMode.BALANCED]:
            words = redacted.split()
            for w in words:
                clean_w = w.strip("\"\',:;()[]{}")
                if len(clean_w) >= 32 and cls._is_high_entropy_token(clean_w, mode):
                    if clean_w not in cls.REPLACEMENT and not clean_w.startswith("[REDACTED"):
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
