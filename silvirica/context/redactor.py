from __future__ import annotations
import re
from typing import List, Tuple

SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("OPENAI_API_KEY", re.compile(r'sk-[a-zA-Z0-9_-]{20,}', re.IGNORECASE)),
    ("ANTHROPIC_API_KEY", re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}', re.IGNORECASE)),
    ("GITHUB_TOKEN", re.compile(r'gh[pousr]-[a-zA-Z0-9]{36,}', re.IGNORECASE)),
    ("AWS_KEY", re.compile(r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}', re.IGNORECASE)),
    ("PRIVATE_KEY", re.compile(r'-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA|PRIVATE)?\s*KEY-----[\s\S]+?-----END\s+(?:RSA|OPENSSH|EC|DSA|PRIVATE)?\s*KEY-----', re.IGNORECASE)),
    ("GENERIC_PASSWORD", re.compile(r'(?:password|secret|passwd|token|apikey|api_key)\s*[:=]\s*["\']([^"\']{8,})["\']', re.IGNORECASE)),
    ("JWT_TOKEN", re.compile(r'eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', re.IGNORECASE)),
]

class SecretRedactor:
    REPLACEMENT = "[REDACTED_SECRET]"
    @classmethod
    def redact(cls, text: str) -> Tuple[str, int]:
        if not text:
            return "", 0
        redacted = text
        count = 0
        for pattern_name, pattern in SECRET_PATTERNS:
            if pattern_name == "GENERIC_PASSWORD":
                def _replace_pwd(m):
                    nonlocal count
                    count += 1
                    full = m.group(0)
                    val = m.group(1)
                    return full.replace(val, cls.REPLACEMENT)
                redacted = pattern.sub(_replace_pwd, redacted)
            else:
                matches = pattern.findall(redacted)
                if matches:
                    count += len(matches)
                    redacted = pattern.sub(cls.REPLACEMENT, redacted)
        return redacted, count
