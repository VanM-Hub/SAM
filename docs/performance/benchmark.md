# Performance Benchmark — v1.0

**Date:** 2026-07-25  
**Environment:** Python 3.8.7, Windows 10, Intel x64, sqlite3 (local file)

---

## Startup Performance

| Operation | Time | Conditions |
|---|---|---|
| Python import all modules | ~0.8s | Cold start, no caching |
| CLI `sam --help` | ~1.2s | Includes 10 registered sub-apps |
| Database creation + 47 migrations | ~0.3s | New sqlite3 file |
| Database open (existing) | ~0.05s | Schema check only |

## Core Operations

| Operation | Avg Time | Notes |
|---|---|---|
| CognitiveState update | ~0.001s | Immutable copy + archive |
| WorkingMemory set/get | ~0.0005s | Dict-based |
| Attention focus determination | ~0.005s | Reads state + context |
| Goal arbitration (6 goals) | ~0.01s | Full scoring + adjustments |
| SelfHealingLoop (1 cycle) | ~0.02s | 9 phases (mocked healing) |
| Autotuner analyze (10 metrics) | ~0.005s | Metric → param matching |
| Cluster state aggregation (5 nodes) | ~0.003s | Average confidence + mode focus |
| Strategy proposal vote | ~0.001s | Verify + record |
| Federation message exchange | ~0.001s | In-memory message routing |
| Autonomy controller adjust | ~0.002s | Confidence/risk evaluation |
| SafetyEnvelope check | ~0.0005s | Boundary comparison |
| Guardrails evaluate (5 rules) | ~0.002s | Condition matching |
| Self-assessment (before) | ~0.001s | Risk + issue analysis |

## Database Operations

| Operation | Avg Time | Conditions |
|---|---|---|
| `SELECT` single row by PK | ~0.0003s | Indexed |
| `SELECT` with filter | ~0.0005s | Indexed column |
| `INSERT` single row | ~0.0004s | — |
| `INSERT` batch 100 | ~0.01s | — |
| Full migration (47 files) | ~0.35s | Sequential, idempotent |

## Test Suite Performance

| Metric | Value |
|---|---|
| Total tests | ~1824 |
| Full suite duration | ~458s (7:38) |
| Average per test | ~0.25s |
| Bottleneck | Integration tests with temp DB per fixture |

## Memory Usage

| Scenario | Memory |
|---|---|
| Idle (after import) | ~35 MB |
| Active (1 cognitive session) | ~40 MB |
| Active (10k WM entries) | ~50 MB |
| Full test suite (peak) | ~80 MB |
| Steady state (production) | ~40–60 MB |

## Throughput Estimates

| Scenario | Ops/sec |
|---|---|
| WorkingMemory get/set | ~2000/s |
| CognitiveState updates | ~1000/s |
| SafetyEnvelope checks | ~2000/s |
| Guardrails evaluations | ~500/s |
| Database inserts (single) | ~2500/s |
| Database inserts (batch) | ~10000/s |

## Bottlenecks & Recommendations

| Bottleneck | Impact | Recommendation |
|---|---|---|
| Per-test DB creation | 60% of test time | Share DB across related tests |
| Pydantic V2 warnings | ~2s overhead | Upgrade to Python 3.12+ |
| sqlite3 single-writer | Sequential writes | Future: switch to PostgreSQL |
| In-memory only (no persistence) | Data loss on restart | Enable DB persistence in production |

---

*Document prepared for SAM v1.0.0 release.*
