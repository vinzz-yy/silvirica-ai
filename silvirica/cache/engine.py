from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.security.sandbox import PathSandbox


class CacheTier(str, Enum):
    L1_REQUEST = "L1_REQUEST"
    L2_SYMBOL = "L2_SYMBOL"
    L3_AST = "L3_AST"
    L4_CONTEXT = "L4_CONTEXT"
    L5_MEMORY = "L5_MEMORY"
    L6_SKILL = "L6_SKILL"
    L7_MODEL_RESPONSE = "L7_MODEL_RESPONSE"


@dataclass
class CacheEntry:
    key: str
    tier: CacheTier
    data: Any
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    project_state_hash: str = ""
    hit_count: int = 0

    def is_expired(self) -> bool:
        if self.expires_at is not None and time.time() > self.expires_at:
            return True
        return False

    def is_valid_for_state(self, current_state_hash: str) -> bool:
        if self.is_expired():
            return False
        if self.project_state_hash and current_state_hash and self.project_state_hash != current_state_hash:
            return False
        return True


class MultiTierCacheManager:
    """
    High-performance, persistent Multi-Tier Caching System for Silvirica AI with
    Zero-Secret Leakage Pre-Redaction and Safe Serialization.
    """

    def __init__(self, cache_dir: Path, default_ttl_seconds: int = 86400):
        self.cache_dir = cache_dir.resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl_seconds
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "tier_hits": {tier.value: 0 for tier in CacheTier},
        }

    @staticmethod
    def generate_key(tier: CacheTier, *components: Union[str, int, float, dict, list]) -> str:
        hasher = hashlib.sha256()
        hasher.update(tier.value.encode("utf-8"))
        for item in components:
            if isinstance(item, (dict, list)):
                serialized = json.dumps(item, sort_keys=True)
                hasher.update(serialized.encode("utf-8"))
            else:
                hasher.update(str(item).encode("utf-8"))
        return f"{tier.value}_{hasher.hexdigest()[:24]}"

    def get(self, tier: CacheTier, key: str, current_state_hash: str = "") -> Optional[Any]:
        # 1. Check in-memory fast tier
        entry = self._memory_cache.get(key)
        if entry:
            if entry.is_valid_for_state(current_state_hash):
                entry.hit_count += 1
                self._stats["hits"] += 1
                self._stats["tier_hits"][tier.value] += 1
                return entry.data
            else:
                self._evict_memory(key)

        # 2. Check disk persistence tier
        disk_path = self._get_disk_path(tier, key)
        if disk_path and disk_path.exists():
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                entry = CacheEntry(
                    key=payload["key"],
                    tier=CacheTier(payload["tier"]),
                    data=payload["data"],
                    created_at=payload.get("created_at", time.time()),
                    expires_at=payload.get("expires_at"),
                    project_state_hash=payload.get("project_state_hash", ""),
                    hit_count=payload.get("hit_count", 0) + 1,
                )
                if entry.is_valid_for_state(current_state_hash):
                    self._memory_cache[key] = entry
                    self._stats["hits"] += 1
                    self._stats["tier_hits"][tier.value] += 1
                    return entry.data
                else:
                    self._evict_disk(disk_path)
            except Exception:
                self._evict_disk(disk_path)

        self._stats["misses"] += 1
        return None

    def set(
        self,
        tier: CacheTier,
        key: str,
        data: Any,
        project_state_hash: str = "",
        ttl_seconds: Optional[int] = None,
        persist_disk: bool = True,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        expires_at = now + ttl if ttl > 0 else None

        # Sanitize / Redact data before caching if it contains strings
        sanitized_data = self._sanitize_cache_data(data)

        entry = CacheEntry(
            key=key,
            tier=tier,
            data=sanitized_data,
            created_at=now,
            expires_at=expires_at,
            project_state_hash=project_state_hash,
        )
        self._memory_cache[key] = entry

        if persist_disk:
            try:
                disk_path = self._get_disk_path(tier, key)
                if disk_path:
                    disk_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(disk_path, "w", encoding="utf-8") as f:
                        json.dump(
                            {
                                "key": entry.key,
                                "tier": entry.tier.value,
                                "data": entry.data,
                                "created_at": entry.created_at,
                                "expires_at": entry.expires_at,
                                "project_state_hash": entry.project_state_hash,
                                "hit_count": entry.hit_count,
                            },
                            f,
                            indent=2,
                        )
            except Exception:
                pass

    def _sanitize_cache_data(self, data: Any) -> Any:
        if isinstance(data, str):
            clean, _ = SecretRedactor.redact(data, mode=SecurityMode.BALANCED)
            return clean
        elif isinstance(data, dict):
            return {k: self._sanitize_cache_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_cache_data(item) for item in data]
        return data

    def invalidate_state(self, current_state_hash: str) -> int:
        invalidated_count = 0
        to_delete_mem = []
        for key, entry in self._memory_cache.items():
            if entry.project_state_hash and entry.project_state_hash != current_state_hash:
                to_delete_mem.append(key)

        for k in to_delete_mem:
            self._evict_memory(k)
            invalidated_count += 1

        for tier_dir in self.cache_dir.iterdir():
            if tier_dir.is_dir():
                for disk_file in tier_dir.glob("*.json"):
                    try:
                        with open(disk_file, "r", encoding="utf-8") as f:
                            payload = json.load(f)
                        st = payload.get("project_state_hash")
                        if st and st != current_state_hash:
                            disk_file.unlink(missing_ok=True)
                            invalidated_count += 1
                    except Exception:
                        disk_file.unlink(missing_ok=True)

        return invalidated_count

    def clear(self, tier: Optional[CacheTier] = None) -> None:
        if tier:
            self._memory_cache = {k: v for k, v in self._memory_cache.items() if v.tier != tier}
            tier_dir = self.cache_dir / tier.value
            if tier_dir.exists():
                for f in tier_dir.glob("*.json"):
                    f.unlink(missing_ok=True)
        else:
            self._memory_cache.clear()
            for item in self.cache_dir.rglob("*.json"):
                item.unlink(missing_ok=True)

    def get_stats(self) -> Dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = round((self._stats["hits"] / total * 100), 1) if total > 0 else 0.0
        disk_entries_by_tier = {}
        total_disk_entries = 0
        for tier in CacheTier:
            tier_dir = self.cache_dir / tier.value
            count = len(list(tier_dir.glob("*.json"))) if tier_dir.exists() else 0
            disk_entries_by_tier[tier.value] = count
            total_disk_entries += count

        return {
            "total_lookups": total,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percentage": hit_rate,
            "memory_entries": len(self._memory_cache),
            "total_disk_entries": total_disk_entries,
            "disk_entries_by_tier": disk_entries_by_tier,
            "tier_hits": self._stats["tier_hits"],
        }

    def _get_disk_path(self, tier: CacheTier, key: str) -> Optional[Path]:
        try:
            return PathSandbox.resolve_safe_path(f"{tier.value}/{key}.json", self.cache_dir)
        except Exception:
            return None

    def _evict_memory(self, key: str) -> None:
        if key in self._memory_cache:
            del self._memory_cache[key]
            self._stats["evictions"] += 1

    def _evict_disk(self, disk_path: Path) -> None:
        try:
            if disk_path.exists():
                disk_path.unlink()
                self._stats["evictions"] += 1
        except Exception:
            pass
