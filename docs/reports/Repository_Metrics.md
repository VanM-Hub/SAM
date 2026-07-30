# Repository Metrics

> **SAM v10.2.0** — Architecture Governance Baseline
> **File:** `docs/reports/Repository_Metrics.md`
> **Date:** 2026-07-30

---

## Code Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Total Python files | ~1,035 | All `.py` files in `src/sam/` |
| Source modules | ~957 | Excluding tests |
| Subsystems (active) | 10 | guardian/live, approval, activation, execution/runtime, operational_brain, runtime_kernel, operations/brain/decision, cli, desktop, launcher |
| Subsystems (legacy) | 26 | Pre-v5.0, not actively maintained |
| Packages (src/sam/) | 52 | As of Architecture Freeze v10 |

## DTO Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Total DTOs (frozen dataclasses) | 1,010 | From DTO Catalog scan |
| DTO violations | 0 | All frozen, no mutable defaults |
| DTO packages | 20+ | Scattered across subsystems |

## Bridge Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Conversation bridges | 82 | 12 per runtime × 7 runtimes (some gaps) |
| Dashboard bridges | 122 | 5-6 ExecutionCards per subsystem |
| Total bridge extensions | 357 | bridges + plugins + dashboards + providers + adapters + launchers |

## Extension Point Metrics

| Type | Count |
|------|-------|
| Bridge Extensions | 82 |
| Plugin Extensions | 54 |
| Provider Extensions | 53 |
| Dashboard Extensions | 122 |
| Adapter Extensions | 36 |
| Launcher Extensions | 8 |

## Test Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Total tests collected | 9,661 | Full collection |
| Unit tests passing | 1,282 | Core unit suite |
| Legacy tests | ~44 | Not imported in standard run |
| Test files | 100+ | Sprint folders + dedicated test files |
| Test coverage | N/A | Not measured (no coverage tool configured) |

## ADR Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| ADR files | 1 | `ADR-001_to_008.md` (8 ADRs in one file) |
| ADR decisions | 8 | Overall Architecture, Runtime Isolation, Immutable DTO, Preview-Only, Approval Boundary, Subsystem Independence, Repository Structure, Runtime Kernel |

## Diagram Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Architecture diagrams | 10 | 01–10 numbered HTML files |
| Detailed diagrams | 3 | Subsystem Overview, Pipeline Overview, Runtime Kernel |
| Skeleton diagrams | 7 | Runtime Relationship, Dependency Graph, Decision Flow, Approval Flow, Operational Flow, Execution Flow, Complete Architecture |

## Documentation Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Architecture docs | 12 | All in `docs/architecture/` |
| Release docs | 2 | `version-history.md`, `manifest.md` |
| ADR files | 1 | `docs/adr/ADR-001_to_008.md` |
| Sprint reports | 60+ | In `docs/sprint-reports/` |
| OP reports | 30+ | In `docs/reports/` |
| Governance docs | 10 | Rulebook, forbidden matrix, health, metrics, checklist, PR template, release checklist, 6 validation scripts |

## CI Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Workflow files | 2 | `ci.yml` + `_check_ci.py` |
| CI jobs | 2 | Core (quality gate), Desktop (needs Core) |
| Python versions | 3 | 3.10, 3.11, 3.12 (core only) |
| Validation scripts | 6 | Integrated into Architecture Validation stage |

## Governance Metrics

| Metric | Count | Notes |
|--------|-------|-------|
| Validation scripts | 6 | imports, layers, dto, pipeline, structure, docs |
| Rulebook rules | 60+ | 12 categories, 5 rules each |
| Forbidden dependency entries | 12 subsystems | Each with allowed/forbidden/friend/extension |
| Checklist items | 40+ | Contributor + PR + Release combined |

## Overall Repository Health

| Score | Domain |
|-------|--------|
| 10/10 | API Stability |
| 10/10 | Dependency |
| 9/10 | Layer |
| 10/10 | DTO |
| 9/10 | Documentation |
| 8/10 | Tests |
| 8/10 | CI |
| 8/10 | Repository |
| 9/10 | Structure |
| 10/10 | Pipeline |
| 9/10 | Architecture Validation |
| 9/10 | Governance |
| **109/120 (90.8%)** | **OVERALL** |
