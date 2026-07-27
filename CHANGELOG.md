# Changelog

## v2.0.0 (2026-07-27) — Production Release 🎉

SAM v2.0.0 adalah rilis produksi pertama yang mencakup 7 fase pengembangan.

### Added
- **Runtime Kernel** — 12-state state machine, bootstrap pipeline (10 step), session CRUD (JSON), graceful shutdown (6 step), crash recovery dengan checkpoint
- **Guardian Kernel** — Observer, Analyzer, Decision, Policy, Action, Verification engine + 10-stage GDP pipeline
- **Hosting Layer** — DesktopAdapter, DockerAdapter, Windows Service (pywin32), systemd unit generator, Dockerfile + docker-compose.yml
- **Telemetry & Metrics** — TelemetryEvent, RuntimeMetrics, TelemetryService (10000 event buffer), MetricsCollector (periodic CPU/memory/uptime), FastAPI REST API (4 endpoints)
- **Operations Console CLI** — 17 commands: status, health, session, runtime, plugins, knowledge, memory, workflow, events, guardian, service, logs, metrics, openclaw, intelligence, autonomous, web
- **OpenClaw Integration** — Discovery (known locations, AppData, env, glob), health collector (4 components + real health.json parsing), log analyzer (5 severity patterns, 4 log locations)
- **Operational Intelligence** — IncidentDetector (log errors + health components), RootCauseAnalyzer (8 pattern rules + knowledge lookup), Recommender (4 step templates, risk-based), KnowledgeLookup (6 built-in entries)
- **Autonomous Operations** — ActionExecutor (safety pipeline), SafetyPolicy (risk matrix, auto-approve, blocked actions), ApprovalManager (30-min expiry, approve/deny), AutoRecovery (4 strategies), PluginIsolation (8 plugins)
- **Web Dashboard** — FastAPI + Jinja2 + HTMX (dark theme, 8 pages, sidebar nav)
- **Contracts** — Mission, DOS, Runtime contracts (Pydantic v2)
- **Graceful Degradation** — Mission/DOS loaders return defaults on missing/invalid files

### Architecture
- 6 ADR (015–020): Hosting Independence, State Machine, Session Persistence, Graceful Shutdown, Crash Recovery, Lifecycle Events
- SAM Constitution — 10 pasal hukum tertinggi
- Golden Rule: Mission > Safety > Autonomy > Runtime > All

### Test Coverage
- **287 tests** (unit + integration), 1 skipped
- **0 regressions**
- Coverage ≥80% pada semua modul Phase 0-1

### Performance
- Coordinator init: ~464ms
- Import time: ~49ms (top-level), ~994ms (CLI full)
- Model serialization: ~0.5ms/call
- Full test suite: ~13s

---

## v1.0.0 (2026-07-27) — GA Release

Rilis awal SAM Framework dengan kemampuan:
- Self-Evolution Engine
- Cognitive Runtime
- Cross-Cluster Intelligence
- Knowledge Federation
- Autonomous Runtime & Safety
- Production Readiness (10 komponen)
- Release tag: `v1.0.0`
- Commit: `aeb20d5`
- Architecture frozen (public API, CLI, DB schema)

Sebelum v1.0 GA, terdapat 3 rilis kandidat:
- **v1.0.0-rc3** — Sprint 33: production readiness
- **v1.0.0-rc2** — Sprint 29–32: autonomous, federation, cognitive
- **v1.0.0-rc1** — Sprint 28: self-evolution engine
