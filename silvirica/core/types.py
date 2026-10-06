from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set
import time


class ComplexityLevel(IntEnum):
    LEVEL_0_INSTANT = 0
    LEVEL_1_SIMPLE = 1
    LEVEL_2_STANDARD = 2
    LEVEL_3_COMPLEX = 3
    LEVEL_4_DEEP = 4
    LEVEL_5_CRITICAL = 5

    @classmethod
    def from_str(cls, name: str) -> ComplexityLevel:
        cleaned = name.strip().upper()
        mapping = {
            "INSTANT": cls.LEVEL_0_INSTANT, "0": cls.LEVEL_0_INSTANT,
            "SIMPLE": cls.LEVEL_1_SIMPLE, "1": cls.LEVEL_1_SIMPLE,
            "STANDARD": cls.LEVEL_2_STANDARD, "2": cls.LEVEL_2_STANDARD,
            "COMPLEX": cls.LEVEL_3_COMPLEX, "3": cls.LEVEL_3_COMPLEX,
            "DEEP": cls.LEVEL_4_DEEP, "4": cls.LEVEL_4_DEEP,
            "CRITICAL": cls.LEVEL_5_CRITICAL, "5": cls.LEVEL_5_CRITICAL,
        }
        return mapping.get(cleaned, cls.LEVEL_2_STANDARD)


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalTier(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"


class MemoryStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    REFERENCE = "REFERENCE"
    ARCHIVED = "ARCHIVED"


class MemoryType(str, Enum):
    WORKING = "WORKING"
    SESSION = "SESSION"
    PROJECT = "PROJECT"
    SEMANTIC = "SEMANTIC"
    EPISODIC = "EPISODIC"
    DECISION = "DECISION"
    FAILURE = "FAILURE"
    GRAPH = "GRAPH"
    USER_APPROVED = "USER_APPROVED"


class RoutingCategory(str, Enum):
    INSTANT = "INSTANT"
    QUICK = "QUICK"
    STANDARD = "STANDARD"
    CODER = "CODER"
    DEEP = "DEEP"
    ARCHITECT = "ARCHITECT"
    SECURITY = "SECURITY"
    VISUAL = "VISUAL"
    RESEARCH = "RESEARCH"
    WRITING = "WRITING"
    ULTRABRAIN = "ULTRABRAIN"
    LOCAL = "LOCAL"


class ExecutionState(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    COMPLETE = "COMPLETE"


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class SkillLevel(IntEnum):
    LEVEL_0_METADATA = 0
    LEVEL_1_SUMMARY = 1
    LEVEL_2_FULL = 2


class SymbolKind(str, Enum):
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    ROUTE = "ROUTE"
    CONTROLLER = "CONTROLLER"
    SERVICE = "SERVICE"
    MODEL = "MODEL"
    COMPONENT = "COMPONENT"
    DATABASE_TABLE = "DATABASE_TABLE"
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    SCHEMA = "SCHEMA"
    IMPORT = "IMPORT"


class NodeKind(str, Enum):
    PROJECT = "Project"
    MODULE = "Module"
    FILE = "File"
    CLASS = "Class"
    FUNCTION = "Function"
    ROUTE = "Route"
    CONTROLLER = "Controller"
    SERVICE = "Service"
    MODEL = "Model"
    TABLE = "Table"
    API = "API"
    USER = "User"
    ROLE = "Role"
    PERMISSION = "Permission"
    COMPONENT = "Component"
    DEPENDENCY = "Dependency"
    BUG = "Bug"
    DECISION = "Decision"
    TEST = "Test"
    SKILL = "Skill"


class RelationKind(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    DEPENDS_ON = "DEPENDS_ON"
    READS = "READS"
    WRITES = "WRITES"
    ROUTES_TO = "ROUTES_TO"
    AUTHORIZES = "AUTHORIZES"
    BELONGS_TO = "BELONGS_TO"
    TESTED_BY = "TESTED_BY"
    USES = "USES"
    RELATED_TO = "RELATED_TO"
    AFFECTS = "AFFECTS"


@dataclass
class SymbolInfo:
    name: str
    kind: SymbolKind
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    container: Optional[str] = None
    signature: Optional[str] = None
    code_hash: str = ""
    references: List[str] = field(default_factory=list)

    @property
    def identifier(self) -> str:
        if self.container:
            return f"{self.file_path}::{self.container}::{self.name}"
        return f"{self.file_path}::{self.name}"


@dataclass
class AstRelation:
    source_identifier: str
    target_name: str
    relation: RelationKind
    file_path: str
    line_number: int = 1
    properties: Dict[str, Any] = field(default_factory=dict)



@dataclass
class RouteInfo:
    path: str
    method: str
    handler: str
    file_path: str
    line_number: int
    middleware: List[str] = field(default_factory=list)
    name: Optional[str] = None


@dataclass
class ContextItem:
    source_type: str
    identifier: str
    content: str
    relevance_score: float = 1.0
    token_count: int = 0
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryRecord:
    id: str
    title: str
    memory_type: MemoryType = MemoryType.PROJECT
    status: MemoryStatus = MemoryStatus.ACTIVE
    content: str = ""
    tags: List[str] = field(default_factory=list)
    wikilinks: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    review_date: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    source: str = "user"


@dataclass
class SecurityFinding:
    rule_id: str
    title: str
    severity: FindingSeverity
    location: str
    file_path: str
    line_number: int
    symbol: Optional[str] = None
    evidence: str = ""
    risk_description: str = ""
    recommendation: str = ""
    confidence: float = 1.0
    verification_status: str = "UNVERIFIED"
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.value,
            "location": self.location,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "symbol": self.symbol,
            "evidence": self.evidence,
            "risk_description": self.risk_description,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
        }


@dataclass
class FastGateResult:
    intent: str
    complexity: ComplexityLevel
    risk: RiskLevel
    skills_matched: List[str] = field(default_factory=list)
    likely_tools: List[str] = field(default_factory=list)
    likely_files: List[str] = field(default_factory=list)
    is_zero_model: bool = False
    zero_model_reason: Optional[str] = None
    zero_model_answer: Optional[str] = None
    zero_model_result: Optional[str] = None
    reasoning_budget_tokens: int = 500
    cache_hit: bool = False
    cached_response: Optional[str] = None
    files_retrieved_count: int = 0
    symbols_retrieved_count: int = 0
    graph_nodes_count: int = 0


@dataclass
class ModelHandoff:
    task: str
    evidence: List[str]
    relevant_code: Dict[str, str]
    failed_attempts: List[str]
    constraints: List[str]
    open_questions: List[str]
    target_category: RoutingCategory
    token_budget: int


@dataclass
class TelemetryEvent:
    query: str
    complexity: ComplexityLevel
    category: RoutingCategory
    model_used: str
    input_tokens: int
    output_tokens: int
    estimated_baseline_tokens: int
    tokens_saved: int
    latency_seconds: float
    cache_hit: bool = False
    zero_model: bool = False
    skills_activated: List[str] = field(default_factory=list)
    files_retrieved: int = 0
    symbols_retrieved: int = 0
    cost_usd: Optional[float] = None
    validation_status: str = "UNVERIFIED"


# Compatibility aliases
TelemetryEntry = TelemetryEvent
