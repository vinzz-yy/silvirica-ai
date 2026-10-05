from __future__ import annotations
import unittest
from silvirica.models.validator import ResultValidator


class TestResultValidator(unittest.TestCase):
    def test_valid_python_code(self) -> None:
        code = "Here is the implementation:\n```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```"
        result = ResultValidator.validate_response(code, task="Add function", language="python")
        self.assertTrue(result.is_valid)
        self.assertFalse(result.needs_escalation)
        self.assertEqual(len(result.errors), 0)

    def test_invalid_python_syntax_triggers_escalation(self) -> None:
        broken_code = "```python\ndef broken_func(\n    invalid syntax here ???\n```"
        result = ResultValidator.validate_response(broken_code, task="Fix function", language="python")
        self.assertFalse(result.is_valid)
        self.assertTrue(result.needs_escalation)
        self.assertTrue(any("Syntax Error" in err for err in result.errors))

    def test_destructive_sql_command_blocked(self) -> None:
        destructive_code = "```sql\nDROP DATABASE production;\n```"
        result = ResultValidator.validate_response(destructive_code, task="Clean DB", prohibit_destructive=True)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.needs_escalation)
        self.assertTrue(any("destructive" in err.lower() for err in result.errors))

    def test_empty_response(self) -> None:
        result = ResultValidator.validate_response("", task="Empty test")
        self.assertFalse(result.is_valid)
        self.assertTrue(result.needs_escalation)


if __name__ == "__main__":
    unittest.main()
