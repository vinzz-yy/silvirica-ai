from __future__ import annotations
import ast
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from silvirica.core.types import RoutingCategory


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    needs_escalation: bool = False
    escalation_reason: Optional[str] = None
    repaired_code: Optional[str] = None


class ResultValidator:
    """
    Validates AI-generated code results for syntactic correctness,
    safety, and completeness before returning to developer/IDE.
    """

    @classmethod
    def validate_response(
        cls,
        code_or_text: str,
        task: str,
        language: Optional[str] = None,
        prohibit_destructive: bool = True,
    ) -> ValidationResult:
        errors = []
        warnings = []
        needs_escalation = False
        escalation_reason = None

        if not code_or_text or len(code_or_text.strip()) == 0:
            return ValidationResult(
                is_valid=False,
                errors=["Empty response generated."],
                needs_escalation=True,
                escalation_reason="Model returned empty output.",
            )

        # 1. Extract fenced code blocks
        code_blocks = re.findall(r'```(?:[a-zA-Z0-9_\-]+)?\n([\s\S]*?)```', code_or_text)

        # 2. Check destructive commands
        if prohibit_destructive:
            destructive_patterns = [
                r'\bDROP\s+DATABASE\b',
                r'\bDROP\s+TABLE\b',
                r'\bTRUNCATE\s+TABLE\b',
                r'\brm\s+-rf\s+/(?:\s|$)',
                r'\bDELETE\s+FROM\s+\w+\s*;',
            ]
            for pat in destructive_patterns:
                if re.search(pat, code_or_text, re.IGNORECASE):
                    errors.append(f"Response contains prohibited destructive pattern: {pat}")
                    needs_escalation = True
                    escalation_reason = "Destructive database or filesystem command detected."

        # 3. Language-specific syntax check
        for block in code_blocks:
            lang = language.lower() if language else "generic"
            if lang == "python" or "def " in block or "import " in block:
                try:
                    ast.parse(block)
                except SyntaxError as e:
                    errors.append(f"Python Syntax Error in generated code: {e.msg} (line {e.lineno})")
                    needs_escalation = True
                    escalation_reason = f"Syntax error: {e.msg}"

            # JS/TS bracket balancing check
            if lang in ["javascript", "typescript", "js", "ts", "jsx", "tsx"] or "const " in block or "function " in block:
                if block.count("{") != block.count("}") or block.count("(") != block.count(")"):
                    warnings.append("Unbalanced braces or parentheses in JavaScript/TypeScript block.")

        # 4. Check for hallucinated placeholder text
        placeholder_patterns = [
            r'// TODO: implement this',
            r'# TODO: write your code here',
            r'/\* insert your logic here \*/',
        ]
        for pat in placeholder_patterns:
            if re.search(pat, code_or_text, re.IGNORECASE):
                warnings.append("Incomplete implementation with placeholder comments.")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            needs_escalation=needs_escalation,
            escalation_reason=escalation_reason,
        )
