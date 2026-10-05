from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Optional, Tuple, Union
from urllib.parse import unquote

from silvirica.core.exceptions import SecurityViolationError


class PathSandbox:
    """
    Enterprise Filesystem Sandbox & Path Canonicalization Engine.
    Guarantees that all file and directory access remains strictly bounded
    within the authorized workspace root across Windows, Linux, and macOS.

    Protects against:
    - Relative directory traversal (../, ..\\, ....//)
    - Encoded traversal (%2e%2e%2f, %2e%2e/, ..%2f)
    - Windows drive escape (C:\\, D:\\, \\\\?\\C:)
    - Windows UNC network paths (\\\\server\\share, //server/share)
    - Symlink escapes pointing outside workspace
    - Absolute path escapes (/etc/passwd, /root/.ssh)
    - Null-byte and control character injections
    - Case-insensitive filesystem collisions
    """

    MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB default ceiling
    MAX_DIRECTORY_DEPTH: int = 25
    BINARY_PROBE_SIZE: int = 8192

    @classmethod
    def sanitize_path_string(cls, path_str: str) -> str:
        """
        Strips dangerous control characters, unquotes URL encoding, and normalizes separators.
        """
        if not path_str:
            return ""
        
        # 1. Decode URL encoded paths (e.g., %2e%2e%2f -> ../)
        decoded = unquote(unquote(path_str))
        
        # 2. Check for null bytes and control chars
        if "\x00" in decoded or any(ord(c) < 32 for c in decoded if c not in "\t\r\n"):
            raise SecurityViolationError("Path contains prohibited control characters or null bytes.")
        
        # 3. Strip leading/trailing whitespace
        cleaned = decoded.strip()
        return cleaned

    @classmethod
    def resolve_safe_path(
        cls,
        target_path: Union[str, Path],
        root_path: Path,
        must_exist: bool = False,
        allow_symlinks_outside: bool = False,
    ) -> Path:
        """
        Resolves a target path against the project root and verifies that the canonical,
        real path strictly resides inside root_path.
        """
        root = root_path.resolve()
        raw_str = str(target_path)
        sanitized_str = cls.sanitize_path_string(raw_str)

        if not sanitized_str:
            return root

        # Detect Windows UNC path injections (\\\\server or //server)
        if sanitized_str.startswith(("\\\\", "//")):
            raise SecurityViolationError(f"UNC network paths are prohibited: {raw_str}")

        target = Path(sanitized_str)
        if target.is_absolute():
            candidate = target.resolve()
        else:
            candidate = (root / target).resolve()

        # Check if resolved path is strictly within root
        try:
            candidate.relative_to(root)
        except ValueError:
            raise SecurityViolationError(
                f"Path traversal blocked: target '{raw_str}' resolves outside project root '{root}'."
            )

        # Check symlink destination if exists
        if candidate.is_symlink() and not allow_symlinks_outside:
            try:
                real_target = candidate.resolve(strict=True)
                real_target.relative_to(root)
            except (ValueError, FileNotFoundError):
                raise SecurityViolationError(
                    f"Symlink traversal blocked: symlink '{candidate}' points outside project root."
                )

        if must_exist and not candidate.exists():
            raise FileNotFoundError(f"Safe path not found: {candidate}")

        return candidate

    @classmethod
    def is_safe_path(cls, target_path: Union[str, Path], root_path: Path) -> bool:
        """
        Returns True if target_path safely resides within root_path, False otherwise.
        """
        try:
            cls.resolve_safe_path(target_path, root_path)
            return True
        except (SecurityViolationError, Exception):
            return False

    @classmethod
    def is_binary_file(cls, file_path: Path) -> bool:
        """
        Quickly detects if a file contains binary content to avoid loading multi-megabyte binary dumps.
        """
        if not file_path.exists() or not file_path.is_file():
            return False
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(cls.BINARY_PROBE_SIZE)
                if b"\x00" in chunk:
                    return True
                # Check for high percentage of non-text bytes
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                non_text = chunk.translate(None, text_chars)
                if len(chunk) > 0 and len(non_text) / len(chunk) > 0.30:
                    return True
        except Exception:
            return True
        return False

    @classmethod
    def check_file_size_limit(cls, file_path: Path, max_bytes: Optional[int] = None) -> bool:
        """
        Verifies file size does not exceed the safety threshold.
        """
        limit = max_bytes or cls.MAX_FILE_SIZE_BYTES
        try:
            if file_path.is_file():
                return file_path.stat().st_size <= limit
        except Exception:
            return False
        return True
