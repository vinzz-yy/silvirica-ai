import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from silvirica.core.types import ComplexityLevel, RoutingCategory, ExecutionState

@dataclass
class SessionState:
    session_id: str
    started_at: float = field(default_factory=time.time)
    last_query: Optional[str] = None
    last_complexity: Optional[ComplexityLevel] = None
    last_category: Optional[RoutingCategory] = None
    last_model: Optional[str] = None
    last_tokens_in: int = 0
    last_tokens_out: int = 0
    last_savings_percent: float = 0.0
    last_latency: float = 0.0
    active_skills: List[str] = field(default_factory=list)
    state: ExecutionState = ExecutionState.PLANNED
    metadata: Dict[str, Any] = field(default_factory=dict)
