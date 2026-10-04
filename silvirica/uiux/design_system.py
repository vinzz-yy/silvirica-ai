from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List, Set

class DesignSystemExtractor:
    COLOR_HEX_PATTERN = re.compile(r'#(?:[0-9a-fA-F]{3}){1,2}\b')
    CSS_VAR_PATTERN = re.compile(r'--([A-Za-z0-9_-]+)\s*:\s*([^;]+);')

    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()

    def extract_tokens(self) -> Dict[str, Any]:
        colors: Set[str] = set()
        css_vars: Dict[str, str] = {}
        has_tailwind = False
        for path in self.root_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in [".css", ".scss", ".vue", ".jsx", ".tsx"]:
                if any(part in ["node_modules", "vendor", ".git"] for part in path.parts):
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    if "@tailwind" in content or "tailwind" in content:
                        has_tailwind = True
                    for m in self.COLOR_HEX_PATTERN.finditer(content):
                        colors.add(m.group(0).lower())
                    for m in self.CSS_VAR_PATTERN.finditer(content):
                        css_vars[f"--{m.group(1)}"] = m.group(2).strip()
                except Exception:
                    pass
        return {
            "has_tailwind": has_tailwind, "colors_detected": sorted(list(colors))[:20],
            "css_variables_count": len(css_vars), "css_variables": {k: css_vars[k] for k in list(css_vars.keys())[:15]},
        }
