from __future__ import annotations
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from silvirica.core.types import TelemetryEvent


class TelemetryStore:
    """
    SQLite-backed telemetry store for Silvirica Observatory.
    Tracks token savings, latency, cache hits, model routing, and verification.
    """

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
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    complexity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    estimated_baseline_tokens INTEGER NOT NULL,
                    tokens_saved INTEGER NOT NULL,
                    latency_seconds REAL NOT NULL,
                    cache_hit INTEGER NOT NULL,
                    zero_model INTEGER NOT NULL,
                    skills_activated TEXT,
                    files_retrieved INTEGER NOT NULL,
                    symbols_retrieved INTEGER NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS last_decision (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    decision_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

    def record_event(self, event: TelemetryEvent, decision_details: Optional[Dict[str, Any]] = None) -> None:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO telemetry (
                    query, complexity, category, model, input_tokens, output_tokens,
                    estimated_baseline_tokens, tokens_saved, latency_seconds,
                    cache_hit, zero_model, skills_activated, files_retrieved,
                    symbols_retrieved, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.query,
                    event.complexity.name if hasattr(event.complexity, 'name') else str(event.complexity),
                    event.category.value if hasattr(event.category, 'value') else str(event.category),
                    event.model_used,
                    event.input_tokens,
                    event.output_tokens,
                    event.estimated_baseline_tokens,
                    event.tokens_saved,
                    event.latency_seconds,
                    1 if event.cache_hit else 0,
                    1 if event.zero_model else 0,
                    json.dumps(event.skills_activated),
                    event.files_retrieved,
                    event.symbols_retrieved,
                    now,
                ),
            )
            if decision_details:
                conn.execute(
                    "INSERT OR REPLACE INTO last_decision (id, decision_json, updated_at) VALUES (1, ?, ?)",
                    (json.dumps(decision_details), now),
                )

    def get_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT
                    COUNT(*) as total_queries,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(estimated_baseline_tokens) as total_baseline_tokens,
                    SUM(tokens_saved) as total_tokens_saved,
                    AVG(latency_seconds) as avg_latency,
                    SUM(cache_hit) as total_cache_hits,
                    SUM(zero_model) as total_zero_model
                FROM telemetry
                """
            )
            row = cur.fetchone()
            total = row["total_queries"] or 0
            if total == 0:
                return {
                    "total_queries": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens_saved": 0,
                    "savings_percentage": 0.0,
                    "avg_latency": 0.0,
                    "cache_hit_rate": 0.0,
                    "zero_model_rate": 0.0,
                }

            baseline = row["total_baseline_tokens"] or 1
            saved = row["total_tokens_saved"] or 0
            savings_pct = (saved / baseline) * 100 if baseline > 0 else 0.0

            return {
                "total_queries": total,
                "total_input_tokens": row["total_input_tokens"] or 0,
                "total_output_tokens": row["total_output_tokens"] or 0,
                "total_tokens_saved": saved,
                "savings_percentage": round(min(99.0, max(0.0, savings_pct)), 1),
                "avg_latency": round(row["avg_latency"] or 0.0, 3),
                "cache_hit_rate": round(((row["total_cache_hits"] or 0) / total) * 100, 1),
                "zero_model_rate": round(((row["total_zero_model"] or 0) / total) * 100, 1),
            }

    def get_last_decision(self) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT decision_json FROM last_decision WHERE id = 1")
            row = cur.fetchone()
            if row and row["decision_json"]:
                return json.loads(row["decision_json"])
            return None
