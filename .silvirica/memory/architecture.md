# Architecture

## System Overview
Silvirica AI is an **AI Intelligence Optimization Layer** that sits between Developer IDEs / Coding Agents and LLMs. Its primary mission is to minimize token consumption (achieving >99% reductions), eliminate latency via zero-model deterministic execution, and ensure security, project-awareness, and persistent memory across developer workflows.

## Target Execution Pipeline
1. **Developer Request**: Captured via CLI, MCP server (`stdio`), or HTTP daemon.
2. **Intent Detection & FastGate**: Determines if query can be answered deterministically with 0 model tokens (e.g., file lookup, symbol search, route discovery, cache hits).
3. **Project Brain & Repository Indexer**: Incremental file hashing and AST relation extraction (`CALLS`, `IMPORTS`, `ROUTES_TO`, `DEPENDS_ON`).
4. **Memory Retrieval**: Vectorless semantic + lexical retrieval across Obsidian-compatible Markdown vault (`#architecture`, `#decisions`, `#bugs`, `#security`).
5. **Knowledge Graph Traversal**: SQLite-backed graph query and impact analysis (`impact_analysis(Symbol)`).
6. **Progressive Skill Router**: Selects 0–3 relevant skills with Level 1 summary injection and lazy Level 2 expansion.
7. **Smart Context Compiler**: Hierarchical AST slicing under tight token budgets (200–2000 tokens) with Git diff prioritization.
8. **Security Filter & Redactor**: Pre-model redaction of API keys, passwords, bearer tokens, and connection strings.
9. **Multi-Tier Cache (L1–L7)**: In-memory LRU + disk persistent cache indexed by composite state hashes.
10. **Model Router & Tier Selection**: Assigns tier 0 (zero-model), tier 1 (fast/cheap), tier 2 (coding), tier 3 (deep reasoning), tier 4 (architecture).
11. **Result Validator**: Syntax parsing (Python AST, JS/JSON linting) and destructive query protection before delivering response.
12. **Automatic Escalation & Memory Update**: Bounded escalation upon invalid results, followed by memory persistence.

## Key Modules
- [[Project]]: Silvirica AI core definition.
- [[Decisions]]: Architecture Decision Records (ADRs).
- [[Conventions]]: Project coding and testing standards.
- [[Security]]: Redaction and vulnerability guardrails.
