from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from silvirica.cache.engine import MultiTierCacheManager
from silvirica.cli.doctor import SilviricaDoctor
from silvirica.context.compiler import SmartContextCompiler
from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.core.config import load_config
from silvirica.core.exceptions import SecurityViolationError
from silvirica.core.project import ProjectBrain
from silvirica.core.types import ComplexityLevel
from silvirica.graph.graph_db import GraphDatabase
from silvirica.graph.impact import ImpactAnalyzer
from silvirica.graph.query import GraphQueryEngine
from silvirica.memory.decision_memory import DecisionMemoryManager
from silvirica.memory.failure_memory import FailureMemoryManager
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.models.router import ModelRouter
from silvirica.observatory.telemetry import TelemetryStore
from silvirica.repository.detector import ProjectDetector
from silvirica.repository.git_watcher import GitWatcher
from silvirica.repository.symbols import SymbolIndex
from silvirica.security.audit_logger import SecurityAuditLogger
from silvirica.security.engine import SecurityEngine
from silvirica.security.sandbox import PathSandbox
from silvirica.skills.loader import SkillLoader


class MCPToolRegistry:
    """
    Implements the 14 Universal MCP Tools for AI Assistants & IDEs with
    Strict Input Validation, Path Sandboxing, Output Secret Redaction, and Audit Logging.
    """

    # Tool Risk Classification (Requirement #6)
    TOOL_RISK_RATINGS = {
        "silvirica_project": "LOW",
        "silvirica_search": "LOW",
        "silvirica_symbol": "LOW",
        "silvirica_graph": "LOW",
        "silvirica_memory": "LOW",
        "silvirica_recall": "LOW",
        "silvirica_skill": "LOW",
        "silvirica_security": "MEDIUM",
        "silvirica_context": "LOW",
        "silvirica_route": "LOW",
        "silvirica_impact": "LOW",
        "silvirica_git": "MEDIUM",
        "silvirica_stats": "LOW",
        "silvirica_health": "LOW",
    }

    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
        self.brain = ProjectBrain(self.root_path)
        self.config = load_config(self.root_path)
        self.cache = MultiTierCacheManager(self.brain.cache_dir)
        self.symbol_index = SymbolIndex(self.brain.symbols_dir / "symbols.db")
        self.graph_db = GraphDatabase(self.brain.graph_dir / "graph.db")
        self.graph_query = GraphQueryEngine(self.graph_db)
        self.vault = ObsidianMemoryVault(self.brain.memory_dir)
        self.decisions = DecisionMemoryManager(self.vault)
        self.failures = FailureMemoryManager(self.vault)
        self.skill_loader = SkillLoader(self.brain.skills_dir)
        self.security_engine = SecurityEngine(self.root_path, self.config)
        self.impact_analyzer = ImpactAnalyzer(self.graph_db)
        self.telemetry = TelemetryStore(self.brain.metrics_dir / "telemetry.db")
        self.model_router = ModelRouter(self.config, cache_manager=self.cache)
        self.audit_logger = SecurityAuditLogger(self.root_path)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "silvirica_project",
                "description": "Get project tech stack, frameworks, language detection, and active configuration.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "silvirica_search",
                "description": "Perform hybrid structural and lexical search across the indexed repository.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search term or symbol name"}},
                    "required": ["query"],
                },
            },
            {
                "name": "silvirica_symbol",
                "description": "Retrieve precise symbol definition, line range, and parameters without reading whole files.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Symbol name (e.g. AuthController, login, handle)"},
                        "exact": {"type": "boolean", "default": False},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "silvirica_graph",
                "description": "Query knowledge graph relationships and dependency pathways for a component or route.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Node or topic to trace in graph"}},
                    "required": ["query"],
                },
            },
            {
                "name": "silvirica_memory",
                "description": "Query Obsidian-style Markdown memory vault, wikilinks, and project conventions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Keyword or wikilink to look up"}},
                    "required": ["query"],
                },
            },
            {
                "name": "silvirica_recall",
                "description": "Recall past architectural decisions (ADRs) or known failure memories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic or symptom (e.g. login loop, jwt timeout)"},
                        "type": {"type": "string", "enum": ["decision", "failure", "all"], "default": "all"},
                    },
                    "required": ["topic"],
                },
            },
            {
                "name": "silvirica_skill",
                "description": "Load specialized progressive skill guidelines (Level 1 summary or Level 2 full text).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string", "description": "Skill name (e.g. security-audit, ui-ux-pro, debugging)"},
                        "level": {"type": "integer", "enum": [1, 2], "default": 2},
                    },
                    "required": ["skill_name"],
                },
            },
            {
                "name": "silvirica_security",
                "description": "Run defensive security scanner for secrets, SQLi, XSS, CSRF, and auth issues.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"file_path": {"type": "string", "description": "Optional specific file to scan"}},
                },
            },
            {
                "name": "silvirica_context",
                "description": "Compile minimal, highly-ranked, deduplicated, and redacted context prompt for a task.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task description"},
                        "complexity": {"type": "string", "enum": ["INSTANT", "SIMPLE", "STANDARD", "COMPLEX", "DEEP", "CRITICAL"], "default": "STANDARD"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "silvirica_route",
                "description": "Determine the optimal model tier (QUICK, CODER, DEEP, etc.) and token budget.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task description"},
                        "risk": {"type": "string", "enum": ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"], "default": "SAFE"},
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "silvirica_impact",
                "description": "Analyze multi-hop impact of changing a symbol or file across callers and dependents.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"node_id": {"type": "string", "description": "Node ID (e.g. file:app/Http/Controllers/AuthController.php)"}},
                    "required": ["node_id"],
                },
            },
            {
                "name": "silvirica_git",
                "description": "Inspect uncommitted git changes and identify affected files.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "silvirica_stats",
                "description": "Get current Observatory telemetry, token savings percentage, and performance metrics.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "silvirica_health",
                "description": "Run Silvirica Doctor runtime diagnostics and return health matrix.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        # Validate arguments dictionary
        if not isinstance(arguments, dict):
            arguments = {}

        self.audit_logger.log_event(
            event_type=SecurityAuditLogger.EVENT_MCP_REQUEST,
            action=name,
            status="START",
            details={"arguments": arguments, "risk_rating": self.TOOL_RISK_RATINGS.get(name, "MEDIUM")},
        )

        try:
            result = self._execute_tool_internal(name, arguments)
            sanitized_result = self._sanitize_tool_output(result)
            return sanitized_result
        except Exception as e:
            self.audit_logger.log_event(
                event_type=SecurityAuditLogger.EVENT_MCP_REQUEST,
                action=name,
                status="ERROR",
                severity="HIGH" if isinstance(e, SecurityViolationError) else "WARN",
                details={"error": str(e)},
            )
            raise

    def _execute_tool_internal(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name == "silvirica_project":
            detector = ProjectDetector(self.root_path)
            return detector.detect()

        elif name == "silvirica_search":
            query = str(arguments.get("query", ""))[:500]
            symbols = self.symbol_index.find_by_name(query, exact=False)[:10]
            memories = self.vault.search(query)[:5]
            return {
                "symbols": [
                    {"name": s.name, "kind": s.kind.value, "file": s.file_path, "lines": f"{s.start_line}-{s.end_line}", "sig": s.signature}
                    for s in symbols
                ],
                "memories": [{"title": m.title, "tags": m.tags} for m in memories],
            }

        elif name == "silvirica_symbol":
            name_arg = str(arguments.get("name", ""))[:200]
            exact = bool(arguments.get("exact", False))
            symbols = self.symbol_index.find_by_name(name_arg, exact=exact)
            return [
                {
                    "name": s.name,
                    "kind": s.kind.value,
                    "file_path": s.file_path,
                    "start_line": s.start_line,
                    "end_line": s.end_line,
                    "container": s.container,
                    "signature": s.signature,
                    "docstring": s.docstring,
                    "parameters": s.parameters,
                }
                for s in symbols
            ]

        elif name == "silvirica_graph":
            query = str(arguments.get("query", ""))[:200]
            return self.graph_query.query_subgraph(query)

        elif name == "silvirica_memory":
            query = str(arguments.get("query", ""))[:500]
            records = self.vault.search(query)
            return [{"title": r.title, "content": r.content, "tags": r.tags, "wikilinks": r.wikilinks} for r in records]

        elif name == "silvirica_recall":
            topic = str(arguments.get("topic", ""))[:500]
            m_type = str(arguments.get("type", "all")).lower()
            res: Dict[str, Any] = {}
            if m_type in ["decision", "all"]:
                res["decisions"] = self.decisions.get_decisions()
            if m_type in ["failure", "all"]:
                res["failures"] = self.failures.retrieve_relevant_failures(topic)
            return res

        elif name == "silvirica_skill":
            skill_name = str(arguments.get("skill_name", ""))[:100]
            level = int(arguments.get("level", 2))
            skill = self.skill_loader.load_skill(skill_name)
            if not skill:
                return {"error": f"Skill '{skill_name}' not found."}
            if level == 1:
                return {"name": skill.name, "summary": skill.summary, "tools": skill.tools, "trust_tier": skill.trust_tier.value}
            return {
                "name": skill.name,
                "instructions": skill.instructions,
                "tools": skill.tools,
                "knowledge": skill.knowledge,
                "trust_tier": skill.trust_tier.value,
                "capabilities": skill.capabilities.to_dict(),
            }

        elif name == "silvirica_security":
            file_path = arguments.get("file_path")
            if file_path:
                try:
                    p = PathSandbox.resolve_safe_path(str(file_path), self.root_path)
                except SecurityViolationError as sve:
                    self.audit_logger.log_event(
                        event_type=SecurityAuditLogger.EVENT_PATH_BLOCKED,
                        action="silvirica_security",
                        severity="HIGH",
                        details={"path": str(file_path), "reason": str(sve)},
                    )
                    return [{"severity": "HIGH", "category": "PATH_TRAVERSAL", "message": "Access denied: file path must be within the project workspace."}]
                except Exception:
                    return [{"severity": "HIGH", "category": "INVALID_PATH", "message": "Invalid file path specified."}]

                from silvirica.security.secret_scanner import SecretScanner
                from silvirica.security.rules import scan_code_for_vulnerabilities
                findings = SecretScanner.scan_file(p, str(file_path))
                if p.exists() and p.is_file() and not PathSandbox.is_binary_file(p) and PathSandbox.check_file_size_limit(p):
                    findings.extend(scan_code_for_vulnerabilities(p.read_text(encoding="utf-8", errors="ignore"), str(file_path)))
                return [f.to_dict() for f in findings]
            scan_res = self.security_engine.scan_repository()
            return {
                "files_scanned": scan_res["files_scanned"],
                "total_findings": scan_res["total_findings"],
                "severity_counts": scan_res["severity_counts"],
                "findings": [f.to_dict() for f in scan_res["findings"][:15]],
            }

        elif name == "silvirica_context":
            task = str(arguments.get("task", ""))[:2000]
            complexity_str = str(arguments.get("complexity", "STANDARD"))
            complexity = ComplexityLevel.from_str(complexity_str)
            compiler = SmartContextCompiler(self.config, cache_manager=self.cache)
            syms = [f"[{s.file_path}:{s.start_line}] {s.name}" for s in self.symbol_index.find_by_name(task)[:5]]
            bundle = compiler.compile(task=task, complexity=complexity, symbols=syms)
            return {
                "prompt": bundle.prompt,
                "input_tokens": bundle.input_tokens,
                "token_budget": bundle.token_budget,
                "skills_activated": bundle.skills_text,
                "reduction_percentage": bundle.reduction_percentage,
                "cache_hit": bundle.cache_hit,
            }

        elif name == "silvirica_route":
            task = str(arguments.get("task", ""))[:2000]
            risk = str(arguments.get("risk", "SAFE"))
            from silvirica.capabilities.jev import JEVCapability
            jev_cap = JEVCapability.get_instance(config=self.config.jev, project_config=self.config)
            jev_dec = jev_cap.route(task)
            model = jev_cap.select_model(task)
            return {
                "category": jev_dec.route,
                "complexity": jev_dec.complexity.value.upper(),
                "execution_path": jev_dec.execution_path.value,
                "model": model,
                "model_tier": jev_dec.model_tier.value,
                "skills_recommended": jev_dec.skills,
                "context_budget_tokens": jev_dec.context_budget,
                "confidence": round(jev_dec.confidence, 3),
                "deep_reasoning": jev_dec.deep_reasoning,
                "decision_source": jev_dec.source,
                "latency_ms": round(jev_dec.latency_ms, 2),
            }

        elif name == "silvirica_impact":
            node_id = str(arguments.get("node_id", ""))[:500]
            return self.impact_analyzer.analyze_impact(node_id)

        elif name == "silvirica_git":
            watcher = GitWatcher(self.root_path)
            changed = watcher.get_modified_files()
            return {"changed_files": changed, "count": len(changed)}

        elif name == "silvirica_stats":
            summary = self.telemetry.get_summary()
            summary["cache_stats"] = self.cache.get_stats()
            return summary

        elif name == "silvirica_health":
            doctor = SilviricaDoctor(self.root_path)
            return doctor.run_diagnostics()

        else:
            raise ValueError(f"Unknown tool: {name}")

    def _sanitize_tool_output(self, output: Any) -> Any:
        if isinstance(output, str):
            clean, _ = SecretRedactor.redact(output, mode=SecurityMode.BALANCED)
            return clean
        elif isinstance(output, dict):
            return {k: self._sanitize_tool_output(v) for k, v in output.items()}
        elif isinstance(output, list):
            return [self._sanitize_tool_output(item) for item in output]
        return output
