from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from silvirica.cache.engine import MultiTierCacheManager
from silvirica.cli.doctor import SilviricaDoctor
from silvirica.context.compiler import SmartContextCompiler
from silvirica.core.config import load_config
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
from silvirica.security.engine import SecurityEngine
from silvirica.skills.loader import SkillLoader


class MCPToolRegistry:
    """
    Implements the 14 Universal MCP Tools for AI Assistants & IDEs.
    Seamlessly integrates with multi-tier caching, deep dependency graphs,
    and progressive skills.
    """

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
        if name == "silvirica_project":
            detector = ProjectDetector(self.root_path)
            return detector.detect()

        elif name == "silvirica_search":
            query = arguments.get("query", "")
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
            name_arg = arguments.get("name", "")
            exact = arguments.get("exact", False)
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
            query = arguments.get("query", "")
            return self.graph_query.query_subgraph(query)

        elif name == "silvirica_memory":
            query = arguments.get("query", "")
            records = self.vault.search(query)
            return [{"title": r.title, "content": r.content, "tags": r.tags, "wikilinks": r.wikilinks} for r in records]

        elif name == "silvirica_recall":
            topic = arguments.get("topic", "")
            m_type = arguments.get("type", "all")
            res: Dict[str, Any] = {}
            if m_type in ["decision", "all"]:
                res["decisions"] = self.decisions.get_decisions()
            if m_type in ["failure", "all"]:
                res["failures"] = self.failures.retrieve_relevant_failures(topic)
            return res

        elif name == "silvirica_skill":
            skill_name = arguments.get("skill_name", "")
            level = arguments.get("level", 2)
            skill = self.skill_loader.load_skill(skill_name)
            if not skill:
                return {"error": f"Skill '{skill_name}' not found."}
            if level == 1:
                return {"name": skill.name, "summary": skill.summary, "tools": skill.tools}
            return {"name": skill.name, "instructions": skill.instructions, "tools": skill.tools, "knowledge": skill.knowledge}

        elif name == "silvirica_security":
            file_path = arguments.get("file_path")
            if file_path:
                try:
                    p = (self.root_path / file_path).resolve()
                    if not p.is_relative_to(self.root_path):
                        return [{"severity": "HIGH", "category": "PATH_TRAVERSAL", "message": "Access denied: file path must be within the project workspace."}]
                except Exception:
                    return [{"severity": "HIGH", "category": "INVALID_PATH", "message": "Invalid file path specified."}]

                from silvirica.security.secret_scanner import SecretScanner
                from silvirica.security.rules import scan_code_for_vulnerabilities
                findings = SecretScanner.scan_file(p, file_path)
                if p.exists() and p.is_file():
                    findings.extend(scan_code_for_vulnerabilities(p.read_text(encoding="utf-8", errors="ignore"), file_path))
                return [f.to_dict() for f in findings]
            scan_res = self.security_engine.scan_repository()
            return {
                "files_scanned": scan_res["files_scanned"],
                "total_findings": scan_res["total_findings"],
                "severity_counts": scan_res["severity_counts"],
                "findings": [f.to_dict() for f in scan_res["findings"][:15]],
            }

        elif name == "silvirica_context":
            task = arguments.get("task", "")
            complexity_str = arguments.get("complexity", "STANDARD")
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
            task = arguments.get("task", "")
            risk = arguments.get("risk", "SAFE")
            from silvirica.fastgate.classifier import TaskClassifier
            clf = TaskClassifier.classify(task)
            category = self.model_router.select_category(clf["complexity"], clf["intent"], risk)
            model = self.model_router.get_model_for_category(category)
            return {
                "category": category.value,
                "model": model,
                "complexity": clf["complexity"].name,
                "intent": clf["intent"],
                "reasoning_budget_tokens": clf["reasoning_budget"],
            }

        elif name == "silvirica_impact":
            node_id = arguments.get("node_id", "")
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
