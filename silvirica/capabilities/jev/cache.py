from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from silvirica.capabilities.jev.schemas import JevDecision
from silvirica.security.sandbox import PathSandbox


class JevDecisionCache:
    """
    Sub-millisecond persistent decision cache for JEV.
    Caches routing, complexity, skill set, and context budget decisions based on
    task fingerprint, project state, and language context.
    """

    def __init__(self, cache_dir: Path, default_ttl_seconds: int = 3600):
        self.cache_dir = cache_dir.resolve()
        self.cache_file = self.cache_dir / "jev_decisions.json"
        self.default_ttl = default_ttl_seconds
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {"hits": 0, "misses": 0, "sets": 0}
        self._load_from_disk()

    @staticmethod
    def generate_fingerprint(
        task: str,
        project_name: str = "",
        state_hash: str = "",
        languages: Optional[list[str]] = None,
    ) -> str:
        hasher = hashlib.sha256()
        hasher.update(task.strip().lower().encode("utf-8"))
        if project_name:
            hasher.update(project_name.encode("utf-8"))
        if state_hash:
            hasher.update(state_hash.encode("utf-8"))
        if languages:
            hasher.update(",".join(sorted(languages)).encode("utf-8"))
        return f"jev_{hasher.hexdigest()[:20]}"

    def get(self, key: str, state_hash: str = "") -> Optional[JevDecision]:
        entry = self._memory_cache.get(key)
        if not entry:
            self._stats["misses"] += 1
            return None

        # Check TTL
        expires_at = entry.get("expires_at")
        if expires_at and time.time() > expires_at:
            del self._memory_cache[key]
            self._stats["misses"] += 1
            return None

        # Check state hash match if provided
        cached_state = entry.get("state_hash")
        if state_hash and cached_state and cached_state != state_hash:
            del self._memory_cache[key]
            self._stats["misses"] += 1
            return None

        self._stats["hits"] += 1
        data = entry.get("decision", {})
        decision = JevDecision.from_dict(data)
        decision.source = "cache"
        return decision

    def set(
        self,
        key: str,
        decision: JevDecision,
        state_hash: str = "",
        ttl_seconds: Optional[int] = None,
        persist: bool = True,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        self._memory_cache[key] = {
            "key": key,
            "decision": decision.to_dict(),
            "state_hash": state_hash,
            "created_at": now,
            "expires_at": now + ttl if ttl > 0 else None,
        }
        self._stats["sets"] += 1

        if persist:
            self._save_to_disk()

    def clear(self) -> None:
        self._memory_cache.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass

    def invalidate_state(self, current_state_hash: str) -> int:
        to_delete = []
        for k, v in self._memory_cache.items():
            st = v.get("state_hash")
            if st and st != current_state_hash:
                to_delete.append(k)
        for k in to_delete:
            del self._memory_cache[k]
        if to_delete:
            self._save_to_disk()
        return len(to_delete)

    def _load_from_disk(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    now = time.time()
                    self._memory_cache = {
                        k: v for k, v in data.items()
                        if not v.get("expires_at") or v["expires_at"] > now
                    }
        except Exception:
            self._memory_cache = {}

    def _save_to_disk(self) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, indent=2)
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        rate = round((self._stats["hits"] / total) * 100, 1) if total > 0 else 0.0
        return {
            "total_queries": total,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_pct": rate,
            "cached_entries": len(self._memory_cache),
        }
