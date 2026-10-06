"""
Safe YAML Compatibility Layer for Silvirica AI.
Provides zero-dependency fallback for parsing and dumping YAML/frontmatter
when PyYAML is not installed in the current Python environment,
and transparently leverages PyYAML when available.
"""

from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import yaml as _pyyaml
    _HAS_PYYAML = True
except (ImportError, ModuleNotFoundError):
    _pyyaml = None
    _HAS_PYYAML = False


def safe_load(stream: Union[str, Any]) -> Any:
    """
    Safely parses YAML content without code execution vulnerabilities.
    """
    if _HAS_PYYAML and _pyyaml is not None:
        return _pyyaml.safe_load(stream)
    
    # Built-in lightweight safe YAML parser fallback
    if hasattr(stream, "read"):
        content = stream.read()
    else:
        content = str(stream)
    
    return _parse_yaml_fallback(content)


def safe_dump(data: Any, stream: Optional[Any] = None, **kwargs: Any) -> Optional[str]:
    """
    Safely dumps structured data into YAML format.
    """
    if _HAS_PYYAML and _pyyaml is not None:
        return _pyyaml.safe_dump(data, stream, **kwargs)
    
    result = _dump_yaml_fallback(data)
    if stream is not None:
        if hasattr(stream, "write"):
            stream.write(result)
            return None
    return result


def _parse_yaml_fallback(content: str) -> Any:
    """
    Lightweight, deterministic YAML subset parser for config and frontmatter.
    Handles dictionaries, lists, booleans, numbers, strings, and comments.
    """
    if not content or not content.strip():
        return {}
    
    text = content.strip()
    # Try JSON parsing first if applicable
    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        try:
            return json.loads(text)
        except Exception:
            pass

    lines = text.splitlines()
    root: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[Any]] = None
    stack: List[Tuple[int, Dict[str, Any]]] = [(0, root)]

    for raw_line in lines:
        # Strip comments
        line_clean = raw_line.split("#", 1)[0].rstrip()
        if not line_clean.strip():
            continue
        
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = line_clean.strip()

        # Handle list items "- value"
        if stripped.startswith("- "):
            val_str = stripped[2:].strip()
            parsed_val = _parse_scalar(val_str)
            if current_list is not None:
                current_list.append(parsed_val)
            elif current_key and isinstance(root.get(current_key), list):
                root[current_key].append(parsed_val)
            continue

        # Handle key: value pairs
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            key = k.strip().strip('"\'')
            val_str = v.strip()

            if not val_str:
                # Nested map or upcoming list
                sub_dict: Dict[str, Any] = {}
                root[key] = sub_dict
                current_key = key
                current_list = None
            elif val_str.startswith("[") and val_str.endswith("]"):
                # Inline list [a, b, c]
                items = [s.strip().strip('"\'') for s in val_str[1:-1].split(",") if s.strip()]
                root[key] = [_parse_scalar(it) for it in items]
                current_key = key
                current_list = root[key]
            else:
                root[key] = _parse_scalar(val_str)
                current_key = key
                current_list = None

    return root


def _parse_scalar(val: str) -> Any:
    cleaned = val.strip()
    if not cleaned:
        return ""
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        return cleaned[1:-1]
    lower = cleaned.lower()
    if lower in ["true", "yes", "on"]:
        return True
    if lower in ["false", "no", "off"]:
        return False
    if lower in ["null", "none", "~"]:
        return None
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return cleaned


def _dump_yaml_fallback(data: Any, indent: int = 0) -> str:
    space = "  " * indent
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{space}{k}:")
                lines.append(_dump_yaml_fallback(v, indent + 1))
            elif isinstance(v, list) and not v:
                lines.append(f"{space}{k}: []")
            elif isinstance(v, dict) and not v:
                lines.append(f"{space}{k}: {{}}")
            else:
                lines.append(f"{space}{k}: {_format_scalar(v)}")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{space}-")
                lines.append(_dump_yaml_fallback(item, indent + 1))
            else:
                lines.append(f"{space}- {_format_scalar(item)}")
        return "\n".join(lines)
    else:
        return f"{space}{_format_scalar(data)}"


def _format_scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if ":" in s or "#" in s or "\n" in s or s.startswith(("-", "[", "{", "*", "&", "!")):
        return json.dumps(s)
    return s
