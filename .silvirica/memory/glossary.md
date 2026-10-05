# Glossary & Terminology

## Core Concept Definitions

- **FastGate**: Zero-model deterministic execution gateway that classifies developer queries and answers deterministic codebase questions without invoking external LLMs.
- **Smart Context Compiler**: Intelligent context budget allocator that extracts minimal sufficient AST symbols, callers, callees, and Git diffs instead of raw files.
- **Obsidian Memory Vault**: Human-readable, file-based project knowledge base formatted in Markdown with YAML frontmatter, tags, categories, and `[[Wikilinks]]`.
- **Knowledge Graph**: SQLite-backed graph database indexing AST relationships such as `CALLS`, `IMPORTS`, `ROUTES_TO`, `EXTENDS`, and `DEPENDS_ON`.
- **L1–L7 Cache Engine**: Multi-tier caching system spanning request cache, symbol cache, AST cache, context cache, memory cache, skill cache, and model response cache.
- **Model Router**: Tiered model dispatch engine mapping tasks from Tier 0 (deterministic/zero-model) to Tier 4 (advanced architectural reasoning).
- **Result Validator**: Post-generation syntax and safety validator ensuring code responses are syntactically sound and non-destructive.
- **Progressive Skill Loading**: Progressive disclosure pattern that loads Level 1 summaries (0–3 skills) initially, expanding to full Level 2 instructions only on demand.
