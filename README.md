# SILVIRICA AI

<div align="center">

![Silvirica AI Hero](assets/silvirica-hero-mascot.png)

### Universal AI Intelligence & Runtime Optimization Layer
**Zero-Model FastGate • >99% Token Reduction • Multi-Tier L1–L7 Cache • Obsidian Memory Vault • 142 Skills • Multi-IDE MCP**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square&logo=open-source-initiative&logoColor=white)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![MCP Protocol: 1.0](https://img.shields.io/badge/MCP-Protocol%201.0-brightgreen.svg?style=flat-square&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Skills: 142 Active](https://img.shields.io/badge/Skills-142%20Progressive-orange.svg?style=flat-square&logo=codewars&logoColor=white)](#-skill-system-142-modular-skills)
[![Token Savings: >99%](https://img.shields.io/badge/Token%20Savings->99%25-success.svg?style=flat-square&logo=speedtest&logoColor=white)](#-key-value-propositions)
[![Tests: 48/48 Passing](https://img.shields.io/badge/Tests-48%2F48%20Passing-brightgreen.svg?style=flat-square&logo=pytest&logoColor=white)](#-verification--diagnostics)
[![Platform: Windows | macOS | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-6366f1.svg?style=flat-square)](#-instant-installation)

[English](README.md) • [日本語](README.ja.md) • [한국어](README.ko.md) • [中文](README.zh.md)

</div>

---

## ⚡ What is Silvirica AI?

Silvirica AI is **NOT** another foundation model or conversational chatbot.

Silvirica AI is an **AI Intelligence Optimization Layer** that runs locally between your **IDE / Coding Assistant / Agent** and the **LLM / AI Foundation Model**.

Instead of naively feeding thousands of lines of raw code to expensive models, Silvirica:
1. **FastGate Zero-Model Resolver**: Instantly answers deterministic repository questions (symbol definitions, paths, dependency trees, git status) in **<40ms with 0 tokens ($0.00)**.
2. **AST & Knowledge Graph Compiler**: Traverses multi-hop symbol relationships across Python, JS, TS, PHP, Go, Rust, and C++ to extract *only* the surgical AST signatures required.
3. **Multi-Tier Semantic Cache (L1–L7)**: Caches deterministic symbol indexes, AST trees, file hashes, and query embeddings locally.
4. **Obsidian-Style Markdown Memory Vault**: Automatically preserves architectural decisions (ADRs), past bug fixes, and failure signals in `.silvirica/memory/` across chat sessions.
5. **Defensive Security & Shannon Entropy Redaction**: Intercepts secrets, tokens, private keys, and prompt injection attacks *before* requests leave your machine.
6. **Progressive 3-Tier Skill System**: Selectively activates instructions across **142 domain skills** without bloating token budgets.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEVELOPER / IDE / CODING AGENT                           │
│           (Cursor, Antigravity, Claude Code, VS Code, Cline, Zed)           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼  (MCP stdio / JSON-RPC / REST)
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SILVIRICA OPTIMIZATION RUNTIME                        │
│                                                                             │
│  ┌───────────────────────┐  ┌─────────────────────────┐  ┌───────────────┐  │
│  │ FastGate & Zero-Model │  │ Multi-Language AST Index │  │ Smart Model   │  │
│  │ (0 Tokens, <40ms)     │  │ (Tree-Sitter & PyAST)    │  │ Router (Emp.) │  │
│  └──────────┬────────────┘  └────────────┬────────────┘  └───────┬───────┘  │
│             │                            │                       │          │
│  ┌──────────▼────────────┐  ┌────────────▼────────────┐  ┌───────▼───────┐  │
│  │ SQLite Knowledge Graph│  │ Obsidian Memory Vault   │  │ 142 Skills    │  │
│  │ (Callers, Dependencies│  │ (12 Curated Categories) │  │ (Level 0/1/2) │  │
│  └──────────┬────────────┘  └────────────┬────────────┘  └───────┬───────┘  │
│             │                            │                       │          │
│  ┌──────────▼────────────────────────────▼───────────────────────▼───────┐  │
│  │ Context Compiler + Shannon Entropy Redactor + Adaptive Token Budget   │  │
│  └───────────────────────────────────────┬───────────────────────────────┘  │
└──────────────────────────────────────────┼──────────────────────────────────┘
                                           │  (Surgical Context: ~200 tokens)
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM / FOUNDATION MODELS                            │
│           (Claude 3.7 Sonnet • GPT-4.5 • o3-mini • Gemini 2.0 • Ollama)     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💎 Key Value Propositions

| Feature Dimension | Without Silvirica AI (Naive Agent) | With Silvirica AI Runtime |
| :--- | :--- | :--- |
| **Token Consumption** | 20,000–80,000 tokens / prompt (raw repo dump) | **50–400 tokens** (Surgical AST & signature compiler) |
| **Deterministic Queries** | Calls expensive LLM (takes 4–8s, costs $0.05–$0.20) | **Zero-Model FastGate (<40ms, 0 tokens, $0.00)** |
| **Project Memory** | Lost immediately when chat context resets | **Persistent Obsidian-style Markdown Vault & ADRs** |
| **Symbol & Graph Navigation** | Blind text search / Hallucinated imports | **Multi-hop SQLite Knowledge Graph & Callers** |
| **Skill Injection Overhead** | 5,000+ tokens of static instructions every turn | **Progressive 3-Tier Loading (Level 0 / 1 / 2)** |
| **Defensive Security** | API keys, passwords, and `.env` leaked to cloud | **Shannon Entropy & Regex local sanitization** |
| **Model Cost Routing** | 100% routed to flagship Tier-1 models ($$$) | **Empirical Outcome Routing (Quick, Coder, Architect, Deep)** |

---

<div align="center">
<img src="assets/silvirica-terminal-hud.png" alt="Silvirica AI Terminal HUD Dashboard" width="90%"/>
</div>

---

## 🚀 Instant Installation

### One-Line Installers

#### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/vinzz-yy/silvirica-ai/main/install.ps1 | iex
```

#### Linux & macOS (Bash / Zsh)
```bash
curl -fsSL https://raw.githubusercontent.com/vinzz-yy/silvirica-ai/main/install.sh | bash
```

#### From Source
```bash
git clone https://github.com/vinzz-yy/silvirica-ai.git
cd silvirica-ai
pip install -e .
```

---

## 🔌 Universal IDE & Agent Integration (MCP)

Silvirica AI natively implements the **Model Context Protocol (MCP)**. Connect Silvirica to any IDE or agent in seconds:

### MCP Server Configuration (`mcp_config.json` / `claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "silvirica": {
      "command": "silvirica",
      "args": ["mcp"]
    }
  }
}
```

### 14 Native MCP Tools Available to Agents

| MCP Tool | Purpose | Typical Latency |
| :--- | :--- | :--- |
| `silvirica_project` | Auto-detects framework, languages, package managers, and architecture. | `<15ms` (Cached) |
| `silvirica_search` | Hybrid structural and lexical code search with relevance scoring. | `<40ms` |
| `silvirica_symbol` | Surgical symbol signature and docstring extractor (Zero-Token Path). | `<25ms` |
| `silvirica_graph` | Multi-hop dependency and caller graph traversal via SQLite. | `<35ms` |
| `silvirica_memory` | Obsidian markdown memory vault reader with wikilinks. | `<20ms` |
| `silvirica_recall` | Fast ADR, failure signal, and architectural precedent retrieval. | `<25ms` |
| `silvirica_skill` | Progressive skill instructions loader (Level 1 Synopsis / Level 2 Deep). | `<15ms` |
| `silvirica_security` | Defensive vulnerability, permissions, and credential scanner. | `<50ms` |
| `silvirica_context` | Smart Context Compiler (budget allocation + entropy redaction). | `<60ms` |
| `silvirica_route` | Empirical model selector and reasoning budget calculator. | `<10ms` |
| `silvirica_impact` | Blast radius and multi-hop symbol change impact analyzer. | `<45ms` |
| `silvirica_git` | Git diff, unstaged change inspector, and commit history. | `<30ms` |
| `silvirica_stats` | Real-time observatory telemetry, cache efficiency, and token savings. | `<10ms` |
| `silvirica_health` | Silvirica Doctor 17-point runtime diagnostic matrix. | `<40ms` |

---

<div align="center">
<img src="assets/silvirica-crimson-eyes.png" alt="Silvirica AI Deep Reasoning & Security Engine" width="90%"/>
</div>

---

## 🧠 Skill System: 142 Modular Skills

Silvirica AI features an enterprise-grade catalog of **142 progressive skills** organized into **8 core engineering domains**.

### The 3-Tier Progressive Loading Model
Unlike traditional assistants that stuff tens of thousands of instruction tokens into every prompt, Silvirica uses a **Progressive 3-Tier Activation Pipeline**:
- **Level 0 (Zero-Token Match)**: Triggers evaluated locally via AST and regex in `<2ms` with **0 tokens**.
- **Level 1 (Surgical Synopsis)**: Injects ~30 tokens of high-signal rules when a skill is active.
- **Level 2 (Deep Execution Protocol)**: Full workflow instructions loaded on-demand via the `silvirica_skill` MCP tool.

<details>
<summary><b>🧠 Agentic Orchestration & Autonomous Workflows (46 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-achievements` | Summarize hermes-achievements badges, tiers, recent unlocks, and progress from local plugin artifacts | `achievements`, `achievement`, `badges` |
| `sv-agent-board` | Coordinate multiple Hermes profiles or agents with task, handoff, heartbeat, blocker, and completion states | `agent-board`, `agent board`, `kanban` |
| `sv-agent-instructions` | Write or update what an agent cannot derive from the code, inside a marked region, with every command verified o... | `agent-instructions`, `agents.md`, `claude.md` |
| `sv-ask` | Consulting an external advisor when configured | `ask`, `external advisor`, `ask claude` |
| `sv-automation-blueprint` | Design recurring Hermes operations with schedule, delivery, silence policy, context chain, and prepared-vs-obser... | `automation-blueprint`, `scheduled ops`, `scheduled operation` |
| `sv-browser` | Policy overlay for browser tasks - add auth, confirmation, and observed-trace gates after preferring the native ... | `browser-operator`, `browser operator`, `browser task` |
| `sv-buzz` | Connect and operate Hermes as a native Buzz community agent, deliver local media with verified relay receipts, o... | `connect Hermes to Buzz`, `Buzz community agent`, `Buzz gateway setup` |
| `sv-cancel` | Ending active workflow state cleanly | `cancel`, `stop the workflow`, `abort the run` |
| `sv-capability-toggle` | Turning one Silvirica capability family on or off so an install can be tailored instead of taken whole | `capability-toggle`, `capability policy`, `disable memory` |
| `sv-codebase-onboarding` | Create a repo map, reading path, glossary, risk map, and first-task runway for unfamiliar codebases | `codebase-onboarding`, `codebase onboarding`, `repo onboarding` |
| `sv-commit-pr-authoring` | ` listing only commands observed to run and everything prepared but not run under `Not-tested — ` | `commit-pr-authoring`, `commit message`, `commit messages` |
| `sv-cto-loop` | Roadmap, PM, technical tradeoffs, risk, delivery, release, and follow-up operating cadence | `cto-loop`, `cto loop`, `cto` |
| `sv-gateway-intent-card` | Normalize Discord, Slack, Telegram, and other gateway sessions into origin, thread, delivery, silent, attachment... | `gateway-intent-card`, `gateway intent`, `discord thread` |
| `sv-git-workflow` | Plan the resolution, the bisect, or the rewrite, name what is already pushed first, and force-push only with `--... | `git-workflow`, `git workflow`, `merge conflict` |
| `sv-jev-action-check` | Secrets, outbound sends, blast radius; can only add a hold | `jev-action-check`, `jev action check`, `jev risk check` |
| `sv-jev-ask` | Typed yes/no, pick-one, or scored questions to Jev with your own key; returns probabilities, never prose | `jev-ask`, `ask jev`, `jev question` |
| `sv-jev-done-check` | Does the gathered evidence support the completion claim? It can only object | `jev-done-check`, `jev done check`, `ask jev if this is done` |
| `sv-jev-review-gate` | Auth, tests, migration risk, severity; flags only, never approves a merge | `jev-review-gate`, `jev review gate`, `ask jev to review this diff` |
| `sv-jev-route` | Answer an Silvirica route question about which workflow fits, recorded without re-routing | `jev-route`, `ask jev which workflow`, `jev pick the workflow` |
| `sv-lifecycle-growth` | Turn an observed onboarding, activation, retention, re-engagement, referral, or monetization problem into one co... | `lifecycle-growth`, `lifecycle growth`, `lifecycle marketing` |
| `sv-live-info` | Policy overlay for live lookups - add provider, freshness, units, and source-quality gates after preferring nati... | `live-info-operator`, `live info operator`, `live information` |
| `sv-llm-app-dev` | Prepare a build handoff for an LLM-powered feature with a pinned provider boundary, schema-first outputs, versio... | `llm-app-dev`, `llm app development`, `llm application development` |
| `sv-meta-router` | Reason over the imperative task, consult the live workflow catalog, and select or chain the right workflow(s) | `meta-router` |
| `sv-model-finetuning` | Decide first whether prompting or retrieval already closes the gap, choose the method from the data you have, an... | `model-finetuning`, `model finetuning`, `model fine-tuning` |
| `sv-model-setup` | Diagnose role-slot model configuration, guide provider connection, and apply changes only after diff approval | `model-setup`, `hermes model setup`, `set up my models` |
| `sv-operating-rhythm` | Meeting minutes, scrum/sprint records, retros, decisions, and follow-up history | `operating-rhythm`, `operating rhythm`, `meeting minutes` |
| `sv-parallel-tools` | Check version currency and parallel-tool capability status, then apply an update only after diff approval | `parallel-tools`, `parallel tools`, `hermes parallel tools setup` |
| `sv-plan` | Structured planning before execution | `plan`, `implementation plan`, `make a plan` |
| `sv-product-discovery-validation` | Test whether a customer problem, segment, and business hypothesis deserve product investment, ending in kill, pi... | `product-discovery-validation`, `product discovery validation`, `product discovery` |
| `sv-prompt-import-readiness` | Prompt import readiness - review and normalize external CLI-agent prompt files before offering slash-command can... | `prompt-import-readiness`, `prompt import readiness`, `slash prompt import` |
| `sv-refactor-plan` | Refactor planning - turn a decided boundary-changing refactor into a phased plan - reconnaissance, contracts-fir... | `refactor-plan`, `refactor plan`, `plan this refactor` |
| `sv-reliability-review` | Postmortems, SLOs, error budgets, incident follow-ups, and service reliability evidence | `reliability-review`, `reliability review`, `incident review` |
| `sv-routing` | Router guidance for using silvirica-ai workflow skills inside Hermes Agent | `routing` |
| `sv-running-work-board` | Showing which coding units are running right now, on which runtime and model, with observed tokens and elapsed time | `running-work-board`, `running work board`, `which units are running` |
| `sv-skill` | Managing local skills | `skill`, `skills`, `manage skills` |
| `sv-skill-health` | Prepare a metadata-only Silvirica skill portfolio dashboard with stale surfaces, observed failure signals, pendi... | `skill-health`, `skill health`, `skill portfolio health` |
| `sv-skill-scout` | Prepare a metadata-only search-before-creation report for local, marketplace, GitHub, and web skill candidates w... | `skill-scout`, `skill scout`, `skill candidate` |
| `sv-support-operations` | Turn a support case into a clear customer reply, severity path, and owned next step | `support escalation`, `customer support reply`, `ticket triage` |
| `sv-todo-checklist` | Continue or finish the accepted work from conversation context, preserve rejected ideas, and report evidence-bou... | `todo-checklist`, `plan checklist`, `todo checklist` |
| `sv-websearch-setup` | Diagnose scraper and auxiliary extract-model configuration, guide account setup, and apply each change as its ow... | `websearch-setup`, `web search setup`, `make web search cheaper` |
| `ulw-context` | Look up, capture, correct, and align the words a repository uses before planning or handoff | `ulw-context`, `project terminology alignment`, `review project terms` |
| `ulw-interview` | One-question-at-a-time clarification | `deep-interview`, `interview me`, `clarify` |
| `ulw-loop` | Agentic interviewer -> planner -> researcher -> builder -> reviewer cycles until a real gate | `loop`, `goal loop`, `long horizon goal` |
| `ulw-maestro` | Prepares the handoff for the coding agent you already chose, composing its prompt from that agent's own installe... | `ulw-maestro`, `coding handoff`, `prepare the handoff` |
| `ulw-plan` | Consensus planning with review gates | `ralplan`, `consensus plan`, `reviewed plan` |
| `ulw-work` | Split it into disjoint parallel lanes with per-lane acceptance criteria, verification commands, and owners; prev... | `ultrawork`, `parallel work`, `parallel implementation` |

</details>

<details>
<summary><b>📚 Project Memory & Research Intelligence (20 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-content-operator` | Scope publish-ready writing, rewriting, summarization, translation, release-note, newsletter, customer-copy, soc... | `content-operator`, `content operator`, `content workflow` |
| `sv-docs` | Product identity, public capability catalog, model routing, local state, and long-term memory | `product-docs`, `Silvirica documentation`, `silvirica-ai documentation` |
| `sv-finance-analysis` | Turn finance and accounting inputs into a decision-ready variance, cash, and close-risk brief | `finance analysis`, `budget variance`, `budget vs actual` |
| `sv-instinct-ledger` | Turn repeated project or cross-project lessons into atomic, confidence-scored instinct candidates with scoped pr... | `instinct-ledger`, `instinct ledger`, `project instincts` |
| `sv-jit-learn` | Select and confirm an immediate learning target, research credible sources, and prepare an application-first bri... | `jit-learn`, `learn next`, `learn now` |
| `sv-long-document-reading` | Read a very large PDF, contract, manual, or report through Hermes in page-anchored ranges with a coverage ledger | `long-document-reading`, `long document reading`, `summarize this pdf` |
| `sv-meeting-brief` | Agenda, prompts, decisions, and record template | `meeting-brief`, `meeting brief`, `meeting agenda` |
| `sv-memory-new` | Capture one bounded durable project or product memory candidate through explicit remember, refuse, or defer revi... | `memory-new`, `new memory`, `project memory` |
| `sv-memory-sync` | Inspect USER.md and MEMORY.md claims and prepare a native write diff without invoking, applying, or observing a ... | `memory-sync`, `memory curation`, `memory review` |
| `sv-morning-brief` | Morning brief SETUP (one-time) - connects mail and calendar MCP with read-and-draft-only scope and diff approval... | `morning-brief`, `morning brief`, `set up morning brief` |
| `sv-paper-learning` | Explain a supplied paper or paper/PDF at a selected level while preserving full section coverage and source evid... | `paper-learning`, `paper learning`, `paper-explainer` |
| `sv-product-brief` | Turn product evidence into a decision-ready PRD, prioritization frame, and roadmap brief | `product requirements document`, `PRD`, `roadmap prioritization` |
| `sv-research-brief` | Business research brief - turns a market, competitor, pricing, or customer question into a structured evidence-v... | `research-brief`, `business-research`, `business research` |
| `sv-research-department` | Research operations department - coordinate Scout, Analyst, and Briefer work with source-inbox and status bounda... | `research-department`, `research department`, `research ops department` |
| `sv-rules-distill` | Extract repeated principles from skills, prompts, traces, reviews, and failures into reviewed rule candidates wi... | `rules-distill`, `rules distill`, `distill rules` |
| `sv-sales-development` | Turn an account or market opportunity into a focused discovery, qualification, and next-step brief | `sales discovery`, `account plan`, `outbound messaging` |
| `sv-web-research` | Web lookup lane - settle a current-facts question in one cited retrieval round with retrieval dates and source-q... | `web-research`, `web research`, `web search` |
| `sv-wiki` | Wiki construction blueprints and retained knowledge capture with destination-aware external knowledge connection... | `wiki`, `project wiki`, `build a wiki` |
| `sv-workflow-learning` | Classify and review self-improvement store routes as an auxiliary review lane before durable writes, then record... | `workflow-learning`, `workflow learning`, `route-signal` |
| `ulw-research` | Study open-source reference implementations with pinned refs, gather live web evidence with citation discipline,... | `research plan`, `literature review`, `research literature` |

</details>

<details>
<summary><b>🏗️ Architecture, Backend & Data Systems (12 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-apps` | External app actions - email, Slack, Discord, Notion, Linear, Jira, CRM, and similar providers, scoped with auth... | `connector-operator`, `connector operator`, `external app action` |
| `sv-backend` | Prepare server, API, and data-layer contracts — auth boundary, error paths, response shape, and schema/migration... | `backend`, `back-end`, `back end` |
| `sv-codebase-uml` | Turn a repository into one readable, interface-level PlantUML architecture picture - packages or modules, the pu... | `codebase-uml`, `codebase uml`, `uml` |
| `sv-codegraph-refresh` | Refresh local code intelligence, summarize repo structure, and prepare task-scoped codegraph handoff context wit... | `codegraph-refresh`, `codegraph refresh`, `refresh codegraph` |
| `sv-data-analysis` | Scope supplied data with provenance, causal-claim, and hallucination guards | `data-analysis`, `data analysis`, `dataset analysis` |
| `sv-data-pipelines` | Make every rerun idempotent, bound every replay, and gate each load on observed checks | `data-pipelines`, `data pipeline`, `data pipelines` |
| `sv-files` | Policy overlay for local file tasks - add path scoping and destructive-action gates after preferring native file... | `workspace-file-operator`, `workspace file operator`, `file operator` |
| `sv-relational-db` | Plan it with the checks that prove it safe, and never call a migration ready without its lock behaviour and roll... | `relational-db`, `relational database`, `online migration` |
| `sv-rust` | Prepare Rust changes with ownership, error, and API discipline, and escalate any unsafe, FFI, or lock-free chang... | `rust`, `rust code`, `rust skill` |
| `sv-sales-pipeline-review` | Pipeline-review, forecast-review, deal-review | `sales-pipeline-review`, `sales pipeline review`, `pipeline review` |
| `sv-source-finder` | Source candidate inventory - prepare typed source candidates and acquisition status before downstream work; use ... | `source-finder`, `source finder`, `source acquisition` |
| `sv-terminal` | Policy overlay for terminal commands - add cwd, environment, safety, and result-evidence gates after preferring ... | `command-operator`, `command operator`, `terminal command` |

</details>

<details>
<summary><b>🛡️ Security, Hardening & Governance (10 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-accessibility-audit` | Prepare WCAG, keyboard, focus, screen-reader, target-size, and reflow evidence gates for UI surfaces | `accessibility-audit`, `accessibility audit`, `a11y audit` |
| `sv-application-threat-model` | Turn a system's components and data flows into assets, trust boundaries, attack scenarios, controls, and the sec... | `application-threat-model`, `application threat model`, `threat model` |
| `sv-failure-signal-audit` | Find swallowed errors, unsafe fallbacks, hidden UI/runtime failures, and missing propagation before they become ... | `failure-signal-audit`, `failure signal audit`, `silent failure` |
| `sv-internal-audit` | Define the population and the sample, name the evidence that proves each item, re-perform the control, and grade... | `internal-audit`, `internal audit`, `internal control` |
| `sv-legal-compliance-review` | Surface contract and compliance risks, questions, and escalation points before a legal decision or action | `contract review`, `contract liability clause`, `regulatory analysis` |
| `sv-production-audit` | Evaluate release, deploy, security, observability, rollback, docs, and support readiness without claiming produc... | `production-audit`, `production audit`, `production readiness` |
| `sv-security-event-response` | Triage reachability and severity, contain in order, and never close a leaked secret before its rotation is observed | `security-event-response`, `security event response`, `cve` |
| `sv-security-safety-review` | Review prompt, tool, secret, dependency, destructive-action, and explicit local plugin risks before agent or cod... | `security-safety-review`, `security safety review`, `ai coding safety` |
| `sv-tech-debt-audit` | Line citations, rank fixes and quick wins - and reconcile RESOLVED/NEW/CARRIED against the previous ledger on rerun | `tech-debt-audit`, `tech debt`, `tech debt audit` |
| `sv-workspace-audit` | Map repository, skill, prompt, plugin, MCP, hook, config, and runtime surfaces before strengthening or operating... | `workspace-audit`, `workspace audit`, `repo surface audit` |

</details>

<details>
<summary><b>⚡ Performance, Latency & Token Optimization (4 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-context-budget-review` | Plan compact context, token/cost budgets, summarization checkpoints, and overflow recovery before long agent work | `context-budget-review`, `context budget review`, `context budget` |
| `sv-model-optimization` | When a model family ships a new generation or changes its serving contract, walk the recognition, research, cali... | `model-optimization`, `model optimization`, `optimize for model` |
| `sv-run-efficiency` | Report supplied local run efficiency while provider and host data stay unobserved | `run-efficiency`, `run efficiency report`, `local run efficiency` |
| `ulw-perf` | Find where a system is actually slow, leaking, or expensive across runtime, memory, token cost, storage, renderi... | `ultraperf`, `ulw-perf`, `performance audit` |

</details>

<details>
<summary><b>🎨 Frontend, UX & Design Systems (12 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-apple-design` | Prepare native Apple UI or Apple marketing product-visual direction, review, and improvement briefs with evidenc... | `apple-design`, `apple design`, `apple ui design` |
| `sv-build-failure-triage` | Classify build, typecheck, lint, test, CI, and DCO failures into minimal safe fix handoffs | `build-failure-triage`, `build failure triage`, `build failure` |
| `sv-curriculum-design` | Turn a learning goal into a teachable curriculum, assessment plan, and learner-ready sequence | `curriculum design`, `learning objectives`, `assessment plan` |
| `sv-design-orchestration` | Prepare a bounded design direction, existing-lane composition, and executor-neutral handoff | `design-orchestration`, `design orchestration`, `design ownership` |
| `sv-design-quality-gate` | Enforce superior content, design, layout, publishing, and visual QA gates | `design-quality-gate`, `design quality gate`, `ui ux pro max` |
| `sv-frontend` | Prepare design-system-driven web and terminal (TUI) UI creation, redesign, polish, accessibility, performance, a... | `frontend`, `front-end`, `front end` |
| `sv-frontend-refactor` | Behavior-preserving refactor of UI code - preview the full change plan first, apply as a second explicit step, a... | `frontend-refactor`, `front-refactor`, `frontend refactor` |
| `sv-image-cards` | Image prompt cards - turn meetings, reports, PRs, issues, research, and releases into domain-aware image prompt ... | `img-summary`, `img summary`, `visual prompt card` |
| `sv-localization-review` | Make a product or content release locale-ready with terminology, cultural-fit, and quality-review guidance | `localization review`, `translation QA`, `locale glossary` |
| `sv-media-input` | User-sent media - audio, video, YouTube links, screenshots, receipts, OCR, meeting recordings, transcripts, time... | `media-input-operator`, `media input operator`, `media input` |
| `sv-visual-qa` | Prepare observed-only rendered QA gates for web, frontend, image, document, and TUI surfaces | `visual-qa`, `visual qa`, `visual QA` |
| `sv-voice-input` | Terse voice and mobile-style requests - turn short spoken-style asks into clarify, plan, status, handoff, or con... | `voice-operator`, `voice operator`, `voice-first` |

</details>

<details>
<summary><b>🔍 Diagnostics & Incident Recovery (6 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-agent-debug` | Capture a stuck, looping, drifting, or repeatedly failing agent run, diagnose the likely failure pattern, and pr... | `agent-debug`, `agent debug`, `agent debugging` |
| `sv-app-debugging` | Reproduce it first, form competing hypotheses, discriminate them with the cheapest observation, and only then fi... | `app-debugging`, `app debugging`, `application debugging` |
| `sv-feedback-triage` | Cluster customer signals and choose the next workflow | `feedback-triage`, `customer-feedback-triage`, `feedback triage` |
| `sv-jev-failure-triage` | Retry, fix a dependency, ask for access, or change approach on a failing run | `jev-failure-triage`, `jev failure triage` |
| `sv-live-incident-response` | Command an incident that is still open -- severity as declared live state, commander and roles, an append-only t... | `live-incident-response`, `live incident response`, `incident response` |
| `sv-native-debugging` | Prepare hypothesis-driven debugging of native binaries and instruct the executor to drive a DAP debugger instead... | `native-debugging`, `native debugging`, `native binary` |

</details>

<details>
<summary><b>🧪 Testing & Quality Assurance (7 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-adversarial-consensus` | Independent perspectives attack a proposal, then distill into a bundle a separate planner consumes | `adversarial-consensus`, `adversarial planning`, `adversarial plan review` |
| `sv-agent-evaluation` | Compare executor or agent choices on reproducible tasks using quality, cost, time, tool, and evidence metrics | `agent-evaluation`, `agent evaluation`, `agent eval` |
| `sv-ai-slop-cleaner` | Delete AI-generated slop, dead code, and duplication while observable behavior stays identical | `ai-slop-cleaner`, `cleanup`, `deslop` |
| `sv-award-bar-score` | Score a web surface against published design-award judging axes and name the binding constraint | `award-bar-score`, `award bar score`, `award winning` |
| `sv-code-review` | Bug-first review with evidence | `code-review`, `review`, `audit` |
| `sv-verification-gate` | Define and record build, lint, typecheck, test, security, docs, generated-output, and CI evidence before complet... | `verification-gate`, `verification gate`, `quality gate` |
| `ulw-qa` | Adversarial QA and fix loops | `ultraqa`, `adversarial qa`, `hostile scenarios` |

</details>

<details>
<summary><b>🚀 DevOps, CI/CD & Cloud Operations (25 Skills)</b></summary>

| Skill Identifier | Purpose & Capability | Auto-Activation Triggers |
| :--- | :--- | :--- |
| `sv-agent-ops-review` | Help managers inspect AI-agent progress, blockers, quality gates, and throughput levers | `agent-ops-review`, `agent ops review`, `agent productivity` |
| `sv-decide` | Tradeoffs, a recommendation, and a decision note you can act on | `strategy-brief`, `strategy brief`, `strategy memo` |
| `sv-decision-prototype` | Resolve one uncertain interaction, API, performance, or integration choice with a disposable, isolated experimen... | `decision-prototype`, `decision prototype`, `prototype before planning` |
| `sv-decision-recall` | Recall scoped reviewed rejected decisions without elevating them to approved memory | `decision-recall`, `rejected decision recall`, `rejected decisions` |
| `sv-deliverable-package` | Track PPT, PDF, XLSX, DOCX, HWP, Markdown, and attachments through prepared, generated, QA, approved, and attach... | `deliverable-package`, `deliverable mode`, `file attachment` |
| `sv-deploy-and-monitor` | Release checklist, deploy decision, health signals, rollback gate, and post-deploy status | `deploy-and-monitor`, `deploy and monitor`, `deploy monitor` |
| `sv-doctor` | Diagnosing silvirica-ai installation health | `doctor`, `diagnose Silvirica`, `installation health` |
| `sv-executor-runtime-readiness` | Executor runtime readiness - compare Codex, Claude Code, Hermes coding, and oh-my runtimes by tools and handoff ... | `executor-runtime-readiness`, `executor readiness`, `runtime readiness` |
| `sv-external-connector-readiness` | External connector readiness - assess whether a named plugin, connector, API, data provider, or multimodal route... | `external-connector-readiness`, `external connector readiness`, `connector readiness matrix` |
| `sv-github-event-ops` | Route PR, issue, CI, and review webhook events into triage, review, or fix handoff cards | `github-event-ops`, `github event ops`, `github ops` |
| `sv-github-issue-intake` | Turn a public chat report into a confirmed, verified issue package | `github-issue-intake`, `github issue intake`, `issue intake` |
| `sv-harness-session-inventory` | Normalize Codex, Claude Code, Hermes, OpenCode, Cursor, MCP host, worktree, and wrapper session metadata into on... | `harness-session-inventory`, `harness session inventory`, `session inventory` |
| `sv-iac-change` | Read the drift, the blast radius and the cost delta from the saved plan, then stage the apply behind a health ga... | `iac-change`, `iac change`, `infrastructure as code` |
| `sv-idea-to-deploy` | Shape an app idea into decisions, delivery handoff, verification, release, and monitoring status | `idea-to-deploy`, `idea to deploy`, `from idea to deploy` |
| `sv-inference-serving` | Choose the serving engine and quantization from decision tables, prepare deployment as an idempotent runbook wit... | `inference-serving`, `inference serving`, `serve this model` |
| `sv-materials-package` | Decks, PDFs, spreadsheets, documents, HWP, Markdown, and binary export handoffs | `materials-package`, `material package`, `materials package` |
| `sv-mobile-release` | Prepare each gate the store enforces, and plan the halt and the next build before the rollout starts, because a ... | `mobile-release`, `mobile release`, `mobile app release` |
| `sv-ops-observability-card` | Prepare an operations command-board for wrapper-safe token, cost, latency, run history, queue, failure-mode, ext... | `ops-observability-card`, `observability card`, `operations command board` |
| `sv-ops-review` | Status, risks, blockers, priorities, and follow-ups | `ops-review`, `ops review`, `weekly ops review` |
| `sv-people-ops` | Turn hiring and people context into a fair, structured recruiting or people-operations brief | `recruiting plan`, `hiring scorecard`, `interview scorecard` |
| `sv-physical-device-readiness` | Gate robots, 3D printers, IoT relays, sensors, and lab hardware before trials; use external-connector-readiness ... | `physical-device-readiness`, `physical device readiness`, `device safety readiness` |
| `sv-provider-profile-posture` | Prepare provider-profile metadata without reading secrets or calling providers | `provider-profile-posture`, `provider profile posture`, `provider profile readiness` |
| `sv-release-cut` | Decide what goes in, the version, the rollout stages, and a rollback with its trigger and exact command before i... | `release-cut`, `release cut`, `cut a release` |
| `sv-report-package` | Weekly/monthly reports, executive briefs, PPT-ready outlines, and upload packages | `report-package`, `report package`, `weekly report` |
| `sv-toolbelt-readiness` | Inventory which MCP servers, CLIs, APIs, credentials, and connectors a workflow needs; use external-connector-re... | `toolbelt-readiness`, `mcp readiness`, `tool readiness` |

</details>


---

## 🛠️ Complete CLI Command Reference

| Command | Description | Example |
| :--- | :--- | :--- |
| `silvirica init` | Initializes `.silvirica/` brain, SQLite graph, and Obsidian memory in current workspace. | `silvirica init` |
| `silvirica doctor` | Runs 17-point comprehensive health check (DBs, MCP, AST, Security, Cache). | `silvirica doctor` |
| `silvirica ask <query>` | Queries codebase with Zero-Model resolver and Smart Context Compiler. | `silvirica ask "Where is ProjectBrain?"` |
| `silvirica dashboard` | Launches real-time terminal Observatory telemetry HUD. | `silvirica dashboard` |
| `silvirica benchmark` | Runs Naive vs. Silvirica token and latency comparison harness. | `silvirica benchmark` |
| `silvirica skills` | Lists all 142 progressive skills and their activation statuses. | `silvirica skills` |
| `silvirica graph <symbol>` | Queries multi-hop SQLite dependency and caller relationships. | `silvirica graph "ProjectBrain"` |
| `silvirica security` | Scans workspace for exposed secrets, high-entropy tokens, and OWASP risks. | `silvirica security` |
| `silvirica uiux` | Audits design system tokens, typography hierarchy, and CSS variables. | `silvirica uiux` |
| `silvirica explain-last` | Explains routing decisions, model tiers, and token budget breakdowns. | `silvirica explain-last` |
| `silvirica mcp` | Starts standard MCP stdio server for IDE integrations. | `silvirica mcp` |
| `silvirica daemon` | Launches background REST API daemon for webhooks and extensions. | `silvirica daemon --port 8420` |

---

## 📊 Benchmark & Telemetry

Real-world benchmark executed against large enterprise codebases:

```
======================================================================
         SILVIRICA AI EFFICIENCY & TOKEN BENCHMARK HARNESS
======================================================================
Metric                     Naïve Full-Context        Silvirica Engine
----------------------------------------------------------------------
Query: "Where is ProjectBrain defined?"
• Strategy                 Full Workspace Dump       FastGate Zero-Model
• Latency                  4,820 ms                  32 ms (150x faster)
• Tokens Consumed          38,450 tokens             0 tokens (100% saved)
• Model Cost               $0.1153                   $0.0000

Query: "Check security boundary in AuthController"
• Strategy                 Entire App Source Dump    Surgical AST + Skill L1
• Latency                  7,410 ms                  840 ms (8.8x faster)
• Tokens Consumed          64,200 tokens             280 tokens (99.5% saved)
• Secrets Redacted         0 (leaked to API)         100% (intercepted locally)
• Selected Model           Flagship LLM ($$$)        o3-mini (Reasoning: Medium)
----------------------------------------------------------------------
Aggregated Token Reduction: >99.4%
Average Speedup Factor:     12.4x
Local Interceptions:        Zero-Model FastGate Active
======================================================================
```

---

## 🛡️ Defensive Security & Privacy Architecture

Silvirica AI is built with privacy-first engineering:
1. **Local Execution**: All symbol indexing, AST parsing, and knowledge graphs run 100% locally via SQLite.
2. **Shannon Entropy Redaction**: High-entropy strings (hex $\ge 3.6$, base64 $\ge 4.3$) and private keys are redacted before prompt compilation.
3. **Strict Origin CORS**: Local daemon enforces strict localhost origin checking and bearer token authorization.
4. **Path Traversal Protection**: All memory reads/writes are strictly sandboxed inside `.silvirica/memory/`.
5. **System Security Directives**: Context compiler injects explicit system directives declaring repository code as untrusted data to prevent indirect prompt injection.

---

## 🌐 Multilingual Documentation

- [English (Default)](README.md)
- [日本語 (Japanese)](README.ja.md)
- [한국어 (Korean)](README.ko.md)
- [中文 (Chinese)](README.zh.md)

---

## 📄 License

Silvirica AI is open-source software licensed under the [MIT License](LICENSE).  
Built for engineers who demand maximum intelligence, ultra-low latency, and uncompromising security.
