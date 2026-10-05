from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

from silvirica.core import yaml_compat


DEFAULT_IGNORE_PATTERNS = [
    ".git", ".silvirica", ".idea", ".vscode", "__pycache__", "*.pyc",
    "node_modules", "vendor", "dist", "build", ".next", ".nuxt",
    ".turbo", "target", ".venv", "venv", "env", ".pytest_cache", ".coverage", "htmlcov"
]


@dataclass
class ProviderConfig:
    provider: str = "openai_compatible"
    api_base: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    default_model: str = "gpt-4o-mini"
    timeout_seconds: int = 30


@dataclass
class ModelRoutingConfig:
    instant_model: str = "local-deterministic"
    quick_model: str = "gpt-4o-mini"
    standard_model: str = "gpt-4o-mini"
    coder_model: str = "gpt-4o"
    deep_model: str = "o3-mini"
    architect_model: str = "o3-mini"
    security_model: str = "gpt-4o"
    visual_model: str = "gpt-4o"
    research_model: str = "gpt-4o"
    ultrabrain_model: str = "o1"
    local_model: str = "llama3"


@dataclass
class TokenBudgetConfig:
    max_context_tokens: int = 16000
    target_compression_ratio: float = 0.10
    trivial_task_max_tokens: int = 400
    simple_task_max_tokens: int = 800
    standard_task_max_tokens: int = 2500
    complex_task_max_tokens: int = 6000
    deep_task_max_tokens: int = 12000


@dataclass
class GuardrailsConfig:
    block_destructive_db: bool = True
    block_hardcoded_secrets: bool = True
    block_migration_auto_edit: bool = True
    require_approval_for_high_risk: bool = True
    secret_redaction_enabled: bool = True
    security_mode: str = "STANDARD"  # STANDARD, STRICT, DEVELOPMENT
    audit_logging_enabled: bool = True
    enforce_skill_sandboxing: bool = True


from silvirica.capabilities.jev.schemas import JevConfig


@dataclass
class ProjectConfig:
    name: str = "Unnamed Project"
    version: str = "0.1.0"
    mode: str = "AUTO"
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)
    ignore_patterns: List[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    providers: Dict[str, ProviderConfig] = field(default_factory=lambda: {"default": ProviderConfig()})
    routing: ModelRoutingConfig = field(default_factory=ModelRoutingConfig)
    token_budget: TokenBudgetConfig = field(default_factory=TokenBudgetConfig)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    jev: JevConfig = field(default_factory=JevConfig)
    active_skills: List[str] = field(default_factory=lambda: ["coding-core", "debugging", "security-audit"])
    telemetry_enabled: bool = True

    @property
    def project_name(self) -> str:
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectConfig:
        routing_data = data.get("routing", {})
        routing = ModelRoutingConfig(**{k: v for k, v in routing_data.items() if k in ModelRoutingConfig.__annotations__})
        budget_data = data.get("token_budget", {})
        budget = TokenBudgetConfig(**{k: v for k, v in budget_data.items() if k in TokenBudgetConfig.__annotations__})
        guardrails_data = data.get("guardrails", {})
        guardrails = GuardrailsConfig(**{k: v for k, v in guardrails_data.items() if k in GuardrailsConfig.__annotations__})
        jev_data = data.get("jev", {})
        jev = JevConfig.from_dict(jev_data) if isinstance(jev_data, dict) else JevConfig()
        providers_data = data.get("providers", {})
        providers = {}
        for p_name, p_val in providers_data.items():
            if isinstance(p_val, dict):
                providers[p_name] = ProviderConfig(**{k: v for k, v in p_val.items() if k in ProviderConfig.__annotations__})

        return cls(
            name=data.get("name", "Unnamed Project"),
            version=data.get("version", "0.1.0"),
            mode=data.get("mode", "AUTO"),
            languages=data.get("languages", []),
            frameworks=data.get("frameworks", []),
            package_managers=data.get("package_managers", []),
            ignore_patterns=data.get("ignore_patterns", list(DEFAULT_IGNORE_PATTERNS)),
            providers=providers or {"default": ProviderConfig()},
            routing=routing,
            token_budget=budget,
            guardrails=guardrails,
            jev=jev,
            active_skills=data.get("active_skills", ["coding-core", "debugging", "security-audit"]),
            telemetry_enabled=data.get("telemetry_enabled", True),
        )


def get_silvirica_dir(start_path: Optional[Path] = None) -> Path:
    current = (start_path or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / ".silvirica"
        if candidate.is_dir():
            return candidate
    return current / ".silvirica"


def load_config(root_path: Optional[Path] = None) -> ProjectConfig:
    root = (root_path or Path.cwd()).resolve()
    config_file = root / ".silvirica" / "config.yaml"
    if not config_file.exists():
        silvirica_dir = get_silvirica_dir(root)
        config_file = silvirica_dir / "config.yaml"
        if not config_file.exists():
            return ProjectConfig()
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            content = yaml_compat.safe_load(f) or {}
            if isinstance(content, dict):
                return ProjectConfig.from_dict(content)
            return ProjectConfig()
    except Exception:
        return ProjectConfig()


def save_config(config: ProjectConfig, root_path: Optional[Path] = None) -> Path:
    root = (root_path or Path.cwd()).resolve()
    silvirica_dir = root / ".silvirica"
    silvirica_dir.mkdir(parents=True, exist_ok=True)
    config_file = silvirica_dir / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml_compat.safe_dump(config.to_dict(), f)
    return config_file
