# Project Conventions

## Standards & Guidelines

### Code Style
- **Python Version**: Python 3.9+ standard library compatibility.
- **Type Annotations**: Use `from __future__ import annotations` and explicit type hints across all modules.
- **Minimal Dependencies**: Rely on Python standard library (`sqlite3`, `ast`, `json`, `hashlib`, `http.server`) where possible; external dependencies restricted to `pyyaml` and `requests`.
- **Surgical Edits**: Prefer focused, minimal diffs over sweeping rewrites.

### Architecture Boundaries
- **Core Independence**: Silvirica Core must not depend on specific IDE plugins or LLM provider SDKs.
- **Adapter Pattern**: Model providers and IDE protocols (MCP, CLI, HTTP) interface through thin adapter layers.
- **Fail Gracefully**: If any optional subsystem (graph, cache, memory) is unavailable, fallback smoothly without crashing or blocking the developer.

### Testing Conventions
- **Unit Tests**: Every core engine feature (AST parser, FastGate, Cache, Context Compiler, Memory Vault, Validator) must have corresponding unit tests in `tests/`.
- **Benchmark Discipline**: Performance and token claims must be verifiable via reproducible benchmarks (`silvirica benchmark`).
