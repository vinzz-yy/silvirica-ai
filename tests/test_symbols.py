from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.core.types import SymbolKind
from silvirica.repository.ast_parser import MultiLanguageASTParser
from silvirica.repository.symbols import SymbolIndex


class TestSymbolExtraction(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "symbols.db"
        self.index = SymbolIndex(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_python_ast_parsing(self) -> None:
        py_code = """
class UserController:
    \"\"\"Handles user authentication.\"\"\"
    def login(self, username, password):
        return True

def standalone_helper(x, y):
    return x + y
"""
        file_path = self.root / "users.py"
        file_path.write_text(py_code, encoding="utf-8")

        symbols = MultiLanguageASTParser.parse_file(file_path, self.root)
        self.assertTrue(len(symbols) >= 3)

        class_sym = next(s for s in symbols if s.kind == SymbolKind.CLASS)
        self.assertEqual(class_sym.name, "UserController")
        self.assertEqual(class_sym.docstring, "Handles user authentication.")

        login_sym = next(s for s in symbols if s.name == "login")
        self.assertEqual(login_sym.kind, SymbolKind.METHOD)
        self.assertEqual(login_sym.container, "UserController")

        self.index.save_symbols("users.py", symbols)
        self.assertEqual(self.index.count(), len(symbols))

        results = self.index.find_by_name("UserController", exact=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "UserController")

    def test_php_parsing(self) -> None:
        php_code = """<?php
class AuthController {
    public function handleLogin($request) {
        return response();
    }
}
Route::post('/api/login', 'AuthController@handleLogin');
"""
        file_path = self.root / "AuthController.php"
        file_path.write_text(php_code, encoding="utf-8")

        symbols = MultiLanguageASTParser.parse_file(file_path, self.root)
        self.assertTrue(len(symbols) >= 2)

        names = [s.name for s in symbols]
        self.assertIn("AuthController", names)
        self.assertIn("handleLogin", names)


if __name__ == "__main__":
    unittest.main()
