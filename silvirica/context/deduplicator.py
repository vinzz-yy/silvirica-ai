from __future__ import annotations
import re
from typing import Any, Dict, List, Set


class ContextDeduplicator:
    @classmethod
    def deduplicate_items(cls, items: List[str]) -> List[str]:
        seen: Set[str] = set()
        deduped: List[str] = []
        for it in items:
            cleaned = it.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                deduped.append(it)
        return deduped

    @classmethod
    def deduplicate_lines(cls, lines: List[str]) -> List[str]:
        if not lines:
            return []
        deduped: List[str] = []
        prev_line: str = ""
        repeat_count: int = 1

        for line in lines:
            norm = line.strip()
            if norm == prev_line:
                repeat_count += 1
            else:
                if repeat_count > 1:
                    deduped.append(f"  [Previous line repeated {repeat_count} times: {prev_line}]")
                    repeat_count = 1
                deduped.append(line)
                prev_line = norm

        if repeat_count > 1:
            deduped.append(f"  [Previous line repeated {repeat_count} times: {prev_line}]")

        return deduped

    @classmethod
    def deduplicate_errors(cls, error_traces: List[str]) -> str:
        if not error_traces:
            return "No errors."
        unique_errors: Dict[str, int] = {}
        for err in error_traces:
            err_clean = err.strip()
            unique_errors[err_clean] = unique_errors.get(err_clean, 0) + 1

        out = []
        for err, count in unique_errors.items():
            if count > 1:
                out.append(f"[Occurred {count} times]\n{err}")
            else:
                out.append(err)
        return "\n\n".join(out)
