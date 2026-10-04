# SILVIRICA AI

## Universal AI Intelligence Enhancement Runtime
### Low-Token • Fast • Multi-IDE • Multi-Agent • Memory • Graph • Skills • Security • UI/UX • Model Routing • Self-Improving Project Intelligence

Silvirica AI is **NOT** another foundation model.

Silvirica AI is an intelligent operating layer installed between:

```
USER
  │
  ▼
IDE / AI CODING ASSISTANT (Cursor, Claude Desktop, Antigravity IDE, VS Code, Roo, Cline)
  │
  ▼
SILVIRICA RUNTIME
  │
  ├── Fast Gate & Zero-Model Resolver
  ├── Project Brain & Symbol Index (SQLite)
  ├── Knowledge Graph & Dependency Pathways
  ├── Obsidian-Style Markdown Memory Vault
  ├── Progressive Skill Loader (Level 0/1/2)
  ├── Defensive Security & Secret Redaction Engine
  └── Smart Context Compiler & Token Budget Engine
  │
  ▼
AI MODEL(S) (Quick, Coder, Architect, Security, Deep, Ultrabrain)
```

---

## 🚀 Key Value Propositions

1. **⚡ Massive Token Reduction (~90–99% Savings)**:
   - Eliminates blind full-repository dumping.
   - AST & Symbol-level surgical extraction (e.g. `AuthController@login` instead of 2,400-line files).
   - Zero-Model Deterministic Path: Answers symbol, file, route, git, and stack questions locally without calling cloud LLMs.
2. **🧠 Persistent Obsidian-Style Project Memory**:
   - Human-readable Markdown vault with `[[wikilinks]]`, tags, and verified lifecycle (`CANDIDATE` → `APPROVED` → `ACTIVE` → `ARCHIVED`).
   - Dedicated Architecture Decisions (ADRs) and Failure Memory to prevent repeating past bugs.
3. **🕸️ Knowledge Graph Intelligence**:
   - SQLite-backed graph database tracking callers, dependencies, routes, tables, tests, and security findings with multi-hop impact analysis.
4. **🛡️ Defensive Security & Secret Redaction**:
   - Automated detection of hardcoded secrets, SQL injection, XSS, CSRF, command injection, and IDOR.
   - Non-negotiable automated redaction before prompts leave the local machine.
5. **🎯 Progressive Skill Loading**:
   - 3-tier loading (Level 0 Metadata → Level 1 Summary → Level 2 Full Text). Never injects hundreds of skills into prompts unnecessarily.
6. **🔌 Universal MCP Server (Model Context Protocol)**:
   - Zero-friction connection to Cursor, Claude Desktop, Antigravity IDE, VS Code extensions, Continue, Roo, and Cline via standard I/O JSON-RPC 2.0.
7. **📊 Observatory & Transparent Explainability**:
   - Real-time tracking of tokens saved, execution latency, cache efficiency, zero-model hits, and step-by-step routing explanations (`silvirica explain-last`).

---

## 📦 Installation & Quick Start

```bash
# Clone and install
git clone https://github.com/silvirica-ai/silvirica.git
cd "silvirica ai"
pip install -e .
```

### 1. Initialize in Any Project
```bash
# Initialize Silvirica Project Brain without modifying application code
silvirica init
```

### 2. Run Diagnostics
```bash
silvirica doctor
```

### 3. Ask Intelligent Queries
```bash
# Zero-Model Deterministic Lookup (0 tokens, ultra-fast)
silvirica ask "Where is ProjectBrain?"

# Complex Security Analysis (Automated context compilation + progressive skills)
silvirica ask "Determine whether tenants can access each other's financial records"
```

### 4. Inspect Decision Transparency
```bash
silvirica explain-last
```

### 5. Benchmark Performance
```bash
silvirica benchmark
```

### 6. View Observatory Dashboard
```bash
silvirica dashboard
```

---

## 🛠️ CLI Commands Reference

| Command | Description |
|---|---|
| `silvirica init` | Detect project tech stack, index symbols, and create `.silvirica/` brain. |
| `silvirica doctor` | Run 16-point comprehensive runtime health diagnostics. |
| `silvirica status` | Display indexed symbols, graph nodes, memory records, and metrics. |
| `silvirica ask "<query>"` | Compile minimal high-value context and route query. |
| `silvirica analyze` | Re-index repository code, symbols, and dependency graph. |
| `silvirica skills` | List installed progressive skills and their triggers. |
| `silvirica memory [term]` | Search and view Obsidian-style markdown memory notes. |
| `silvirica graph "<term>"` | Query dependency graph relationships and multi-hop paths. |
| `silvirica security` | Run defensive vulnerability audit and secret scanner. |
| `silvirica uiux` | Extract CSS variables, color palettes, and audit design tokens. |
| `silvirica benchmark` | Run comparative benchmark harness (Naïve vs. Silvirica Context). |
| `silvirica dashboard` | Render real-time terminal Observatory telemetry dashboard. |
| `silvirica explain-last` | Explain the routing, skill selection, and token compilation rationale. |
| `silvirica daemon [--port]` | Run local HTTP REST API daemon service. |
| `silvirica mcp` | Launch Model Context Protocol standard I/O server. |

---

## 🔌 Universal MCP Server Configuration

To connect Silvirica to your AI coding assistant (Cursor, Claude Desktop, Antigravity IDE, Roo, Cline), add the following to your MCP settings (`mcp_config.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "silvirica": {
      "command": "python",
      "args": ["-m", "silvirica.cli.main", "mcp"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Available MCP Tools:
- `silvirica_project`: Tech stack, frameworks, package managers detection.
- `silvirica_search`: Hybrid structural & lexical repository search.
- `silvirica_symbol`: Surgical symbol extraction with line ranges and signatures.
- `silvirica_graph`: Knowledge graph dependency and pathway queries.
- `silvirica_memory`: Obsidian memory vault note and wikilink retrieval.
- `silvirica_recall`: ADR decision records and known failure memory retrieval.
- `silvirica_skill`: Progressive skill guideline injection (Level 1 / Level 2).
- `silvirica_security`: Defensive vulnerability and secret scanning.
- `silvirica_context`: Smart Context Compiler generating minimal token prompts.
- `silvirica_route`: Model category selection & reasoning budget calculator.
- `silvirica_impact`: Multi-hop symbol and file change impact analyzer.
- `silvirica_git`: Uncommitted change and diff inspector.
- `silvirica_stats`: Observatory telemetry and token savings summary.
- `silvirica_health`: Silvirica Doctor diagnostic health matrix.

---

## 🧪 Testing

Silvirica AI includes a complete test suite covering unit, integration, security, AST parsing, and MCP protocols:

```bash
python -m unittest discover tests
```

---

## 📄 License

MIT License. Designed for open-source AI developer infrastructure.
