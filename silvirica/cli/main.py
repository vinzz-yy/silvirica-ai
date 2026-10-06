"""
Silvirica AI Main CLI Entrypoint.
Universal AI Intelligence Enhancement Runtime with Security Hardening.
"""

from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from silvirica.benchmark.harness import BenchmarkHarness
from silvirica.benchmark.report import BenchmarkReporter
from silvirica.cache.engine import MultiTierCacheManager
from silvirica.cli.ask import execute_ask
from silvirica.cli.doctor import SilviricaDoctor
from silvirica.cli.status import show_status
from silvirica.core.config import ProjectConfig, load_config
from silvirica.core.project import ProjectBrain
from silvirica.daemon.server import run_daemon
from silvirica.graph.graph_db import GraphDatabase
from silvirica.graph.query import GraphQueryEngine
from silvirica.mcp.server import MCPServer
from silvirica.memory.vault import ObsidianMemoryVault
from silvirica.observatory.dashboard import ObservatoryDashboard
from silvirica.observatory.explain import DecisionExplainer
from silvirica.observatory.telemetry import TelemetryStore
from silvirica.repository.detector import ProjectDetector
from silvirica.repository.indexer import RepositoryIndexer
from silvirica.repository.symbols import SymbolIndex
from silvirica.security.audit_logger import SecurityAuditLogger
from silvirica.security.engine import SecurityEngine
from silvirica.skills.loader import SkillLoader
from silvirica.uiux.design_system import DesignSystemExtractor


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="silvirica",
        description="Silvirica AI: Universal AI Intelligence Enhancement Runtime",
    )
    subparsers = parser.add_subparsers(dest="command", help="Silvirica Commands")

    init_parser = subparsers.add_parser("init", help="Initialize Silvirica in current directory")
    init_parser.add_argument("--force", action="store_true", help="Force re-indexing")

    subparsers.add_parser("setup", help="Interactive environment setup wizard")
    subparsers.add_parser("doctor", help="Run comprehensive runtime diagnostics")
    subparsers.add_parser("status", help="Show project status and summary")

    ask_parser = subparsers.add_parser("ask", help="Query project intelligence with minimal tokens")
    ask_parser.add_argument("query", type=str, help="Question or task for Silvirica")

    analyze_parser = subparsers.add_parser("analyze", help="Index repository and update symbols and graph")
    analyze_parser.add_argument("--force", action="store_true", help="Force full re-index")

    skills_parser = subparsers.add_parser("skills", help="List and inspect available progressive skills")
    skills_parser.add_argument("--overlaps", action="store_true", help="Audit overlapping / duplicate skills")

    mem_parser = subparsers.add_parser("memory", help="Inspect and search Obsidian memory vault")
    mem_parser.add_argument("query", nargs="?", default="", help="Optional search term")
    mem_parser.add_argument("--summary", action="store_true", help="Show Obsidian-style category summary")

    graph_parser = subparsers.add_parser("graph", help="Query knowledge graph relationships")
    graph_parser.add_argument("query", type=str, help="Node or keyword to trace in graph")

    cache_parser = subparsers.add_parser("cache", help="Manage multi-tier L1-L7 cache")
    cache_parser.add_argument("--clear", action="store_true", help="Clear all cache tiers")
    cache_parser.add_argument("--stats", action="store_true", help="Show cache hit statistics")

    sec_parser = subparsers.add_parser("security", help="Run defensive security audit or check security status")
    sec_parser.add_argument("action", nargs="?", default="scan", choices=["scan", "status"], help="Action: scan or status (default: scan)")
    sec_parser.add_argument("--file", type=str, help="Optional specific file to scan")

    audit_parser = subparsers.add_parser("audit", help="Inspect security audit log events")
    audit_parser.add_argument("--limit", type=int, default=20, help="Number of events to display")

    subparsers.add_parser("permissions", help="Display runtime permission policies and trust tiers")
    subparsers.add_parser("uiux", help="Extract design system tokens and audit UI/UX")
    subparsers.add_parser("benchmark", help="Run before-vs-after benchmark harness")
    subparsers.add_parser("dashboard", help="Render Observatory dashboard")
    subparsers.add_parser("explain-last", help="Explain last routing and context decision")

    daemon_parser = subparsers.add_parser("daemon", help="Run local HTTP daemon service")
    daemon_parser.add_argument("--port", type=int, default=7458, help="Port to listen on (default 7458)")
    daemon_parser.add_argument("--token", type=str, help="Optional custom auth token")

    subparsers.add_parser("mcp", help="Run MCP standard I/O server for AI coding assistants")

    jev_parser = subparsers.add_parser("jev", help="JEV Fast-Thinking & Decision Engine intelligence")
    jev_sub = jev_parser.add_subparsers(dest="jev_command", help="JEV subcommands")
    jev_sub.add_parser("status", help="Show JEV capability health, circuit breaker state, and metrics")
    jev_test = jev_sub.add_parser("test", help="Test JEV decision routing on a query")
    jev_test.add_argument("query", type=str, help="Query to route and classify")
    jev_sub.add_parser("doctor", help="Run comprehensive diagnostics on JEV connectivity & latency")
    jev_sub.add_parser("benchmark", help="Run comparative benchmark: Without JEV vs With JEV")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    root = Path.cwd()

    if args.command == "init":
        print(f"Initializing Silvirica AI in {root}...")
        brain = ProjectBrain(root)
        detector = ProjectDetector(root)
        det_info = detector.detect()

        cfg = ProjectConfig(
            name=det_info["name"],
            languages=det_info["languages"],
            frameworks=det_info["frameworks"],
            package_managers=det_info["package_managers"],
        )
        brain.init(cfg)

        indexer = RepositoryIndexer(root)
        idx_res = indexer.index(force=args.force)

        print(f"Project initialized successfully without modifying application code.")
        print(f"- Languages detected: {', '.join(det_info['languages']) or 'None'}")
        print(f"- Frameworks detected: {', '.join(det_info['frameworks']) or 'None'}")
        print(f"- Files indexed: {idx_res['code_files_indexed']}")
        print(f"- Symbols indexed: {idx_res['symbols_indexed']}")
        print(f"- Graph nodes created: {idx_res['graph_nodes']}")
        print(f"- Duration: {idx_res['duration_seconds']}s")
        print("Run 'silvirica doctor' to verify system health.")

    elif args.command == "setup":
        print("================== SILVIRICA SETUP WIZARD ==================")
        detector = ProjectDetector(root)
        det = detector.detect()
        print(f"Detected Platform: Python {sys.version.split()[0]} on {sys.platform}")
        print(f"Detected Project:  {det['name']}")
        print(f"Languages:         {', '.join(det['languages']) or 'None'}")
        print(f"Frameworks:        {', '.join(det['frameworks']) or 'None'}")
        brain = ProjectBrain(root)
        brain.init()
        indexer = RepositoryIndexer(root)
        indexer.index()
        print("Setup complete! Use 'silvirica ask', 'silvirica benchmark', or 'silvirica mcp'.")
        print("============================================================")

    elif args.command == "doctor":
        doc = SilviricaDoctor(root)
        ok = doc.print_report()
        if not ok:
            sys.exit(1)

    elif args.command == "status":
        show_status(root)

    elif args.command == "ask":
        answer = execute_ask(root, args.query, show_telemetry_box=True)
        print(answer)

    elif args.command == "analyze":
        indexer = RepositoryIndexer(root)
        res = indexer.index(force=args.force)
        print("================== REPOSITORY INDEX REPORT ==================")
        for k, v in res.items():
            print(f"{k:<24}: {v}")
        print("=============================================================")

    elif args.command == "skills":
        loader = SkillLoader(root / "skills")
        if args.overlaps:
            overlaps = loader.detect_overlapping_skills()
            print(f"================ OVERLAPPING SKILLS DETECTED ({len(overlaps)}) ================")
            for ov in overlaps[:15]:
                print(f"- [{ov['skill_a']}] <-> [{ov['skill_b']}]: Shared triggers: {', '.join(ov['shared_triggers'])}")
            print("=========================================================================")
        else:
            skills = loader.list_skills()
            print(f"================ INSTALLED PROGRESSIVE SKILLS ({len(skills)}) ================")
            for s in sorted(skills, key=lambda x: x.name):
                desc = (s.description[:65] + '...') if len(s.description) > 65 else s.description
                print(f"- {s.name:<30} [{s.trust_tier.value:<9} | {s.priority.upper():<6}]: {desc}")
            print("=======================================================================")

    elif args.command == "memory":
        vault = ObsidianMemoryVault(root / ".silvirica" / "memory")
        if args.summary:
            summary = vault.get_vault_summary()
            print(f"================ OBSIDIAN MEMORY SUMMARY ({summary['total_notes']} files) ================")
            for cat, cnt in summary["categories"].items():
                print(f"  - {cat.replace('_', ' ').title():<20}: {cnt} entries")
            print("===========================================================================")
        elif args.query:
            matches = vault.search(args.query)
            print(f"Found {len(matches)} memory note(s) matching '{args.query}':")
            for m in matches:
                print(f"\n--- [{m.id}] {m.title} ---\n{m.content[:400]}...")
        else:
            notes = vault.list_notes()
            print(f"================ OBSIDIAN MEMORY VAULT ({len(notes)} notes) ================")
            for n in notes:
                rec = vault.read_note(n)
                tags_str = f" #{' #'.join(rec.tags)}" if rec and rec.tags else ""
                print(f"- [[{n}]]{tags_str}")
            print("=====================================================================")

    elif args.command == "graph":
        graph_db = GraphDatabase(root / ".silvirica" / "graph" / "graph.db")
        engine = GraphQueryEngine(graph_db)
        print(engine.query(args.query))

    elif args.command == "cache":
        cache_manager = MultiTierCacheManager(root / ".silvirica" / "cache")
        if args.clear:
            cache_manager.clear()
            print("Silvirica Multi-Tier Cache cleared successfully.")
        else:
            stats = cache_manager.get_stats()
            print("=================== SILVIRICA MULTI-TIER CACHE STATS ===================")
            print(f"Total Lookups:      {stats['total_lookups']}")
            print(f"Cache Hits:         {stats['hits']}")
            print(f"Cache Misses:       {stats['misses']}")
            print(f"Hit Rate:           {stats['hit_rate_percentage']}%")
            print(f"Active Mem Entries: {stats['memory_entries']}")
            print("Tier Hits Breakdown:")
            for tier, hits in stats["tier_hits"].items():
                print(f"  - {tier:<20}: {hits}")
            print("========================================================================")

    elif args.command == "security":
        engine = SecurityEngine(root)
        if args.action == "status":
            cfg = load_config(root)
            print("===================== SILVIRICA SECURITY STATUS =====================")
            print(f"Security Mode:           {cfg.guardrails.security_mode}")
            print(f"Secret Redaction:        {'ENABLED' if cfg.guardrails.secret_redaction_enabled else 'DISABLED'}")
            print(f"Destructive DB Block:    {'ENABLED' if cfg.guardrails.block_destructive_db else 'DISABLED'}")
            print(f"Migration Auto-Edit:     {'BLOCKED' if cfg.guardrails.block_migration_auto_edit else 'ALLOWED'}")
            print(f"Skill Sandboxing:        {'ENFORCED' if cfg.guardrails.enforce_skill_sandboxing else 'DISABLED'}")
            print(f"Audit Logging:           {'ACTIVE' if cfg.guardrails.audit_logging_enabled else 'DISABLED'}")
            print("====================================================================")
        else:
            res = engine.scan_repository(target_path=args.file)
            print("===================== SECURITY INTELLIGENCE AUDIT =====================")
            print(f"Files Scanned:   {res['files_scanned']}")
            print(f"Total Findings:  {res['total_findings']}")
            print(f"Severity Breakdown: {res['severity_counts']}")
            print("-----------------------------------------------------------------------")
            for idx, f in enumerate(res["findings"][:15], 1):
                print(f"[{f.severity.value}] {f.title} ({f.location})")
                print(f"  Risk: {f.risk_description}")
                print(f"  Fix:  {f.recommendation}\n")
            print("=======================================================================")

    elif args.command == "audit":
        audit = SecurityAuditLogger(root)
        events = audit.get_recent_events(limit=args.limit)
        print(f"================ SECURITY AUDIT LOG ({len(events)} events) ================")
        for ev in events:
            print(f"[{ev.get('timestamp')}] {ev.get('severity', 'INFO')} | {ev.get('event_type')} - {ev.get('action')} ({ev.get('status')})")
            if ev.get("details"):
                print(f"    Details: {ev.get('details')}")
        print("==========================================================================")

    elif args.command == "permissions":
        cfg = load_config(root)
        print("=================== SILVIRICA PERMISSION MATRIX ===================")
        print("Trust Tier Hierarchy:")
        print("  1. SYSTEM_POLICY      -> Immutable local runtime rules")
        print("  2. USER_REQUEST       -> Explicit interactive CLI / IDE commands")
        print("  3. TRUSTED_SKILL      -> Built-in & Verified skill instructions")
        print("  4. REPOSITORY_DATA    -> Unprivileged text data (PromptArmor fenced)")
        print("  5. EXTERNAL_CONTENT   -> Unprivileged network context (SSRF checked)")
        print("\nGuardrail Capabilities:")
        print(f"  - Database Mutations: {'Blocked' if cfg.guardrails.block_destructive_db else 'Permitted'}")
        print(f"  - Migration Edits:    {'Blocked' if cfg.guardrails.block_migration_auto_edit else 'Permitted'}")
        print(f"  - Secret Mod:         Blocked (.env, id_rsa, credentials.json)")
        print("===================================================================")

    elif args.command == "uiux":
        extractor = DesignSystemExtractor(root)
        tokens = extractor.extract_tokens()
        print("=================== UI/UX DESIGN SYSTEM INTELLIGENCE ===================")
        print(f"Tailwind Detected:   {'YES' if tokens['has_tailwind'] else 'NO'}")
        print(f"Colors Detected:     {len(tokens['colors_detected'])} ({', '.join(tokens['colors_detected'][:8])})")
        print(f"CSS Variables:       {tokens['css_variables_count']}")
        print("========================================================================")

    elif args.command == "benchmark":
        harness = BenchmarkHarness(root)
        results = harness.run_all()
        print(BenchmarkReporter.format_table(results))

    elif args.command == "dashboard":
        dash = ObservatoryDashboard(root)
        print(dash.render())

    elif args.command == "explain-last":
        telemetry = TelemetryStore(root / ".silvirica" / "metrics" / "telemetry.db")
        explainer = DecisionExplainer(telemetry)
        print(explainer.explain_last())

    elif args.command == "daemon":
        run_daemon(root, port=args.port, auth_token=args.token)

    elif args.command == "mcp":
        server = MCPServer(root)
        server.run_stdio()

    elif args.command == "jev":
        from silvirica.capabilities.jev import JEVCapability
        from silvirica.capabilities.jev.benchmark import JevBenchmarkHarness
        cfg = load_config(root)
        jev_cap = JEVCapability.get_instance(config=cfg.jev, project_config=cfg)

        if not getattr(args, "jev_command", None) or args.jev_command == "status":
            st = jev_cap.get_status()
            stats = st["stats"]
            cb = st["circuit_breaker"]
            print("==================== JEV CAPABILITY STATUS ====================")
            print(f"Status:            {st['status']}")
            print(f"Mode:              {st['mode'].title()}")
            print(f"Fallback:          Native Router")
            print(f"Decision Cache:    {'Enabled' if st['enabled'] else 'Disabled'}")
            print(f"Circuit Breaker:   {cb['state']} ({cb['consecutive_failures']} consecutive fails)")
            print(f"Total Decisions:   {stats['total_decisions']}")
            print(f"Average Decision:  {stats['average_latency_ms']} ms")
            print(f"Cache Hit Rate:    {stats['cache_hit_rate_pct']}%")
            print(f"Success Rate:      {stats['success_rate_pct']}%")
            print("===============================================================")

        elif args.jev_command == "test":
            dec = jev_cap.route(args.query)
            print("===================== JEV DECISION MATRIX =====================")
            print(f"Task Query:        {args.query}")
            print(f"Complexity:        {dec.complexity.value.upper()}")
            print(f"Execution Path:    {dec.execution_path.value}")
            print(f"Route:             {dec.route}")
            print(f"Confidence:        {round(dec.confidence * 100, 1)}%")
            print(f"Model Tier:        {dec.model_tier.value.upper()} ({jev_cap.select_model(args.query)})")
            print(f"Skills Selected:   {', '.join(dec.skills)}")
            print(f"Context Budget:    {dec.context_budget} tokens")
            print(f"Deep Reasoning:    {'YES' if dec.deep_reasoning else 'NO'}")
            print(f"Decision Latency:  {round(dec.latency_ms, 2)} ms (Source: {dec.source})")
            if dec.reasons:
                print(f"Rationale:         {dec.reasons}")
            print("===============================================================")

        elif args.jev_command == "doctor":
            st = jev_cap.get_status()
            t0 = time.time()
            test_dec = jev_cap.route("verify system health")
            lat = round((time.time() - t0) * 1000.0, 2)
            print("===================== JEV DOCTOR DIAGNOSTICS =====================")
            print(f"JEV Engine:        {'ACTIVE' if st['enabled'] else 'DISABLED'}")
            print(f"Remote Endpoint:   {st['provider_endpoint']}")
            print(f"API Key Present:   {'YES' if st['api_key_configured'] else 'NO (Local System One Mode)'}")
            print(f"Circuit Breaker:   {st['circuit_breaker']['state']}")
            print(f"Probe Latency:     {lat} ms")
            print(f"Latency Budget:    {cfg.jev.timeout_ms} ms ceiling")
            print(f"Health Status:     {'HEALTHY' if lat < cfg.jev.timeout_ms else 'DEGRADED'}")
            print("==================================================================")

        elif args.jev_command == "benchmark":
            harness = JevBenchmarkHarness(runs_per_task=5)
            print("Running Empirical JEV Benchmark (Baseline vs Silvirica + JEV)...")
            res = harness.run_benchmark()
            base = res["baseline_without_jev"]
            jev_res = res["silvirica_with_jev"]
            imp = res["comparative_improvements"]
            
            print("\n========================= JEV EMPIRICAL BENCHMARK =========================")
            print(f"{'Metric':<32} | {'Silvirica Without JEV':<24} | {'Silvirica + JEV':<24}")
            print("-" * 88)
            print(f"{'Routing Latency (Avg)':<32} | {str(base['avg_routing_latency_ms']) + ' ms':<24} | {str(jev_res['avg_routing_latency_ms']) + ' ms (' + str(imp['routing_latency_reduction_pct']) + '% faster)':<24}")
            print(f"{'Cached Decision Latency':<32} | {'N/A (No cache)':<24} | {str(jev_res['avg_cached_latency_ms']) + ' ms (' + str(imp['cache_speedup_factor']) + 'x speedup)':<24}")
            print(f"{'Context Budget (Avg Tokens)':<32} | {str(int(base['avg_context_budget'])) + ' tokens':<24} | {str(int(jev_res['avg_context_budget'])) + ' tokens (-' + str(imp['context_token_savings_pct']) + '%)':<24}")
            print(f"{'Skills Injected (Avg Count)':<32} | {str(base['avg_skills_loaded']) + ' (All monolithic)':<24} | {str(jev_res['avg_skills_loaded']) + ' (Selective -' + str(imp['skill_context_reduction_pct']) + '%)':<24}")
            print(f"{'Model Selection Strategy':<32} | {base['model_selection']:<24} | {'Tiered (Fast/Standard/Deep)':<24}")
            print(f"{'Tasks Evaluated':<32} | {str(res['tasks_evaluated']) + ' tasks':<24} | {str(res['tasks_evaluated']) + ' tasks (' + str(res['total_runs']) + ' runs)':<24}")
            print("===========================================================================")


if __name__ == "__main__":
    main()
