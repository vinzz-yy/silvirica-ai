from __future__ import annotations
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TaskOutcome:
    task_id: str
    task_type: str
    task_description: str
    context_tokens: int
    skills_selected: List[str]
    model_selected: str
    tests_passed: int = 0
    tests_total: int = 0
    validation_passed: bool = True
    escalated: bool = False
    latency_seconds: float = 0.0
    user_accepted: bool = True
    timestamp: float = field(default_factory=time.time)

    @property
    def is_verified_success(self) -> bool:
        """
        Anti-Hallucination Guard:
        Outcome learning MUST NOT blindly trust model confidence.
        Only verified signals count as success:
        1. Tests passed (tests_passed == tests_total and tests_total > 0)
        2. Validation passed without syntax errors or destructive commands
        3. User accepted without escalation
        """
        if self.tests_total > 0:
            return self.tests_passed == self.tests_total and self.validation_passed
        return self.validation_passed and not self.escalated and self.user_accepted


class OutcomeEngine:
    """
    Silvirica Outcome Learning Engine 2.0.
    Learns from verified task outcomes (tests passed, build passed, validation succeeded)
    to optimize future skill selection, context budgets, and model routing.
    Guards strictly against self-reinforcing errors.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.cwd() / ".silvirica" / "metrics" / "outcomes.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_outcomes (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    task_description TEXT,
                    context_tokens INTEGER,
                    skills_selected TEXT,
                    model_selected TEXT,
                    tests_passed INTEGER,
                    tests_total INTEGER,
                    validation_passed INTEGER,
                    escalated INTEGER,
                    latency_seconds REAL,
                    user_accepted INTEGER,
                    verified_success INTEGER,
                    timestamp REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_type ON task_outcomes(task_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_model ON task_outcomes(model_selected)")
            conn.commit()
        finally:
            conn.close()

    def record_outcome(self, outcome: TaskOutcome) -> None:
        verified = 1 if outcome.is_verified_success else 0
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO task_outcomes (
                    task_id, task_type, task_description, context_tokens,
                    skills_selected, model_selected, tests_passed, tests_total,
                    validation_passed, escalated, latency_seconds, user_accepted,
                    verified_success, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome.task_id,
                outcome.task_type,
                outcome.task_description[:500],
                outcome.context_tokens,
                json.dumps(outcome.skills_selected),
                outcome.model_selected,
                outcome.tests_passed,
                outcome.tests_total,
                1 if outcome.validation_passed else 0,
                1 if outcome.escalated else 0,
                outcome.latency_seconds,
                1 if outcome.user_accepted else 0,
                verified,
                outcome.timestamp,
            ))
            conn.commit()
        finally:
            conn.close()

    def get_best_model_for_task(self, task_type: str) -> Optional[str]:
        """
        Queries historical verified success rates across models for the given task type.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT model_selected,
                       COUNT(*) as total_runs,
                       SUM(verified_success) as successes,
                       AVG(latency_seconds) as avg_latency
                FROM task_outcomes
                WHERE task_type = ?
                GROUP BY model_selected
                HAVING total_runs >= 2
                ORDER BY (CAST(successes AS REAL) / total_runs) DESC, avg_latency ASC
                LIMIT 1
            """, (task_type,))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
        finally:
            conn.close()
        return None

    def get_optimal_skills_for_task(self, task_type: str) -> List[str]:
        """
        Queries skills that historically yielded verified successful outcomes.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT skills_selected
                FROM task_outcomes
                WHERE task_type = ? AND verified_success = 1
                ORDER BY timestamp DESC
                LIMIT 5
            """, (task_type,))
            rows = cursor.fetchall()
            all_skills: Dict[str, int] = {}
            for r in rows:
                try:
                    s_list = json.loads(r[0])
                    for s in s_list:
                        all_skills[s] = all_skills.get(s, 0) + 1
                except Exception:
                    pass
            sorted_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)
            return [s[0] for s in sorted_skills[:3]]
        finally:
            conn.close()

    def get_outcome_statistics(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) as total_tasks,
                       SUM(verified_success) as verified_successes,
                       SUM(escalated) as total_escalations,
                       AVG(latency_seconds) as avg_latency,
                       AVG(context_tokens) as avg_tokens
                FROM task_outcomes
            """)
            row = cursor.fetchone()
            if not row or row[0] == 0:
                return {
                    "total_tasks": 0,
                    "success_rate": 1.0,
                    "escalation_rate": 0.0,
                    "avg_latency": 0.0,
                    "avg_tokens": 0,
                }
            total = row[0]
            successes = row[1] or 0
            escalations = row[2] or 0
            avg_lat = row[3] or 0.0
            avg_tok = row[4] or 0.0

            return {
                "total_tasks": total,
                "success_rate": round(successes / total, 3),
                "escalation_rate": round(escalations / total, 3),
                "avg_latency": round(avg_lat, 3),
                "avg_tokens": int(avg_tok),
            }
        finally:
            conn.close()
