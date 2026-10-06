from __future__ import annotations
from typing import Any, Dict, List


class BenchmarkReporter:
    """
    Renders benchmark scoreboard and results in terminal and markdown with Correctness Gates.
    """

    @classmethod
    def render(cls, results: List[Dict[str, Any]]) -> str:
        total_naive_tokens = sum(r["naive"]["input_tokens"] for r in results)
        total_silv_tokens = sum(r["silvirica"]["input_tokens"] for r in results)
        total_saved = total_naive_tokens - total_silv_tokens
        overall_reduction = round((total_saved / total_naive_tokens) * 100, 1) if total_naive_tokens > 0 else 0.0
        all_passed = all(r.get("correctness_gate", {}).get("passed", True) for r in results)

        out = []
        out.append("==========================================================================================")
        out.append("                   SILVIRICA AI BENCHMARK SCOREBOARD                                      ")
        out.append("                 (BASELINE vs SURGICAL SILVIRICA PIPELINE)                                ")
        out.append("==========================================================================================")
        out.append(f"{'SCENARIO':<32} | {'BASELINE (Tokens)':<17} | {'SILVIRICA CONTEXT':<18} | {'REDUCTION':<10} | {'GATE':<6}")
        out.append("------------------------------------------------------------------------------------------")

        for r in results:
            title = r["title"][:31]
            naive_tok = f"{r['naive']['input_tokens']:,}"
            silv_tok = f"{r['silvirica']['input_tokens']:,}" if not r["silvirica"]["zero_model"] else "0 (Zero-Model)"
            savings = f"{r['reduction_percentage']}%"
            gate = "PASS" if r.get("correctness_gate", {}).get("passed", True) else "FAIL"
            out.append(f"{title:<32} | {naive_tok:<17} | {silv_tok:<18} | {savings:<10} | {gate:<6}")

        out.append("==========================================================================================")
        out.append(f"TOTAL BASELINE CONTEXT:    {total_naive_tokens:,} tokens")
        out.append(f"TOTAL SILVIRICA CONTEXT:   {total_silv_tokens:,} tokens")
        out.append(f"TOTAL CONTEXT REDUCED:     {total_saved:,} tokens (TOTAL TOKENS SAVED: {total_saved:,})")
        out.append(f"OVERALL CONTEXT REDUCTION: {overall_reduction}% (OVERALL TOKEN REDUCTION: {overall_reduction}%)")
        out.append(f"CORRECTNESS GATE STATUS:   {'ALL GATES PASSED (Verified)' if all_passed else 'SOME GATES FAILED'}")
        out.append("==========================================================================================")

        return "\n".join(out)

    @classmethod
    def format_table(cls, results: List[Dict[str, Any]]) -> str:
        return cls.render(results)

