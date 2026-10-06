from __future__ import annotations
import json
import os
import ssl
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from silvirica.context.redactor import SecretRedactor, SecurityMode
from silvirica.core.config import ProviderConfig
from silvirica.core.exceptions import SecurityViolationError


class AIProvider(ABC):
    @abstractmethod
    def generate(self, model: str, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1500) -> Dict[str, Any]:
        """
        Executes model generation and returns dict with:
        { "text": str, "input_tokens": int, "output_tokens": int, "latency_seconds": float, "model": str, "success": bool, "error": Optional[str] }
        """
        pass


class OpenAICompatibleProvider(AIProvider):
    # Prohibited SSRF destinations
    BLOCKED_HOSTNAMES = {
        "169.254.169.254",  # AWS/GCP/Azure link-local metadata
        "metadata.google.internal",
        "metadata.internal",
        "100.100.100.200",  # Alibaba Cloud metadata
    }

    def __init__(self, config: ProviderConfig):
        self.config = config

    @classmethod
    def validate_api_endpoint(cls, api_base: str) -> str:
        """
        Validates API base URL against SSRF attempts, metadata abuse, and insecure transports.
        """
        if not api_base:
            raise SecurityViolationError("API base URL cannot be empty.")
        
        parsed = urlparse(api_base)
        if parsed.scheme not in ["https", "http"]:
            raise SecurityViolationError(f"Unsupported URL scheme: {parsed.scheme}")

        hostname = (parsed.hostname or "").lower()
        if hostname in cls.BLOCKED_HOSTNAMES or hostname.startswith("169.254."):
            raise SecurityViolationError(f"SSRF protection: destination '{hostname}' is blocked.")

        # Require HTTPS for external domains (allow http only for localhost/127.0.0.1 development servers)
        if parsed.scheme == "http" and hostname not in ["localhost", "127.0.0.1", "::1"]:
            raise SecurityViolationError(
                f"Insecure transport blocked: external provider endpoint '{api_base}' must use HTTPS."
            )

        return api_base

    def generate(self, model: str, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1500) -> Dict[str, Any]:
        api_key = os.environ.get(self.config.api_key_env, "")
        if not api_key:
            # Degrade gracefully to local deterministic fallback if no API key is set
            res = LocalDeterministicProvider().generate(model, prompt, system_prompt, max_tokens)
            res["provider_available"] = False
            res["provider_called"] = False
            res["actual_model"] = "NONE"
            res["actual_provider"] = "NONE"
            res["fallback_used"] = True
            return res

        # Validate endpoint against SSRF
        try:
            self.validate_api_endpoint(self.config.api_base)
        except SecurityViolationError as sve:
            return {
                "text": f"Security Error: {str(sve)}",
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_seconds": 0.0,
                "model": model,
                "selected_model": model,
                "actual_model": "NONE",
                "provider_available": True,
                "provider_called": False,
                "actual_provider": "NONE",
                "fallback_used": True,
                "success": False,
                "error": str(sve),
            }

        # Pre-transmission secret redaction
        clean_prompt, _ = SecretRedactor.redact(prompt, mode=SecurityMode.BALANCED)
        clean_sys_prompt, _ = SecretRedactor.redact(system_prompt or "", mode=SecurityMode.BALANCED) if system_prompt else ("", 0)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Silvirica-AI-Runtime/0.1.0",
        }
        messages = []
        if clean_sys_prompt:
            messages.append({"role": "system", "content": clean_sys_prompt})
        messages.append({"role": "user", "content": clean_prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }

        url = f"{self.config.api_base.rstrip('/')}/chat/completions"
        start_time = time.time()

        # Attempt with requests if available, otherwise use stdlib urllib.request
        try:
            import requests
            resp = requests.post(url, headers=headers, json=payload, timeout=self.config.timeout_seconds)
            latency = time.time() - start_time
            if resp.status_code == 200:
                data = resp.json()
                choice = data.get("choices", [{}])[0]
                text = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})
                return {
                    "text": text,
                    "input_tokens": usage.get("prompt_tokens", len(clean_prompt) // 4),
                    "output_tokens": usage.get("completion_tokens", len(text) // 4),
                    "latency_seconds": latency,
                    "model": model,
                    "selected_model": model,
                    "actual_model": model,
                    "provider_available": True,
                    "provider_called": True,
                    "actual_provider": "openai_compatible",
                    "fallback_used": False,
                    "success": True,
                    "error": None,
                }
            else:
                return {
                    "text": f"Provider error: HTTP {resp.status_code} - {resp.text}",
                    "input_tokens": len(clean_prompt) // 4,
                    "output_tokens": 0,
                    "latency_seconds": latency,
                    "model": model,
                    "selected_model": model,
                    "actual_model": "NONE",
                    "provider_available": True,
                    "provider_called": True,
                    "actual_provider": "openai_compatible",
                    "fallback_used": True,
                    "success": False,
                    "error": resp.text,
                }
        except (ImportError, ModuleNotFoundError):
            # Zero-dependency standard library fallback using urllib.request
            try:
                import urllib.request
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
                context = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=self.config.timeout_seconds, context=context) as response:
                    resp_body = response.read().decode("utf-8")
                    data = json.loads(resp_body)
                    choice = data.get("choices", [{}])[0]
                    text = choice.get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    latency = time.time() - start_time
                    return {
                        "text": text,
                        "input_tokens": usage.get("prompt_tokens", len(clean_prompt) // 4),
                        "output_tokens": usage.get("completion_tokens", len(text) // 4),
                        "latency_seconds": latency,
                        "model": model,
                        "selected_model": model,
                        "actual_model": model,
                        "provider_available": True,
                        "provider_called": True,
                        "actual_provider": "openai_compatible",
                        "fallback_used": False,
                        "success": True,
                        "error": None,
                    }
            except Exception as e:
                latency = time.time() - start_time
                return {
                    "text": f"Provider connection error: {str(e)}",
                    "input_tokens": len(clean_prompt) // 4,
                    "output_tokens": 0,
                    "latency_seconds": latency,
                    "model": model,
                    "selected_model": model,
                    "actual_model": "NONE",
                    "provider_available": True,
                    "provider_called": False,
                    "actual_provider": "NONE",
                    "fallback_used": True,
                    "success": False,
                    "error": str(e),
                }
        except Exception as e:
            latency = time.time() - start_time
            return {
                "text": f"Connection error: {str(e)}",
                "input_tokens": len(clean_prompt) // 4,
                "output_tokens": 0,
                "latency_seconds": latency,
                "model": model,
                "selected_model": model,
                "actual_model": "NONE",
                "provider_available": True,
                "provider_called": False,
                "actual_provider": "NONE",
                "fallback_used": True,
                "success": False,
                "error": str(e),
            }


class LocalDeterministicProvider(AIProvider):
    """
    Offline local deterministic fallback and benchmark engine.
    Produces structured responses directly from compiled context without calling external clouds.
    """
    def generate(self, model: str, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1500) -> Dict[str, Any]:
        start_time = time.time()
        import re

        # Extract symbols, call hierarchy, memory, and code blocks from compiled prompt
        symbols_match = re.search(r"## Exact Code Symbols\s*\n(.*?)(?=\n##|\Z)", prompt, re.DOTALL)
        deps_match = re.search(r"## Direct Dependencies\s*\n(.*?)(?=\n##|\Z)", prompt, re.DOTALL)
        callers_match = re.search(r"## Call Hierarchy & Dependents\s*\n(.*?)(?=\n##|\Z)", prompt, re.DOTALL)
        code_match = re.search(r"## Targeted Code Context\s*\n(.*?)(?=\n##|\Z)", prompt, re.DOTALL)
        memory_match = re.search(r"## Verified Project Memory\s*\n(.*?)(?=\n##|\Z)", prompt, re.DOTALL)

        response_parts = [
            "**[Silvirica Local Intelligence Fallback Response]**",
            "",
            "The required model provider is not configured. I found the following relevant local context:",
            "",
        ]

        has_context = False
        if symbols_match and symbols_match.group(1).strip():
            has_context = True
            response_parts.append("### Relevant Code Symbols:")
            sym_clean = re.sub(r"<!-- UNTRUSTED_DATA_BOUNDARY.*?-->\n?", "", symbols_match.group(1).strip())
            response_parts.append(sym_clean)
            response_parts.append("")

        if deps_match and deps_match.group(1).strip():
            has_context = True
            response_parts.append("### Dependencies:")
            deps_clean = re.sub(r"<!-- UNTRUSTED_DATA_BOUNDARY.*?-->\n?", "", deps_match.group(1).strip())
            response_parts.append(deps_clean)
            response_parts.append("")

        if callers_match and callers_match.group(1).strip():
            has_context = True
            response_parts.append("### Call Hierarchy:")
            callers_clean = re.sub(r"<!-- UNTRUSTED_DATA_BOUNDARY.*?-->\n?", "", callers_match.group(1).strip())
            response_parts.append(callers_clean)
            response_parts.append("")

        if code_match and code_match.group(1).strip():
            has_context = True
            response_parts.append("### Code Context:")
            code_clean = re.sub(r"<!-- UNTRUSTED_DATA_BOUNDARY.*?-->\n?", "", code_match.group(1).strip())
            response_parts.append(code_clean)
            response_parts.append("")

        if memory_match and memory_match.group(1).strip():
            has_context = True
            response_parts.append("### Project Memory:")
            mem_clean = re.sub(r"<!-- UNTRUSTED_DATA_BOUNDARY.*?-->\n?", "", memory_match.group(1).strip())
            response_parts.append(mem_clean)
            response_parts.append("")

        if not has_context:
            response_parts.append("No matching code symbols or files were located in the repository index for this query.")
            response_parts.append("")

        response_parts.append("*(Note: To enable cloud reasoning, configure OPENAI_API_KEY in environment or .silvirica/config.yaml)*")
        response_text = "\n".join(response_parts)

        latency = time.time() - start_time
        return {
            "text": response_text,
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(response_text) // 4,
            "latency_seconds": max(0.005, latency),
            "model": model,
            "selected_model": model,
            "actual_model": "NONE",
            "provider_available": False,
            "provider_called": False,
            "actual_provider": "NONE",
            "fallback_used": True,
            "success": True,
            "error": None,
        }
