from __future__ import annotations
import re

class ContextCompressor:
    @classmethod
    def compress_text(cls, text: str) -> str:
        if not text:
            return ""
        code_blocks = []
        def _save_code(match):
            idx = len(code_blocks)
            code_blocks.append(match.group(0))
            return f"__SILVIRICA_CODE_BLOCK_{idx}__"
        text_masked = re.sub(r'```[\s\S]*?```', _save_code, text)
        text_masked = re.sub(r'\n{3,}', '\n\n', text_masked)
        text_masked = re.sub(r'[ \t]+', ' ', text_masked)
        for idx, block in enumerate(code_blocks):
            text_masked = text_masked.replace(f"__SILVIRICA_CODE_BLOCK_{idx}__", block)
        return text_masked.strip()

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        if not text:
            return 0
        words = len(text.split())
        chars = len(text)
        return max(words, int(chars / 3.8))
