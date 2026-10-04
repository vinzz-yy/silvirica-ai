from __future__ import annotations
import hashlib
from pathlib import Path

def compute_file_hash(file_path: Path) -> str:
    if not file_path.exists() or not file_path.is_file():
        return ""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""
