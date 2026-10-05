import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from silvirica.capabilities.jev import (
    CircuitState,
    JEVCapability,
    JevAdapter,
    JevCircuitBreaker,
    JevComplexity,
    JevConfig,
    JevDecision,
    JevDecisionCache,
    JevExecutionPath,
    JevModelTier,
    JevRouter,
    JevStats,
    JevTaskClassifier,
    NativeFallbackRouter,
)
from silvirica.capabilities.jev.benchmark import JevBenchmarkHarness
from silvirica.core.config import ProjectConfig
from silvirica.core.exceptions import SecurityViolationError
from silvirica.mcp.tools import MCPToolRegistry


class TestJevSchemas(unittest.TestCase):
    def test_decision_serialization(self):
        decision = JevDecision(
            complexity=JevComplexity.ADVANCED,
            confidence=0.98,
            route="security",
            skills=["security-and-hardening"],
            context_budget=12000,
            model_tier=JevModelTier.REASONING,
            deep_reasoning=True,
            execution_path=JevExecutionPath.DEEP_PATH,
            latency_ms=1.5,
            source="jev",
        )
        d = decision.to_dict()
        self.assertEqual(d["complexity"], "advanced")
        self.assertEqual(d["model_tier"], "reasoning")
        self.assertEqual(d["execution_path"], "DEEP_PATH")
        self.assertEqual(d["skills"], ["security-and-hardening"])
        self.assertEqual(d["context_budget"], 12000)
        self.assertTrue(d["deep_reasoning"])

        reconstructed = JevDecision.from_dict(d)
        self.assertEqual(reconstructed.complexity, JevComplexity.ADVANCED)
        self.assertEqual(reconstructed.model_tier, JevModelTier.REASONING)
        self.assertEqual(reconstructed.skills, ["security-and-hardening"])

    def test_stats_metrics(self):
        stats = JevStats()
        self.assertEqual(stats.average_latency_ms, 0.0)
        self.assertEqual(stats.cache_hit_rate, 0.0)
        self.assertEqual(stats.success_rate, 100.0)

        stats.total_decisions = 10
        stats.cache_hits = 6
        stats.native_fallbacks = 1
        stats.total_latency_ms = 50.0

        self.assertEqual(stats.average_latency_ms, 5.0)
        self.assertEqual(stats.cache_hit_rate, 60.0)
        self.assertEqual(stats.success_rate, 90.0)


class TestJevCircuitBreaker(unittest.TestCase):
    def test_normal_operation(self):
        cb = JevCircuitBreaker(max_consecutive_failures=3, cooldown_seconds=0.1)
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.allow_request())

        cb.record_success()
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_tripping_and_cooldown(self):
        cb = JevCircuitBreaker(max_consecutive_failures=3, cooldown_seconds=0.1)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.allow_request())

        cb.record_failure()  # 3rd failure -> trips
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertFalse(cb.allow_request())

        # Wait for cooldown
        time.sleep(0.15)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)
        self.assertTrue(cb.allow_request())

        # Successful probe resets to CLOSED
        cb.record_success()
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_manual_reset(self):
        cb = JevCircuitBreaker(max_consecutive_failures=2, cooldown_seconds=10.0)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        cb.reset()
        self.assertEqual(cb.state, CircuitState.CLOSED)
        self.assertTrue(cb.allow_request())


class TestJevCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = JevDecisionCache(Path(self.temp_dir), default_ttl_seconds=3600)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_and_set(self):
        key = self.cache.generate_fingerprint("fix syntax bug in parser.py", "my_proj")
        decision = JevDecision(complexity=JevComplexity.SIMPLE, route="fast", context_budget=1500)
        
        self.assertIsNone(self.cache.get(key))
        self.cache.set(key, decision, state_hash="state123")
        
        cached = self.cache.get(key, state_hash="state123")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.route, "fast")
        self.assertEqual(cached.source, "cache")

    def test_state_hash_mismatch(self):
        key = self.cache.generate_fingerprint("optimize query", "my_proj")
        decision = JevDecision(complexity=JevComplexity.MEDIUM)
        self.cache.set(key, decision, state_hash="state_old")
        
        self.assertIsNone(self.cache.get(key, state_hash="state_new"))

    def test_ttl_expiration(self):
        key = self.cache.generate_fingerprint("find symbol", "my_proj")
        decision = JevDecision(complexity=JevComplexity.SIMPLE)
        self.cache.set(key, decision, ttl_seconds=0.01)
        time.sleep(0.05)
        self.assertIsNone(self.cache.get(key))


