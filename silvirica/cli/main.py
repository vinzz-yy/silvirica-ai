"""
Silvirica AI Main CLI Entrypoint.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from silvirica.benchmark.harness import BenchmarkHarness
from silvirica.benchmark.report import BenchmarkReporter
from silvirica.cache.engine import MultiTierCacheManager
from silvirica.cli.ask import execute_ask
from silvirica.cli.doctor import SilviricaDoctor
from silvirica.cli.status import show_status
from silvirica.core.config import ProjectConfig
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
from silvirica.security.engine import SecurityEngine
from silvirica.skills.loader import SkillLoader
from silvirica.uiux.design_system import DesignSystemExtractor


def main() -> None:
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

    subparsers.add_parser("security", help="Run defensive security audit")
    subparsers.add_parser("uiux", help="Extract design system tokens and audit UI/UX")
    subparsers.add_parser("benchmark", help="Run before-vs-after benchmark harness")
    subparsers.add_parser("dashboard", help="Render Observatory dashboard")
    subparsers.add_parser("explain-last", help="Explain last routing and context decision")

    daemon_parser = subparsers.add_parser("daemon", help="Run local HTTP daemon service")
    daemon_parser.add_argument("--port", type=int, default=7458, help="Port to listen on (default 7458)")

    subparsers.add_parser("mcp", help="Run MCP standard I/O server for AI coding assistants")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

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
        sys.exit(0 if ok else 1)

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
                desc = (s.description[:75] + '...') if len(s.description) > 75 else s.description
                print(f"- {s.name:<32} [{s.priority.upper():<8}]: {desc}")
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
        res = engine.scan_repository()
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
        run_daemon(root, port=args.port)

    elif args.command == "mcp":
        server = MCPServer(root)
        server.run_stdio()


if __name__ == "__main__":
    main()
