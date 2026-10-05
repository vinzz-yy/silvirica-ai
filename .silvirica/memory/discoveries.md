# Project Discoveries

## Codebase Facts & Verified Benchmarks

### Benchmark Performance Facts
- **Token Reduction**: Achieved **99.3%** aggregate token reduction across the 8-scenario benchmark harness (2,298 tokens vs. 308,500 baseline).
- **Zero-Model Execution**: FastGate resolves file lookups, symbol locations, and route listings in `<40ms` with 0 model tokens consumed.
- **Cache Hit Latency**: L1/L4/L7 cache lookups execute in `<2ms` from in-memory tier and `<15ms` from disk.

### System Assets & Extensibility
- **Skills Catalog**: 153 modular skill configurations indexed in `skills/`.
- **MCP Tool Surface**: 14 standard MCP tools exposed for VS Code, Cursor, Cline, Claude Code, and Codex.
- **Multi-Language AST Support**: Python AST parser + regex/tree extractors for JavaScript/TypeScript, PHP, Go, Rust, Java, C#, and SQL.