class TestJevAdapter(unittest.TestCase):
    def setUp(self):
        self.config = JevConfig(enabled=True, timeout_ms=500)
        self.adapter = JevAdapter(config=self.config)

    def test_ssrf_validation(self):
        with self.assertRaises(SecurityViolationError):
            self.adapter.validate_api_endpoint("http://169.254.169.254/latest/meta-data")
        with self.assertRaises(SecurityViolationError):
            self.adapter.validate_api_endpoint("ftp://example.com/api")
        with self.assertRaises(SecurityViolationError):
            self.adapter.validate_api_endpoint("http://external-api.com/api")  # Non-local http blocked

        valid = self.adapter.validate_api_endpoint("https://openrouter.ai/api/v1")
        self.assertEqual(valid, "https://openrouter.ai/api/v1")

    def test_local_system_one_evaluation(self):
        # Security task -> Advanced
        sec_decision = self.adapter.eval_local_system_one("Fix critical SQL injection vulnerability in user auth")
        self.assertEqual(sec_decision.complexity, JevComplexity.ADVANCED)
        self.assertEqual(sec_decision.model_tier, JevModelTier.REASONING)
        self.assertIn("security-and-hardening", sec_decision.skills)
        self.assertTrue(sec_decision.deep_reasoning)

        # Simple symbol task -> Simple
        simple_decision = self.adapter.eval_local_system_one("where is symbol load_config defined")
        self.assertEqual(simple_decision.complexity, JevComplexity.SIMPLE)
        self.assertEqual(simple_decision.model_tier, JevModelTier.FAST)
        self.assertEqual(simple_decision.execution_path, JevExecutionPath.FAST_PATH)

        # Bug debugging task -> Medium
        debug_decision = self.adapter.eval_local_system_one("debug TypeError exception in list processing")
        self.assertEqual(debug_decision.complexity, JevComplexity.MEDIUM)
        self.assertEqual(debug_decision.model_tier, JevModelTier.STANDARD)
        self.assertIn("debugging", debug_decision.skills)

    def test_pre_redaction(self):
        # Pass raw secret in query — ensure secret is redacted and doesn't crash
        raw_query = "fix bug with api key sk-proj-1234567890abcdef1234567890abcdef"
        decision = self.adapter.decide(raw_query)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.complexity, JevComplexity.MEDIUM)


class TestJevTaskClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = JevTaskClassifier()

    def test_deterministic_fast_path(self):
        is_fast, reason = self.classifier.is_deterministic_fast_path("locate symbol PathSandbox")
        self.assertTrue(is_fast)
        self.assertIsNotNone(reason)

        is_fast_file, reason_file = self.classifier.is_deterministic_fast_path("show file silvirica/core/config.py")
        self.assertTrue(is_fast_file)

        is_not_fast, _ = self.classifier.is_deterministic_fast_path("redesign the entire cache architecture")
        self.assertFalse(is_not_fast)

    def test_classify_pipeline(self):
        dec = self.classifier.classify("find file symbols.db")
        self.assertEqual(dec.execution_path, JevExecutionPath.FAST_PATH)
        self.assertEqual(dec.context_budget, 500)


class TestNativeFallbackRouter(unittest.TestCase):
    def test_native_fallback(self):
        dec = NativeFallbackRouter.evaluate("Conduct full security audit and CVE review")
        self.assertEqual(dec.complexity, JevComplexity.ADVANCED)
        self.assertEqual(dec.model_tier, JevModelTier.REASONING)
        self.assertEqual(dec.source, "native_fallback")
        self.assertIn("security-and-hardening", dec.skills)


class TestJevRouterAndCapability(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = JevConfig(enabled=True, cache=True)
        self.project_config = ProjectConfig(name="TestProj")
        self.router = JevRouter(
            config=self.config,
            project_config=self.project_config,
            cache_dir=Path(self.temp_dir),
        )
        self.capability = JEVCapability(config=self.config, project_config=self.project_config)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_router_pipeline_and_caching(self):
        task = "debug index out of bounds exception in parser"
        # 1. First run: evaluated
        d1 = self.router.evaluate_task(task)
        self.assertEqual(d1.complexity, JevComplexity.MEDIUM)
        self.assertEqual(self.router.stats.jev_calls, 1)

        # 2. Second run: served from cache (< 1ms)
        d2 = self.router.evaluate_task(task)
        self.assertEqual(d2.source, "cache")
        self.assertEqual(self.router.stats.cache_hits, 1)

    def test_model_and_skill_selection(self):
        task = "Fix XSS and CSRF vulnerabilities in form renderer"
        skills = self.capability.select_skills(task)
        self.assertIn("security-and-hardening", skills)

        model = self.capability.select_model(task)
        self.assertIsNotNone(model)

        budget = self.capability.context_budget(task)
        self.assertGreaterEqual(budget, 10000)

    def test_disabled_jev_fallback(self):
        disabled_config = JevConfig(enabled=False)
        router = JevRouter(config=disabled_config, cache_dir=Path(self.temp_dir))
        decision = router.evaluate_task("simple explain query")
        self.assertEqual(decision.source, "native_fallback")
        self.assertEqual(router.stats.native_fallbacks, 1)

    def test_status_diagnostics(self):
        status = self.capability.get_status()
        self.assertEqual(status["status"], "Connected")
        self.assertTrue(status["enabled"])
        self.assertIn("circuit_breaker", status)
        self.assertIn("cache", status)


class TestJevBenchmark(unittest.TestCase):
    def test_benchmark_execution(self):
        harness = JevBenchmarkHarness(runs_per_task=2)
        report = harness.run_benchmark()
        self.assertIn("baseline_without_jev", report)
        self.assertIn("silvirica_with_jev", report)
        self.assertIn("comparative_improvements", report)
        
        improvements = report["comparative_improvements"]
        self.assertGreater(improvements["context_token_savings_pct"], 0)
        self.assertGreater(improvements["skill_context_reduction_pct"], 0)


class TestJevMCPIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root_path = Path(self.temp_dir)
        (self.root_path / ".silvirica").mkdir(parents=True, exist_ok=True)
        self.registry = MCPToolRegistry(self.root_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mcp_route_tool_with_jev(self):
        res = self.registry.call_tool("silvirica_route", {"task": "fix critical authentication bypass vulnerability"})
        self.assertIn("category", res)
        self.assertIn("complexity", res)
        self.assertIn("model", res)
        self.assertIn("skills_recommended", res)
        self.assertIn("context_budget_tokens", res)
        self.assertEqual(res["complexity"], "ADVANCED")
        self.assertIn("security-and-hardening", res["skills_recommended"])


if __name__ == "__main__":
    unittest.main()
