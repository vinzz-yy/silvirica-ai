from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List

class GitWatcher:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()

    def has_git(self) -> bool:
        return (self.root_path / ".git").exists()

    def get_modified_files(self) -> List[str]:
        if not self.has_git():
            return []
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.root_path),
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return []
            files = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    files.append(parts[1].strip('"'))
            return files
        except Exception:
            return []

    def get_diff_summary(self, max_files: int = 10) -> str:
        if not self.has_git():
            return "Git repository not detected."
        try:
            result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=str(self.root_path),
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() or "No uncommitted changes."
        except Exception:
            return "Could not retrieve git diff."
