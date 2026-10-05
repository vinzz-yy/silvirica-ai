# Failure Memory

## Known Pitfalls & Anti-Patterns to Avoid

### Pitfall 1: Injecting Full Source Files into LLM Context
- **Why it Fails**: Reading entire files exceeds model token limits, increases costs exponentially, and dilutes the model's focus on relevant logic.
- **Rule**: Always slice target classes, functions, and direct caller/callee relations using the Smart Context Compiler.

### Pitfall 2: Using LLMs to Make Deterministic Routing Decisions
- **Why it Fails**: Calling an LLM just to decide whether to run a file search or route query introduces 500–2000ms latency and consumes unnecessary tokens.
- **Rule**: Use deterministic regex, keyword, and AST pattern matching in FastGate for zero-model resolution.

### Pitfall 3: Stale Cache Returns After Code Edits
- **Why it Fails**: Returning cached responses after a source file has changed produces outdated or broken recommendations.
- **Rule**: All L1–L7 cache keys must incorporate composite project state hashes (`file_hashes.json`).
