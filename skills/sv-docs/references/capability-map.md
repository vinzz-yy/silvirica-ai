# Capability and Public Skill Map

Load this reference for questions about what Silvirica can do, which skill fits a
task, the public ULW family, or how many skills are installed.

## Retrieve the Current Catalog

- For the public catalog, inspect the generated
  `skills/Silvirica-routing/references/catalog-index.md` and
  `skills/Silvirica-routing/references/workflow-registry.md` on the disclosed official
  ref, or run `Silvirica docs workflows --json` from a version-pinned checkout.
  Registry IDs and internal fields are not public display names; derive public
  names with `src/skills/catalog_types.py` and
  `src/routing/display_names.py`.
- `Silvirica list --json` reports only the current installed manifest. Count those
  returned records only when the user asks about `current_local_install`; a
  clean or differently profiled home can legitimately report zero skills.
- Use `Silvirica recommend "<intent>" --json --limit 3` for a bounded recommendation;
  a recommendation is not a reason to dump or memorize the full catalog.
- Verify the six capability families in `src/capabilities/families.py` at the
  disclosed ref.

Never hard-code a mutable public catalog or installed-manifest count in an
answer or in the always-loaded skill body. They answer different questions and
can differ by version and profile.

## Six Capability Families

Use the current projection, whose public families are:

1. Plan and decide.
2. Learn and gather.
3. Retain knowledge.
4. Create materials and visuals.
5. Delegate coding and ship.
6. Operate and observe.

Representative exact public skills across the engineering-intelligence catalog:

| Area | Public skill examples |
| --- | --- |
| Operations | `Silvirica-support-operations`, `Silvirica-deploy-and-monitor` |
| Design | `Silvirica-design-orchestration`, `Silvirica-design-quality-gate` |
| Frontend | `Silvirica-frontend`, `Silvirica-frontend-refactor` |
| Finance and financial statements | `Silvirica-finance-analysis` |
| Planning | `ulw-plan`, `ulw-interview`, `ulw-context` |
| Research | `ulw-research`, `Silvirica-web-research`, `Silvirica-source-finder` |
| Inference serving | `Silvirica-inference-serving` |
| Reliability and review | `Silvirica-reliability-review`, `Silvirica-code-review` |
| Materials | `Silvirica-materials-package`, `Silvirica-report-package` |
| Retained knowledge | `Silvirica-memory-new`, `Silvirica-memory-sync`, `Silvirica-decision-recall`, `Silvirica-wiki` |

## Public ULW Names

When examples need an engine name, use only these current public labels:
`ulw-context`, `ulw-interview`, `ulw-research`, `ulw-plan`, `ulw-work`,
`ulw-maestro`, `ulw-loop`, `ulw-qa`, and `ulw-perf`.

Canonical implementation identifiers may differ internally. Do not expose an
internal identifier as the public skill name, and do not derive an installed
name by guessing from the canonical id.
