---
name: "sv-decision-prototype"
description: "[Silvirica] Uncertain technical choice for a spike: bounded decision prototype workflow: resolve one uncertain interaction, API, performance, or integration choice with a disposable, isolated experiment whose observed result feeds planning. Use when the user says: decision-prototype, decision prototype, prototype this uncertain choice before planning, prototype before planning, prototype the uncertain choice, run a small spike, small spike, spike solution."
metadata:
  silvirica:
    tags: [workflow, silvirica-ai, planning]
    category: planning
    phase: decision-prototype
    role: planner
    quality_tier: decision-gated
---

# Decision Prototype

Required: one decision, a bounded experiment, an isolated scratch boundary, and a measurement method. Output: a decision record, prepared handoff, observation ledger, and receipt.

**HOLD:** Missing inputs or failed contract gates. Prepared Silvirica routing is not execution or approval. **Completion:** Follow the full-contract checklist.

Shared product, routing, compatibility, and evidence rules: `Silvirica-routing/references/skill-common-rail.md`.

Agent/operator: `Silvirica runtime workflow-artifact decision-prototype prepare --input <json-file-or->` prepares bounded metadata only. Shared operator reference: `Silvirica-routing/references/workflow-artifacts.md`.

Contract: `references/full-contract.md`. Procedure: `references/procedure.md`.

## Completion Checklist

- Preserve workflow intent and stop conditions; load the full contract before claiming completion.
- Reply in the user's own words and the host's own voice: its SOUL.md persona owns reply language, tone, speech level, and sentence endings, progress updates included (where it sets no language, use the one the user wrote in), and Silvirica shapes structure and content only; Silvirica's record terms (surface, lane, wrapper, handoff, evidence boundary, not_observed) stay in records and tool calls, never in the sentence the user reads unless they ask about one; and when a stop condition or a decision the user owns ends the turn, offer the next action as a question rather than declaring what will not be done.
- Record observed delegation results; otherwise return `not_available` or `not_observed`.
- Use Silvirica-native subagent/delegation features when available: native subagents -> Hermes delegation when available, otherwise sequential lanes.

## Recovery Notes

- If a required input, authority, or runtime capability is unavailable, HOLD and name the smallest safe next action; do not invent observation or approval.

## Workflow Lane

advisory local context
