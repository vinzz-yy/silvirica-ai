# Architecture Decisions (ADR)

## Record of Decisions

### ADR-001: Multi-Tier L1–L7 Caching with State Hashing
- **Status**: Accepted
- **Context**: LLM inference and AST parsing are expensive when repeated on unchanged repositories.
- **Decision**: Implement a 7-tier cache (L1 Request, L2 Symbol, L3 AST, L4 Context, L5 Memory, L6 Skill, L7 Model Response) combining in-memory fast lookups with disk persistence. Cache keys incorporate repository state hashes to invalidate automatically on file modifications.
- **Consequences**: Deterministic sub-millisecond retrieval on cache hits; eliminates stale context.

### ADR-002: Zero-Model FastGate Execution
- **Status**: Accepted
- **Context**: Many developer queries (file lookups, symbol navigation, route searches, project metadata) do not require generative models.
- **Decision**: Route queries through a deterministic FastGate that executes local AST/graph lookups and returns results with 0 model tokens.
- **Consequences**: Saves tokens, eliminates network latency, guarantees 100% factual accuracy for codebase lookups.

### ADR-003: Obsidian-Compatible Human-Readable Memory Vault
- **Status**: Accepted
- **Context**: AI assistants often use opaque embeddings or transient context windows that developers cannot inspect or edit.
- **Decision**: Store persistent project memory in a standard Markdown vault with YAML frontmatter, tags, category files, and `[[Wikilinks]]`.
- **Consequences**: Fully transparent to developers; can be inspected and edited directly in Obsidian, VS Code, or via Silvirica CLI.

### ADR-004: AST-Driven Minimum Sufficient Context Budgeting
- **Status**: Accepted
- **Context**: Injecting full files causes token bloat and context dilution.
- **Decision**: Parse source files into AST symbols, extract relevant functions/classes, prioritize direct dependencies and Git diffs, and cap context strictly within tier budgets (200–6000 tokens).
- **Consequences**: >90% token reduction per prompt with higher LLM accuracy.

### ADR-005: Pre-Delivery Result Validation & Bounded Escalation
- **Status**: Accepted
- **Context**: Hallucinated syntax errors or destructive commands can break user projects.
- **Decision**: Pass model responses through AST syntax checkers and safety rules. If validation fails, perform bounded auto-escalation to higher model tiers.
- **Consequences**: High reliability without runaway recursive loops.
