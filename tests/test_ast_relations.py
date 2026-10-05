from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from silvirica.core.types import RelationKind, SymbolKind
from silvirica.repository.ast_parser import MultiLanguageASTParser


class TestASTRelations(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_python_calls_and_imports(self) -> None:
        py_code = """
import os
from datetime import datetime

class UserService:
    def getUser(self, user_id):
        self.validate(user_id)
        return {"id": user_id}

    def validate(self, uid):
        pass
"""
        f = self.root / "user_service.py"
        f.write_text(py_code, encoding="utf-8")

        symbols, relations = MultiLanguageASTParser.parse_file_with_relations(f, self.root)
        self.assertTrue(len(symbols) >= 3)
        self.assertTrue(len(relations) >= 2)

        import_rels = [r for r in relations if r.relation == RelationKind.IMPORTS]
        self.assertTrue(any("os" in r.target_name for r in import_rels))

        call_rels = [r for r in relations if r.relation == RelationKind.CALLS]
        self.assertTrue(any("validate" in r.target_name for r in call_rels))

    def test_php_laravel_routes_and_controllers(self) -> None:
        php_code = """<?php
namespace App\\Http\\Controllers;
use App\\Models\\User;

class AuthController extends Controller {
    public function login() {
        return view('auth.login');
    }
}
Route::post('/api/v1/login', [AuthController::class, 'login']);
"""
        f = self.root / "AuthController.php"
        f.write_text(php_code, encoding="utf-8")

        symbols, relations = MultiLanguageASTParser.parse_file_with_relations(f, self.root)
        self.assertTrue(len(symbols) >= 3)

        routes_to = [r for r in relations if r.relation == RelationKind.ROUTES_TO]
        self.assertTrue(len(routes_to) >= 1)
        self.assertIn("AuthController@login", routes_to[0].target_name)


if __name__ == "__main__":
    unittest.main()
