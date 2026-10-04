from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from silvirica.core.config import ProjectConfig, load_config, save_config
from silvirica.core.exceptions import ProjectNotInitializedError


class ProjectBrain:
    def __init__(self, root_path: Optional[Path] = None):
        self.root_path = (root_path or Path.cwd()).resolve()
        self.silvirica_dir = self.root_path / ".silvirica"
        self.state_dir = self.silvirica_dir / "state"
        self.index_dir = self.silvirica_dir / "index"
        self.symbols_dir = self.silvirica_dir / "symbols"
        self.graph_dir = self.silvirica_dir / "graph"
        self.cache_dir = self.silvirica_dir / "cache"
        self.metrics_dir = self.silvirica_dir / "metrics"
        self.security_dir = self.silvirica_dir / "security"
        self.knowledge_dir = self.silvirica_dir / "knowledge"
        self.memory_dir = self.silvirica_dir / "memory"
        self.skills_dir = self.silvirica_dir / "skills"
        
        self.config_path = self.silvirica_dir / "config.yaml"
        self.project_json_path = self.silvirica_dir / "project.json"

    @property
    def is_initialized(self) -> bool:
        return self.silvirica_dir.exists() and self.config_path.exists()

    def ensure_initialized(self) -> None:
        if not self.is_initialized:
            raise ProjectNotInitializedError(
                f"Project not initialized at {self.root_path}. Run 'silvirica init' first."
            )

    def init(self, config: Optional[ProjectConfig] = None) -> Dict[str, Any]:
        for directory in [
            self.silvirica_dir, self.state_dir, self.index_dir, self.symbols_dir,
            self.graph_dir, self.cache_dir, self.metrics_dir, self.security_dir,
            self.knowledge_dir, self.memory_dir, self.skills_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        cfg = config or ProjectConfig(name=self.root_path.name)
        save_config(cfg, self.root_path)

        project_info = {
            "name": cfg.name,
            "root": str(self.root_path),
            "initialized_at": time.time(),
            "silvirica_version": "0.1.0",
            "mode": cfg.mode,
            "languages": cfg.languages,
            "frameworks": cfg.frameworks,
        }
        with open(self.project_json_path, "w", encoding="utf-8") as f:
            json.dump(project_info, f, indent=2)

        self._init_memory_vault()
        return project_info

    def _init_memory_vault(self) -> None:
        default_memories = {
            "project.md": f"# Project: {self.root_path.name}\n\n## Overview\nProject context.\n\n## Technology Stack\n- Languages: \n- Frameworks: \n\n## Core Modules\n- [[Architecture]]\n- [[Conventions]]\n",
            "architecture.md": "# Architecture\n\n## System Overview\nHigh-level patterns.\n\n## Key Components\n- [[Project]]\n- [[Decisions]]\n",
            "decisions.md": "# Architecture Decisions (ADR)\n\n## Record of Decisions\nRecord key technical decisions here.\n",
            "failures.md": "# Failure Memory\n\n## Known Pitfalls & Failed Approaches\nPrevents AI assistants from repeating past mistakes.\n",
            "conventions.md": "# Project Conventions\n\n## Standards\n- Naming Conventions\n- Code Style\n- Testing Conventions\n",
            "discoveries.md": "# Project Discoveries\n\n## Findings\nVerified codebase patterns.\n",
            "glossary.md": "# Glossary & Terminology\n\n## Domain Terms\nDefinitions for domain concepts.\n",
        }
        for filename, content in default_memories.items():
            filepath = self.memory_dir / filename
            if not filepath.exists():
                filepath.write_text(content, encoding="utf-8")

    def load_project_json(self) -> Dict[str, Any]:
        if not self.project_json_path.exists():
            return {}
        try:
            with open(self.project_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_config(self) -> ProjectConfig:
        return load_config(self.root_path)
