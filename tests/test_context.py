from __future__ import annotations
import unittest
from silvirica.context.compiler import SmartContextCompiler
from silvirica.context.deduplicator import ContextDeduplicator
from silvirica.context.redactor import SecretRedactor
from silvirica.core.config import ProjectConfig
from silvirica.core.types import ComplexityLevel


class TestContextCompiler(unittest.TestCase):
    def test_secret_redaction(self) -> None:
        raw_text = "API_KEY = 'sk-1234567890abcdef1234567890abcdef12345678'\ngh_token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'"
        redacted, count = SecretRedactor.redact(raw_text)
        self.assertNotIn("sk-1234567890abcdef", redacted)
        self.assertNotIn("ghp_ABCDEF", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)
        self.assertTrue(count >= 2)

    def test_context_deduplication(self) -> None:
        lines = [
            "Error: Connection timeout at line 42",
            "Error: Connection timeout at line 42",
            "Error: Connection timeout at line 42",
            "Normal output",
        ]
        deduped = ContextDeduplicator.deduplicate_lines(lines)
        self.assertTrue(len(deduped) < len(lines))
        self.assertTrue(any("repeated" in d for d in deduped))

    def test_smart_context_compilation(self) -> None:
        config = ProjectConfig()
        compiler = SmartContextCompiler(config)

        symbols = ["[app/Users.php:1-50] UserController", "[app/Auth.php:10-30] AuthMiddleware"]
        memory = ["Memory [[Auth]]: Standard JWT timeout is 3600s."]
        skills = "defensive security guidelines"

        bundle = compiler.compile(
            task="Fix JWT authentication timeout in AuthController",
            complexity=ComplexityLevel.LEVEL_2_STANDARD,
            symbols=symbols,
            memory=memory,
            skills=skills,
        )

        self.assertIsNotNone(bundle.prompt)
        self.assertTrue(bundle.input_tokens > 0)
        self.assertTrue(bundle.token_budget >= bundle.input_tokens)
        self.assertIn("Fix JWT authentication", bundle.prompt)


if __name__ == "__main__":
    unittest.main()
