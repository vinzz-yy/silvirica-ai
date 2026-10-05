from __future__ import annotations
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional
from silvirica.core.types import SymbolInfo, SymbolKind


class SymbolIndex:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    container TEXT,
                    signature TEXT,
                    docstring TEXT,
                    parameters TEXT,
                    code_hash TEXT,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind)")

    def save_symbols(self, file_path: str, symbols: List[SymbolInfo], code_hash: str = "") -> None:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
            for s in symbols:
                conn.execute(
                    """
                    INSERT INTO symbols (name, kind, file_path, start_line, end_line, container, signature, docstring, parameters, code_hash, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        s.name,
                        s.kind.value if isinstance(s.kind, SymbolKind) else str(s.kind),
                        s.file_path,
                        s.start_line,
                        s.end_line,
                        s.container,
                        s.signature,
                        s.docstring,
                        json.dumps(s.parameters),
                        code_hash or s.code_hash,
                        now,
                    ),
                )

    def find_by_name(self, name: str, exact: bool = False) -> List[SymbolInfo]:
        with self._get_connection() as conn:
            if exact:
                cur = conn.execute("SELECT * FROM symbols WHERE name = ? COLLATE NOCASE", (name,))
            else:
                cur = conn.execute("SELECT * FROM symbols WHERE name LIKE ? COLLATE NOCASE", (f"%{name}%",))
            return [self._row_to_symbol(row) for row in cur.fetchall()]

    def count(self) -> int:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM symbols")
            return cur.fetchone()[0]

    def _row_to_symbol(self, row: sqlite3.Row) -> SymbolInfo:
        params = []
        if row["parameters"]:
            try:
                params = json.loads(row["parameters"])
            except Exception:
                params = []
        kind_str = row["kind"]
        try:
            kind = SymbolKind(kind_str)
        except ValueError:
            kind = SymbolKind.FUNCTION
        return SymbolInfo(
            name=row["name"],
            kind=kind,
            file_path=row["file_path"],
            start_line=row["start_line"],
            end_line=row["end_line"],
            container=row["container"],
            signature=row["signature"],
            docstring=row["docstring"],
            parameters=params,
            code_hash=row["code_hash"] or "",
        )

def extract_symbol_snippet(root_path: Path, symbol: SymbolInfo) -> str:
    file_full = root_path / symbol.file_path
    if not file_full.exists():
        return ""
    try:
        lines = file_full.read_text(encoding="utf-8", errors="ignore").splitlines()
        start = max(0, symbol.start_line - 1)
        end = min(len(lines), symbol.end_line)
        return "\n".join(lines[start:end])
    except Exception:
        return ""
