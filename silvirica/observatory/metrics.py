from __future__ import annotations
from typing import Any, Dict
from silvirica.observatory.telemetry import TelemetryStore


class ImprovementScoreCalculator:
    """
    Calculates the transparent Silvirica Improvement Score (0–100).
    Components:
    - Token Efficiency (35%)
    - Latency Improvement (20%)
    - Retrieval Precision (15%)
    - Cache Efficiency (15%)
    - Zero-Model Utilization (15%)
    """

    @classmethod
    def calculate_score(cls, summary: Dict[str, Any]) -> Dict[str, Any]:
        savings_pct = summary.get("savings_percentage", 0.0)
        cache_rate = summary.get("cache_hit_rate", 0.0)
        zero_model_rate = summary.get("zero_model_rate", 0.0)
        avg_latency = summary.get("avg_latency", 1.0)

        # Token efficiency component (max 35)
        token_score = min(35.0, (savings_pct / 90.0) * 35.0)

        # Latency score (max 20) -> lower latency is better
        lat_score = 20.0 if avg_latency < 0.2 else (20.0 * max(0.0, 1.0 - (avg_latency / 5.0)))

        # Cache score (max 15)
        cache_score = min(15.0, (cache_rate / 100.0) * 15.0)

        # Zero-Model score (max 15)
        zero_score = min(15.0, (zero_model_rate / 100.0) * 15.0)

        # Quality baseline (15)
        quality_score = 15.0

        total_score = int(round(token_score + lat_score + cache_score + zero_score + quality_score))
        total_score = max(0, min(100, total_score))

        return {
            "overall_score": total_score,
            "components": {
                "token_efficiency": round(token_score, 1),
                "latency_score": round(lat_score, 1),
                "cache_efficiency": round(cache_score, 1),
                "zero_model_utilization": round(zero_score, 1),
                "quality_baseline": round(quality_score, 1),
            },
        }


class MetricsCalculator:
    def __init__(self, telemetry_store: TelemetryStore):
        self.store = telemetry_store

    def calculate_summary(self) -> Dict[str, Any]:
        summary = self.store.get_summary()
        score_data = ImprovementScoreCalculator.calculate_score(summary)
        return {
            "silvirica_score": score_data["overall_score"],
            "tokens_saved_percent": summary.get("savings_percentage", 0.0),
            "avg_latency": summary.get("avg_latency", 0.0),
            "zero_model_count": int(summary.get("zero_model_rate", 0.0) * summary.get("total_queries", 0) / 100.0),
            "cache_hit_rate": summary.get("cache_hit_rate", 0.0),
            "total_queries": summary.get("total_queries", 0),
            "components": score_data["components"],
        }
