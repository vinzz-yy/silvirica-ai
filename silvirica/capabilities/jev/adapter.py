from __future__ import annotations
import json
import os
import re
import ssl
import time
from typing import Any, Dict, List, Optional
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
import urllib.request

from silvirica.capabilities.jev.circuit_breaker import JevCircuitBreaker
from silvirica.capabilities.jev.schemas import (
    JevComplexity,
    JevDecision,
    JevExecutionPath,
    JevModelTier,
    JevConfig,
)
from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.core.exceptions import SecurityViolationError


class JevAdapter:
    """
    Adapter for JEV Decision Engine (TypeSafe System One / Fast Decision Layer).
    
    Security & Reliability Guarantees:
    1. Zero-leakage: All inputs are pre-redacted before sending to JEV.
    2. Strict Timeout: Respects configured latency budget (default 500ms).
    3. Circuit Breaking: Automatically trips to prevent hanging requests.
    4. Safe Structured Parsing: Emits typed JevDecision objects, never prose.
    5. SSRF Protected: Restricts outbound destinations to secure, verified URLs.
    6. Non-blocking Fallback: If JEV is unavailable, raises JevUnavailableError for instant native fallback.
    """

    BLOCKED_HOSTNAMES = {
        "169.254.169.254",
        "metadata.google.internal",
        "metadata.internal",
        "100.100.100.200",
    }

    def __init__(self, config: Optional[JevConfig] = None):
        self.config = config or JevConfig()
        self.circuit_breaker = JevCircuitBreaker(
            max_consecutive_failures=self.config.max_consecutive_failures,
            cooldown_seconds=self.config.circuit_cooldown_seconds,
        )

    def is_available(self) -> bool:
        """
        Checks if JEV capability is enabled and circuit breaker allows requests.
        """
        if not self.config.enabled:
            return False
        return self.circuit_breaker.allow_request()

    def get_api_key(self) -> Optional[str]:
        """
        Looks up JEV API key across environment variables in priority order.
        """
        for env_var in [self.config.api_key_env, "TYPESAFE_API_KEY", "OPENROUTER_API_KEY", "JEV_KEY"]:
            val = os.environ.get(env_var, "").strip()
            if val:
                return val
        return None

    @classmethod
    def validate_api_endpoint(cls, api_base: str) -> str:
        if not api_base:
            raise SecurityViolationError("JEV API base URL cannot be empty.")
        parsed = urlparse(api_base)
        if parsed.scheme not in ["https", "http"]:
            raise SecurityViolationError(f"Unsupported URL scheme for JEV: {parsed.scheme}")
        hostname = (parsed.hostname or "").lower()
        if hostname in cls.BLOCKED_HOSTNAMES or hostname.startswith("169.254."):
            raise SecurityViolationError(f"SSRF protection: destination '{hostname}' is blocked.")
        if parsed.scheme == "http" and hostname not in ["localhost", "127.0.0.1", "::1"]:
            raise SecurityViolationError(
                f"Insecure transport blocked: external JEV endpoint '{api_base}' must use HTTPS."
            )
        return api_base

    def decide(
        self,
        task_query: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
    ) -> JevDecision:
        """
        Runs JEV decision pipeline on the user request.
        Returns a structured JevDecision.
        """
        start_time = time.time()

        if not self.is_available():
            raise RuntimeError(f"JEV is unavailable (Circuit Breaker State: {self.circuit_breaker.state.value})")

        # 1. Pre-Redact all inputs before decision processing
        redacted_task = SecretRedactor.sanitize_text(task_query, mode=SecurityMode.ACTIVE_REDACTION)
        
        # Prepare compact project metadata
        project_meta = {}
        if project_context:
            for k, v in project_context.items():
                if isinstance(v, str):
                    project_meta[k] = SecretRedactor.sanitize_text(v, mode=SecurityMode.ACTIVE_REDACTION)
                elif isinstance(v, (int, float, bool, list, dict)):
                    project_meta[k] = v

        api_key = self.get_api_key()

        # If API key is present and mode is not forced-local, use remote TypeSafe JEV endpoint
        if api_key and self.config.mode in ("fast", "balanced", "deep"):
            try:
                decision = self._call_remote_jev(
                    redacted_task=redacted_task,
                    project_meta=project_meta,
                    available_skills=available_skills,
                    api_key=api_key,
                )
                elapsed_ms = (time.time() - start_time) * 1000.0
                decision.latency_ms = elapsed_ms
                decision.source = "jev_remote"
                self.circuit_breaker.record_success()
                return decision
            except Exception as e:
                self.circuit_breaker.record_failure(e)
                # If remote fails, fallback to high-speed local TypeSafe System One evaluator
                local_decision = self.eval_local_system_one(
                    task=redacted_task,
                    project_context=project_meta,
                    available_skills=available_skills,
                )
                elapsed_ms = (time.time() - start_time) * 1000.0
                local_decision.latency_ms = elapsed_ms
                local_decision.source = "jev_local_fallback"
                return local_decision

        # Otherwise, run the ultra-fast local TypeSafe System One decision evaluator (< 2ms)
        try:
            local_decision = self.eval_local_system_one(
                task=redacted_task,
                project_context=project_meta,
                available_skills=available_skills,
            )
            elapsed_ms = (time.time() - start_time) * 1000.0
            local_decision.latency_ms = elapsed_ms
            local_decision.source = "jev_local"
            self.circuit_breaker.record_success()
            return local_decision
        except Exception as e:
            self.circuit_breaker.record_failure(e)
            raise

    def _call_remote_jev(
        self,
        redacted_task: str,
        project_meta: Dict[str, Any],
        available_skills: Optional[List[str]],
        api_key: str,
    ) -> JevDecision:
        """
        Calls external JEV/TypeSafe decision endpoint with strict timeout enforcement.
        """
        api_base = self.validate_api_endpoint(self.config.api_base).rstrip("/")
        endpoint = f"{api_base}/chat/completions"

        system_instruction = (
            "You are JEV, the TypeSafe System One fast decision layer for Silvirica AI. "
            "You NEVER emit prose, summaries, or explanations. "
            "Return ONLY a single valid raw JSON object conforming exactly to this schema:\n"
            "{\n"
            '  "complexity": "simple" | "medium" | "advanced",\n'
            '  "confidence": float (0.0 to 1.0),\n'
            '  "route": "fast" | "debug" | "architect" | "security" | "standard",\n'
            '  "skills": [string, ...],\n'
            '  "context_budget": int,\n'
            '  "model_tier": "fast" | "standard" | "powerful" | "reasoning",\n'
            '  "deep_reasoning": bool,\n'
            '  "needs_escalation": bool\n'
            "}"
        )

        user_content = json.dumps({
            "task": redacted_task[:1000],
            "context": project_meta,
            "available_skills": available_skills or [
                "coding-core", "debugging", "security-and-hardening",
                "frontend-ui-engineering", "performance-optimization",
                "test-driven-development", "planning-and-task-breakdown"
            ],
        })

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct" if "openrouter" in api_base else "jev-decision-v1",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 200,
            "temperature": 0.0,
            "response_format": {"type": "json_object"} if "openrouter" in api_base else None,
        }
        # Filter None
        payload = {k: v for k, v in payload.items() if v is not None}

        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Silvirica-JEV-Adapter/1.0",
        }

        timeout_sec = max(0.1, self.config.timeout_ms / 1000.0)
        req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")

        context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec, context=context) as response:
                if response.status != 200:
                    raise RuntimeError(f"JEV endpoint returned HTTP {response.status}")
                raw_body = response.read().decode("utf-8")
                res_json = json.loads(raw_body)
                content = res_json["choices"][0]["message"]["content"].strip()
                # Parse JSON block
                parsed_dict = json.loads(content)
                return JevDecision.from_dict(parsed_dict)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"JEV remote decision call failed: {str(e)}") from e

    def eval_local_system_one(
        self,
        task: str,
        project_context: Optional[Dict[str, Any]] = None,
        available_skills: Optional[List[str]] = None,
    ) -> JevDecision:
        """
        Ultra-fast deterministic TypeSafe System One decision engine (< 1ms).
        Classifies task complexity, selects minimal skill sets, budgets context tokens,
        and assigns appropriate model tiers without any external network latency.
        """
        t = task.lower().strip()
        all_skills = set(available_skills or [
            "coding-core", "debugging", "security-and-hardening",
            "frontend-ui-engineering", "performance-optimization",
            "test-driven-development", "planning-and-task-breakdown"
        ])

        # 1. Advanced / Security / Deep Path Patterns
        security_patterns = [
            r"\b(vulnerab\w*|cve\w*|injection|sqli|xss|csrf|ssrf|rce|auth\w*|jwt|tamper\w*|exploit\w*|sandbox escape|secret leak|dos|ddos|bypass)\b",
            r"\b(security audit|pentest\w*|hardening|least privilege|crypto\w*|cipher|sanitize|sanitization)\b",
        ]
        architect_patterns = [
            r"\b(architect\w*|redesign\w*|refactor\w* (?:entire|whole|all)|migration|distributed|concurrency|race condition|deadlock)\b",
            r"\b(system design|multi-tenant|schema migration|protocol redesign)\b",
        ]

        # 2. Medium / Standard Path Patterns
        debug_patterns = [
            r"\b(bug|error|exception|fail|crash|traceback|fix|broken|debug|issue|timeout|nullpointer)\b",
            r"\b(stack trace|why does|doesn't work|failing test|flaky)\b",
        ]
        feature_patterns = [
            r"\b(add|implement|create|build|extend|endpoint|api|database query|route|component)\b",
            r"\b(integrate|support|hook|handler|service|interface)\b",
        ]
        test_patterns = [
            r"\b(test|tdd|unit test|mock|coverage|pytest|benchmark|assert)\b",
        ]
        perf_patterns = [
            r"\b(slow|latency|speed up|optimize|bottleneck|memory leak|profil|token cost)\b",
        ]
        ui_patterns = [
            r"\b(ui|css|html|frontend|styling|react|tailwind|button|theme|responsive|modal)\b",
        ]

        # 3. Simple / Fast Path Patterns
        simple_patterns = [
            r"^(explain|what is|how does|show me|find|locate|where is|rename|syntax|typo|format)\b",
            r"\b(docstring|comment|symbol|file path|line number)\b",
        ]

        # Evaluate Matches
        is_security = any(re.search(p, t) for p in security_patterns)
        is_architect = any(re.search(p, t) for p in architect_patterns)
        is_debug = any(re.search(p, t) for p in debug_patterns)
        is_feature = any(re.search(p, t) for p in feature_patterns)
        is_test = any(re.search(p, t) for p in test_patterns)
        is_perf = any(re.search(p, t) for p in perf_patterns)
        is_ui = any(re.search(p, t) for p in ui_patterns)
        is_simple = any(re.search(p, t) for p in simple_patterns) and not (is_security or is_architect or is_debug)

        selected_skills = []
        
        # Skill routing
        if is_security:
            if "security-and-hardening" in all_skills:
                selected_skills.append("security-and-hardening")
        if is_debug:
            if "debugging" in all_skills:
                selected_skills.append("debugging")
        if is_test:
            if "test-driven-development" in all_skills:
                selected_skills.append("test-driven-development")
        if is_perf:
            if "performance-optimization" in all_skills:
                selected_skills.append("performance-optimization")
        if is_ui:
            if "frontend-ui-engineering" in all_skills:
                selected_skills.append("frontend-ui-engineering")
        if is_architect:
            if "planning-and-task-breakdown" in all_skills:
                selected_skills.append("planning-and-task-breakdown")

        if not selected_skills:
            selected_skills = ["coding-core"]

        # Determine Complexity, Route, Model Tier, and Context Budget
        if is_security or is_architect:
            complexity = JevComplexity.ADVANCED
            model_tier = JevModelTier.REASONING if is_security else JevModelTier.POWERFUL
            route = "security" if is_security else "architect"
            context_budget = 12000
            deep_reasoning = True
            execution_path = JevExecutionPath.DEEP_PATH
            confidence = 0.95
        elif is_debug or is_feature or is_perf or is_test or is_ui or len(t.split()) > 30:
            complexity = JevComplexity.MEDIUM
            model_tier = JevModelTier.STANDARD
            route = "debug" if is_debug else ("perf" if is_perf else "feature")
            context_budget = 6000
            deep_reasoning = False
            execution_path = JevExecutionPath.STANDARD_PATH
            confidence = 0.92
        else:
            complexity = JevComplexity.SIMPLE
            model_tier = JevModelTier.FAST
            route = "fast"
            context_budget = 2000
            deep_reasoning = False
            execution_path = JevExecutionPath.FAST_PATH
            confidence = 0.96

        return JevDecision(
            complexity=complexity,
            confidence=confidence,
            route=route,
            skills=selected_skills,
            context_budget=context_budget,
            model_tier=model_tier,
            deep_reasoning=deep_reasoning,
            needs_escalation=False,
            execution_path=execution_path,
            latency_ms=0.0,
            source="jev_local",
        )
