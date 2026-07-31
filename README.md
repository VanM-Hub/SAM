# SAM Framework

**The Autonomous Guardian Operating System for AI** 🔰  
*Versi: v13.0.0 - Mission Runtime*

---

## Ringkasan

SAM adalah platform guardian otonom — mengamati, melindungi, dan memulihkan sistem AI. Dikembangkan dari foundation hingga runtime kernel (10 fase) + Universal Connector Runtime (Phase XI) + Orchestration Runtime (Phase XII) + Mission Runtime (Phase XIII).

**Status: 13 fase selesai dari 13 fase terencana.**

| Fase | Sprint | Versi | Komponen Utama |
|------|--------|-------|---------------|
| I | 1–7 | v0.0.1 | Foundation: agent state, telemetry, contracts |
| II | 8–17 | v2.0.0 | Operational Brain (plan, archive, monitor, visualize) |
| III | 18–29 | v3.0.0 | Guardian Intelligence (observation, policies, event engine) |
| IV | 30–42 | v4.0.0 | Guardian Runtime (dispatcher, reasoning, learning, dashboard) |
| V | 43–58 | v5.0.0–v6.0.0 | Guardian Live Runtime + Live Situation Intelligence |
| VI | 59–75 | v6.0.0–v7.0.0 | Decision Runtime (certification, finalization, lifecycle) |
| VII | 76–81 | v7.0.0–v8.0.0 | Operational Brain Full Integration |
| VIII | 82–87 | v8.0.0–v8.5.0 | Activation Runtime (6 sprints, ~48 files, pipeline lengkap) |
| IX | 88–99 | v9.0.0–v9.11.0 | Execution Runtime (12 sprints, ~1,600 tests, 15 bridges) |
| **X** | **100-111** | **v10.0.0** | **Runtime Kernel (12 sprints, 1,719 tests, 69 files, 60 cards)** |
| **XI** | **112-122** | **v11.0.0** | **Universal Connector Runtime (11 sprints, 220 tests, 77 files)** |
| **XII** | **123-133** | **v12.0.0** | **Orchestration Runtime (11 sprints, 172 tests, 78 files)** |
| **XIII** | **134-143** | **v13.0.0** | **Mission Runtime (10 sprints, 145 tests, 70 files)** |

> **Phase XIV (menunggu):** Real Connector Implementations — adapter provider (OpenClaw, OpenAI, GitHub, Docker) sebagai plugin di atas fondasi yang sudah matang. Phase XV: Operational Intelligence Console.

---

## Fitur v10.0.0 — Runtime Kernel

Runtime Kernel adalah lapisan koordinasi antar-subsystem. Preview-only, read-only, tidak memodifikasi subsystem lain.

**12 Subsystem:**

| Subsystem | Engine | Bridge |
|-----------|--------|--------|
| Context | IdentityBuilder, EnvironmentEngine, ProfileEngine, ConfigurationEngine | ConversationRuntimeContext + Dashboard |
| Registry | RuntimeCatalog, Locator, DescriptorEngine, ManifestEngine | ConversationRegistry + Dashboard |
| State | StateMachineEngine (FSM 7 states/8 transitions), SnapshotEngine, StateHistory | ConversationState + Dashboard |
| Lifecycle | LifecycleManager (startup 6-phases, shutdown, restart) | ConversationLifecycle + Dashboard |
| Bridge | AdapterRegistry, BridgeRouter, TransformEngine, ProtocolMapper | ConversationBridge + Dashboard |
| Health | HealthChecker, HealthEngine (thresholds), ResourceMonitor | ConversationHealth + Dashboard |
| Security | SecurityManager, AccessController, AuditLogger, VerdictEngine | ConversationSecurity + Dashboard |
| Scheduler | SchedulerEngine, TaskScheduler, WindowScheduler, PriorityAllocator | ConversationScheduler + Dashboard |
| Event Bus | EventBus (pub/sub), EventDispatcher, EventLogger, EventFilter | ConversationEvent + Dashboard |
| Coordinator | CoordinationEngine, SyncCoordinator, Orchestrator | ConversationCoordinator + Dashboard |
| Telemetry | TelemetryCollector, MetricsAggregator, TelemetryReporter | ConversationTelemetry + Dashboard |
| Final Assembly | FinalInspector (11 components), KernelReporter | ConversationFinal + Dashboard |

- **69 file** sumber di `src/sam/runtime_kernel/`
- **60 Dashboard Cards** (5 per subsystem, frozen ExecutionCards)
- Semua DTO immutable (`frozen dataclass`) — **0 forbidden imports**
- Synchronous, deterministic, rule-based

---

## Pipeline

```
Phase I     Foundation                           v0.0.1
Phase II    Operational Brain                    v2.0.0
Phase III   Guardian Intelligence                v3.0.0
Phase IV    Guardian Runtime                     v4.0.0
Phase V     Guardian Live Intelligence           v5.0.0–v6.0.0
Phase VI    Decision Runtime                     v6.0.0–v7.0.0
Phase VII   Operational Brain Integration        v7.0.0–v8.0.0
Phase VIII  Activation Runtime                   v8.0.0–v8.5.0
Phase IX    Execution Runtime                    v9.0.0–v9.11.0
Phase X     Runtime Kernel                       v10.0.0

Pipeline Runtime Kernel:
  Boot → Context → Registry → State → Lifecycle → Bridge
  → Health → Security → Scheduler → Event Bus → Coordinator
  → Telemetry → Final Assembly → **Runtime Kernel Ready**
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/VanM-Hub/SAM.git
cd SAM

# Setup (Windows PowerShell)
$env:PYTHONPATH = "./src"
$env:PYTHONIOENCODING = "utf-8"

# Install dependencies
pip install -e ".[dev,console]"

# Jalankan test
python -m pytest tests/unit/ -q --tb=short
```

---

## Testing

**Test count: 1,719+** (sprint 100–111 validation tests)
**Unit tests:** 1,282+ (lokal, berjalan normal)

```powershell
# Semua test unit
python -m pytest tests/unit/ -q --tb=short

# Sprint validation (contoh: sprint 100)
python -m pytest tests/sprint100/ -q --tb=short
```

---

## Struktur Folder

```
SAM/
├── src/sam/                  # Source code
│   ├── activation/           # Phase VIII
│   ├── approval/             # Phase VI
│   ├── execution/runtime/    # Phase IX
│   ├── guardian/live/        # Phase V
│   ├── operational_brain/    # Phase II
│   ├── operations/brain/decision/  # Phase VI
    └── runtime_kernel/       # Phase X (baru)
├── tests/
│   ├── unit/                 # 1,282+ unit tests
│   ├── sprint100/ - sprint111/  # 1,719 sprint validation
├── docs/
│   ├── reports/              # OP reports
│   ├── sprint-reports/       # Per-sprint laporan
│   └── architecture/         # Dokumentasi arsitektur
├── data/                     # Database migrations
└── .github/workflows/        # CI (core + desktop)
```

---

## Lisensi

Apache-2.0 — lihat file LICENSE.
