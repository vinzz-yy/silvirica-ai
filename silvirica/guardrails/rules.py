from __future__ import annotations
import re
from typing import List, Optional, Tuple
from silvirica.core.config import GuardrailsConfig
from silvirica.core.types import ApprovalTier, RiskLevel


class GuardrailEngine:
    """
    Project Guardrails and Safety Validation.
    Blocks prohibited operations (destructive database changes, secret commitments, unauthorized file modifications).
    """

    DESTRUCTIVE_DB_PATTERNS = [
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        re.compile(r'\bDROP\s+DATABASE\b', re.IGNORECASE),
        re.compile(r'\bTRUNCATE\s+TABLE\b', re.IGNORECASE),
        re.compile(r'\bDELETE\s+FROM\s+\w+\s*;', re.IGNORECASE),
    ]

    MIGRATION_PATTERNS = [
        re.compile(r'/migrations?/', re.IGNORECASE),
        re.compile(r'\\migrations?\\', re.IGNORECASE),
        re.compile(r'schema\.rb', re.IGNORECASE),
    ]

    def __init__(self, config: Optional[GuardrailsConfig] = None):
        self.config = config or GuardrailsConfig()

    def evaluate_action(
        self,
        action_type: str,
        target_path: Optional[str] = None,
        code_content: Optional[str] = None,
    ) -> Tuple[bool, ApprovalTier, str]:
        """
        Returns (is_allowed, approval_tier, reason).
        """
        # 1. Read operations are always SAFE
        if action_type in ["read_file", "search", "list_dir", "symbol_lookup", "graph_query"]:
            return True, ApprovalTier.SAFE, "Read-only operation allowed."

        # 2. Check destructive DB operations
        if self.config.block_destructive_db and code_content:
            for pat in self.DESTRUCTIVE_DB_PATTERNS:
                if pat.search(code_content):
                    return False, ApprovalTier.HIGH_RISK, f"Destructive database operation blocked: {pat.pattern}"

        # 3. Check migration file modifications
        if self.config.block_migration_auto_edit and target_path:
            for pat in self.MIGRATION_PATTERNS:
                if pat.search(target_path) and action_type in ["edit_file", "delete_file", "overwrite_file"]:
                    return False, ApprovalTier.HIGH_RISK, "Direct automatic modification of database migration files is blocked."

        # 4. Check credential/secret modifications
        if target_path and any(target_path.endswith(s) for s in [".env", ".env.production", "id_rsa", "credentials.json"]):
            if action_type in ["edit_file", "overwrite_file", "delete_file"]:
                return False, ApprovalTier.HIGH_RISK, "Direct modification of environment/secret credential files is blocked."

        # Standard file modification requires REVIEW tier
        if action_type in ["edit_file", "overwrite_file", "create_file"]:
            return True, ApprovalTier.REVIEW, "File modification allowed under review."

        return True, ApprovalTier.SAFE, "Action approved."
