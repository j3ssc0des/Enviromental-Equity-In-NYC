---
name: audit-nyc-environment-data
description: Audit NYC Environmental Atlas sources for reachability, schema drift, provenance, missingness, geography mismatches, and suspicious value changes. Use before adding or updating environmental datasets, changing scoring methods, rebuilding the map, diagnosing a scheduled refresh, or publishing data-derived claims.
---

# Audit NYC Environmental Data

Protect the published site from stale, silently transformed, or fabricated data.

## Workflow

1. Read `data/sources.json` and `docs/methodology.md`.
2. Run `python3 .skillshare/skills/audit-nyc-environment-data/scripts/audit_sources.py`.
3. Stop publication if an active source is unreachable, required fields disappear, coverage falls below the pipeline threshold, or the build enters demo mode.
4. Inspect `data/metadata/source-audit.json` and the generated validation report.
5. Confirm every mapped metric includes source, unit, native geography, reference period, retrieval time, method, and estimated status.
6. Compare record counts, null rates, minima, maxima, and percentiles with the previous successful build. Investigate material shifts before accepting them.
7. Keep datasets in their native geography unless a documented spatial or population-weighted crosswalk exists. Never fuzzy-match place names or fill neighborhoods with borough/city defaults.
8. Rebuild only after the audit passes. Verify narrative claims against the same generated artifact.

## Adding a source

Add it to `data/sources.json` as `next`, document its native geography in `docs/data-catalog.md`, and inspect sample records. Promote it to `active` only after implementing tests, provenance fields, missing-data behavior, and a reproducible transformation.

## Agent review tasks

- Data steward: verify source definitions, years, units, and cadence.
- Geography reviewer: verify CRS, land-area denominators, crosswalk coverage, and boundary versions.
- Statistical reviewer: verify aggregation, uncertainty, weights, and sensitivity.
- Editorial reviewer: reject unsupported causal, “live,” “safe,” or “hazardous” claims.

These review roles complement, but never replace, deterministic CI checks.
