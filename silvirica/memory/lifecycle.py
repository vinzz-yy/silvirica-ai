from __future__ import annotations
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional
from silvirica.core.types import MemoryRecord, MemoryStatus, MemoryType

class ReviewedMemoryManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
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
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    wikilinks TEXT,
                    related_files TEXT,
                    confidence REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'user',
                    verification_status TEXT DEFAULT 'UNVERIFIED',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    review_date TEXT
                )
                """
            )

    def propose_candidate(self, item_id: str, title: str, content: str, memory_type: MemoryType = MemoryType.PROJECT, tags: Optional[List[str]] = None, related_files: Optional[List[str]] = None, source: str = "ai_candidate") -> MemoryRecord:
        now = time.time()
        record = MemoryRecord(
            id=item_id, title=title, memory_type=memory_type, status=MemoryStatus.CANDIDATE,
            content=content, tags=tags or [], related_files=related_files or [],
            confidence=0.7, source=source, verification_status="UNVERIFIED", created_at=now, updated_at=now
        )
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_items 
                (id, title, memory_type, status, content, tags, wikilinks, related_files, confidence, source, verification_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (record.id, record.title, record.memory_type.value, record.status.value, record.content, json.dumps(record.tags), json.dumps(record.wikilinks), json.dumps(record.related_files), record.confidence, record.source, record.verification_status, record.created_at, record.updated_at),
            )
        return record

    def approve(self, item_id: str) -> bool:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute("UPDATE memory_items SET status = ?, verification_status = 'VERIFIED', confidence = 1.0, updated_at = ? WHERE id = ?", (MemoryStatus.APPROVED.value, now, item_id))
            return cur.rowcount > 0

    def reject(self, item_id: str) -> bool:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute("UPDATE memory_items SET status = ?, updated_at = ? WHERE id = ?", (MemoryStatus.ARCHIVED.value, now, item_id))
            return cur.rowcount > 0

    def get_active_memories(self, limit: int = 20) -> List[MemoryRecord]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM memory_items WHERE status IN (?, ?) ORDER BY updated_at DESC LIMIT ?", (MemoryStatus.ACTIVE.value, MemoryStatus.APPROVED.value, limit))
            return [self._row_to_record(r) for r in cur.fetchall()]

    def search_active(self, query: str, limit: int = 10) -> List[MemoryRecord]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM memory_items WHERE status IN (?, ?) AND (title LIKE ? OR content LIKE ? OR tags LIKE ?) ORDER BY confidence DESC LIMIT ?", (MemoryStatus.ACTIVE.value, MemoryStatus.APPROVED.value, f"%{query}%", f"%{query}%", f"%{query}%", limit))
            return [self._row_to_record(r) for r in cur.fetchall()]

    def _row_to_record(self, r: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=r["id"], title=r["title"], memory_type=MemoryType(r["memory_type"]), status=MemoryStatus(r["status"]),
            content=r["content"], tags=json.loads(r["tags"] or "[]"), wikilinks=json.loads(r["wikilinks"] or "[]"),
            related_files=json.loads(r["related_files"] or "[]"), confidence=r["confidence"], source=r["source"],
            verification_status=r["verification_status"], created_at=r["created_at"], updated_at=r["updated_at"], review_date=r["review_date"]
        )
