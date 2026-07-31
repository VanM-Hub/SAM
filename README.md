# SAM Framework

**The Autonomous Guardian Operating System for AI** 🔰  
*Versi: v17.0.0 - Memory Runtime*

---

## Ringkasan

SAM adalah **Deterministic Operational Intelligence Platform** — mengobservasi, memahami, merencanakan, mengoordinasikan, menyiapkan, dan mengawasi operasi lintas sistem secara aman, dapat diaudit, provider-agnostic, dan dapat dipertanggungjawabkan.

AI hanyalah **salah satu provider** yang dapat dipasang melalui Connector Runtime — identitas SAM tetap utuh walaupun provider AI diganti.

**Versi aktif:** v17.0.0 — Memory Runtime (Phase XVII)
**Fase aktif terakhir:** XVII — selesai ✅
**Status:** 17 dari 20 fase selesai (I–XVII).
**Fase berikutnya:** XVIII — Execution Integration (PLANNED)

> 📌 **Seluruh peta fase dari awal hingga akhir** (Phase I–XX) ada di [**ROADMAP.md**](ROADMAP.md) — sumber kebenaran tunggal.

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
