from __future__ import annotations
from typing import Any, Dict, List


class BenchmarkReporter:
    """
    Renders benchmark scoreboard and results in terminal and markdown.
    """

    @classmethod
    def render(cls, results: List[Dict[str, Any]]) -> str:
        total_naive_tokens = sum(r["naive"]["input_tokens"] for r in results)
        total_silv_tokens = sum(r["silvirica"]["input_tokens"] for r in results)
        total_saved = total_naive_tokens - total_silv_tokens
        overall_reduction = round((total_saved / total_naive_tokens) * 100, 1) if total_naive_tokens > 0 else 0.0

        out = []
        out.append("================================================================================")
        out.append("                   SILVIRICA AI BENCHMARK SCOREBOARD                            ")
        out.append("                      (WITHOUT vs WITH SILVIRICA)                               ")
        out.append("================================================================================")
        out.append(f"{'SCENARIO':<35} | {'WITHOUT (Tokens)':<16} | {'WITH SILVIRICA':<15} | {'SAVINGS':<10}")
        out.append("--------------------------------------------------------------------------------")

        for r in results:
            title = r["title"][:34]
            naive_tok = f"{r['naive']['input_tokens']:,}"
            silv_tok = f"{r['silvirica']['input_tokens']:,}" if not r["silvirica"]["zero_model"] else "0 (Zero-Model)"
            savings = f"{r['reduction_percentage']}%"
            out.append(f"{title:<35} | {naive_tok:<16} | {silv_tok:<15} | {savings:<10}")

        out.append("================================================================================")
        out.append(f"TOTAL NAIVE CONTEXT:       {total_naive_tokens:,} tokens")
        out.append(f"TOTAL SILVIRICA CONTEXT:   {total_silv_tokens:,} tokens")
        out.append(f"TOTAL TOKENS SAVED:        {total_saved:,} tokens")
        out.append(f"OVERALL TOKEN REDUCTION:   {overall_reduction}%")
        out.append("================================================================================")

        return "\n".join(out)

    @classmethod
    def format_table(cls, results: List[Dict[str, Any]]) -> str:
        return cls.render(results)
