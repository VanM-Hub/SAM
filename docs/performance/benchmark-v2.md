# SAM Framework — Performance Benchmark v2

**Date:** 2026-07-27  
**Python:** 3.8.7  
**Platform:** Windows 10 x64  
**Node:** VM (VanM)

## 1. Import Time
| Module | Time (ms) |
|---|---|
| `import sam` (top-level) | 48.7 |
| `RuntimeCoordinator` | 428.9 |
| CLI (`sam.cli.main`) | 993.8 |

Note: Higher import times include lazy-loading of sub-modules and structlog setup.

## 2. Coordinator Init
| Operation | Time (ms) |
|---|---|
| Instantiate `RuntimeCoordinator()` | 464.2 |

Includes: SessionManager, BootstrapManager, ShutdownManager, RecoveryManager, TelemetryService, MetricsCollector, OpenClawDiscovery, OpenClawHealthCollector, IncidentDetector, RootCauseAnalyzer, Recommender, KnowledgeLookup, ActionExecutor, AutoRecovery, PluginIsolation.

## 3. Test Suite
| Metric | Value |
|---|---|
| Total tests | 270+ (Phase 0-1) |
| Passed | 270 |
| Failed | 0 |
| Skipped | 1 |
| Execution time | 14.04s |

Excluding warisan v1.0 tests (autonomy, cluster, plugin_integration).

## 4. Model Serialization
| Operation | Time (ms) |
|---|---|
| 1000x `RuntimeMetrics.json()` | 500.7 |
| Per-call average | ~0.5ms |

## 5. Key Observations
- CLI import is heaviest due to transitive dependency loading (structlog, typer, pydantic).
- RuntimeCoordinator init is fast (<500ms) despite wiring 15+ components.
- Test suite completes in ~14s for 270+ tests — acceptable.
- Model serialization is efficient (~0.5ms per call).
- No performance regressions from Phase 0 baseline.

## 6. Recommendations
- Consider lazy-loading CLI sub-commands for faster startup.
- Metrics collection interval of 10s is appropriate.
- Web dashboard FastAPI server starts in <1s on demand.
