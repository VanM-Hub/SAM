# SAM Framework

**The Autonomous Guardian Operating System for AI** 🔰

SAM (Self-evolving AI Manager) adalah platform guardian otonom yang mengamati, melindungi, dan memulihkan sistem AI. Dari runtime kernel hingga event-driven live runtime, web dashboard, dan desktop console — SAM menangani seluruh siklus operasi.

## Fitur v9.11.0 — Execution Runtime (NEW)

| Fitur | Deskripsi |
|---|---|
| **Execution Runtime (NEW)** | Menerima Activation Package Ready → menghasilkan Execution Plan Ready. 12 sprint (88–99), ~1,600 tests, 35+ files. Preview-only, deterministic, synchronous. |
| **Execution Assembly** | AssemblyEngine merakit 7 komponen: Plan, Resources, Dependencies, Timeline, Alerts, Risk, Quality → Execution Plan Ready. |
| **Execution Resources** | ResourceAllocator, ResourcePlan, ConversationResources, DashboardResources (allocation, limits, availability, summary). |
| **Execution Dependencies** | DependencyGraphBuilder, DependencyValidator, ExecutionOrderResolver (topological sort, cycle detection). |
| **Execution Timeline** | TimelineBuilder, TimelineEvent, ExecutionWindow, Milestone, TimelineSnapshot. |
| **Execution Alerts** | AlertEngine dengan 5 operator (gt/lt/gte/lte/eq), rule registration, acknowledge, summary. |
| **Execution Simulation** | SimulationEngine dengan step tracking, result aggregation, multiple scenarios. |
| **Execution Budget/Cost** | BudgetEngine, CostEstimate, BudgetReport dengan over-budget detection. |
| **Execution Risk** | RiskEngine dengan factor-based scoring (effort, dependencies, priority), 4 risk levels. |
| **Execution Quality** | QualityEngine dengan 3 metrics (effort variance, dependency coverage, type diversity), QualityGate. |
| **15 Conversation Bridges** | Masing-masing 8 queries per subsystem. |
| **15 Dashboard Bridges** | Masing-masing 5 ExecutionCard per subsystem (75 total cards). |

## Pipeline Upgrade (Phase IX)

```
Activation Package Ready
       ↓
Execution Runtime (preview-only)
  ├── ExecutionRequest → ExecutionBuilder
  ├── ExecutionValidator + ExecutionStrategy
  ├── ResourcePlan + DependencyGraph + Timeline
  ├── AlertEngine + BudgetEngine + RiskEngine + QualityEngine
  ├── SimulationEngine
  └── AssemblyEngine → Execution Plan Ready
```

| Fitur | Deskripsi |
|---|---|
| **Guardian Live Runtime (NEW)** | Event-driven synchronous runtime: dispatcher → guardian → reasoning → learning → execution preview → dashboard → conversation. No async, no threading, no network. |
| **Guardian Runtime** | Observe-Analyze-Decide-Act-Verify (GDP) pipeline. Governance, risk assessment, execution readiness |
| **Learning Foundation** | Knowledge Base, Experience Repository, Pattern Evolution, Optimizer, Policy Engine |
| **Execution Pipeline** | Dispatch Runtime → Connector Runtime → Execution Engine → Adapter Layer → Provider Runtime |
| **External Integration** | 6 mock integrations: Slack, Discord, Email, Webhook, REST, Filesystem |
| **Plugin Ecosystem** | Registry, Loader, Policy, Runtime, 3 mock plugins |
| **Extension SDK** | PluginSDK, ConnectorSDK, ProviderSDK, Extension Validator |
| **Launcher Runtime** | Startup pipeline (8-stage), bootstrap orchestrator, safe mode, diagnostics, recovery |
| **Telemetry Foundation** | Event Taxonomy (36 types), Ring Buffer (1000 events), SQLite cache, JSON Schema |
| **Operations Engine** | Context, Status, Task, Knowledge, History, Settings, Explainability engines |
| **Desktop Console** | 8 halaman: Home, Task, Timeline, Knowledge, History, Settings, Explainability |
| **CLI** | 17 commands via `sam.cli.main` + lightweight `ops.py` commands |
| **Runtime Kernel** | State machine (12 state), bootstrap, session, shutdown, recovery |
| **Service Layer** | Windows Service, systemd, Docker, Desktop Launcher |
| **Observability** | Telemetry events, metrics collector, FastAPI REST API |
| **Operational Intelligence** | Incident detection, root cause analysis, recommendations |
| **Autonomous Operations** | Auto restart, recovery, resume, isolate, escalate, human approval |
| **Explainability** | Template-based explanations with evidence, impact, recommendations |

## Pipeline

```
Observation → Operational Brain → Reasoning Runtime → Decision Runtime
    → Guardian Runtime → Governance → Learning Foundation
    → Execution Pipeline → External Integration → Plugin Ecosystem
    → Extension SDK → **Guardian Live Runtime (v5.0.0)**
        ├── Event Dispatcher (priority-sorted, deterministic)
        ├── Reasoning Bridge
        ├── Learning Bridge
        ├── Execution Preview Bridge (preview only)
        ├── Dashboard Bridge (6 immutable cards)
        └── Conversation Bridge (10 queries)
    → Dashboard → Conversation → Host
```

## Quick Start

```bash
# Clone repo
git clone https://github.com/VanM-Hub/SAM.git
cd SAM

# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH (Windows PowerShell)
$env:PYTHONPATH = "./src"
$env:PYTHONIOENCODING = "utf-8"

# Atau (Linux/macOS)
# export PYTHONPATH="./src"
# export PYTHONIOENCODING="utf-8"

# Lihat semua CLI commands
python -m sam.cli.main --help

# Jalankan Desktop Console
python -m sam.desktop.main

# Atau gunakan CLI lightweight
python ops.py settings list
python ops.py history show
python ops.py task list
```

## CLI Commands

Legacy (17 commands via `sam.cli.main`):
```
status, health, session, runtime, plugins, knowledge, memory,
workflow, events, guardian, service, logs, metrics, openclaw,
intelligence, autonomous, web
```

Operations Platform (via `ops.py` — **ringan, tanpa dependensi legacy**):
```
ops.py task list              — daftar task
ops.py history show           — riwayat aktivitas
ops.py settings list          — pengaturan sistem
ops.py knowledge show         — knowledge & insight
ops.py explain recent         — penjelasan event
```

## Testing

```bash
# Windows PowerShell
$env:PYTHONPATH = "./src"
python -m pytest tests/unit/ -v --tb=short

# Linux/macOS
PYTHONPATH="./src" python -m pytest tests/unit/ -v --tb=short
```

**1414+ tests** (unit + sprint validation), 0 regressions.

## Arsitektur

Dokumentasi arsitektur: `docs/architecture/`

## Kontribusi

Baca [CONTRIBUTING.md](CONTRIBUTING.md) sebelum memulai.

## Lisensi

Apache-2.0 — lihat file LICENSE.
