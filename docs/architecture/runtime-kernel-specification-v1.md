# SAM Runtime Kernel Specification v1.0

**Version:** 1.0  
**Status:** Final  
**Date:** 2026-07-27  

---

## Bab 0 — Architectural Principles

### AP-001 — Runtime Independence
Runtime tidak boleh mengetahui lingkungan hosting. Semua interaksi dengan platform melalui Hosting Adapter.

### AP-002 — Hosting Independence
Runtime dapat dijalankan di Desktop, Windows Service, systemd, Docker, Kubernetes, dan Embedded tanpa perubahan kode.

### AP-003 — Headless Core
Runtime adalah proses mandiri. GUI, CLI, dan Operations Console hanyalah client.

### AP-004 — Observable First
Semua perubahan lifecycle wajib menghasilkan Lifecycle Event.

### AP-005 — Recoverable Runtime
Setiap operasi penting memiliki Recovery Point.

### AP-006 — Contract Before Implementation
Seluruh komunikasi antar komponen melalui interface. Komponen tidak boleh mengakses implementasi internal komponen lain.

---

## Bab 1 — Objective & Scope

### Background
SAM Framework v1.0 telah memiliki capability utama tetapi belum memiliki Application Lifecycle.

### Objective
Membangun Runtime Lifecycle sehingga SAM dapat diinstal, dijalankan, melakukan bootstrap, memulihkan state, shutdown dengan aman, dan siap menerima pekerjaan.

### Target Pengalaman
Install → Run → SAM Ready

### Scope (Phase 0)
- Runtime Lifecycle
- Runtime Coordinator
- Launcher
- Bootstrap Pipeline
- Session
- Shutdown
- Recovery
- Hosting Adapter
- Health Endpoint

### Non-Goals (Phase 0)
- GUI penuh
- Operations Console
- Kubernetes deployment
- Multi-node cluster
- Distributed federation

---

## Bab 2 — Architecture Components

### 2.1 Launcher
**Responsibility:** Entry point aplikasi. Membaca parameter startup, memilih Hosting Adapter, membuat Runtime Coordinator, memulai Coordinator.

**Interface:**
```python
class Launcher:
    async def run()
    async def install_service()
    async def uninstall_service()
    async def restart()
```

### 2.2 Runtime Coordinator
**Responsibility:** Pusat pengendali lifecycle. Mengelola state startup, shutdown, recovery, health, state transition.

**State yang Dikelola:**
INITIALIZING → BOOTSTRAPPING → RECOVERING → READY → RUNNING → DEGRADED → PAUSED → STOPPING → SHUTDOWN → CRASHED → SAFE_MODE → UPDATING

**Interface:**
```python
class RuntimeCoordinator:
    async def start()
    async def stop()
    async def recover()
    async def pause()
    async def resume()
    async def status()
    async def health()
```

### 2.3 Hosting Adapter
**Responsibility:** Mengabstraksikan platform host (Windows, Linux, Docker).

**Interface:**
```python
class HostingAdapter:
    def environment()
    def workspace()
    def register_signal()
    def load_environment()
    def write_log()
    def stop_signal()
```

### 2.4 Bootstrap Manager
**Responsibility:** Menjalankan startup pipeline.

**Pipeline:**
Configuration → Workspace → Database → Migration → Plugin Discovery → Knowledge → Memory → Runtime → Services → Health Check → READY

**Serial:**
Configuration, Workspace, Database, Migration

**Parallel:**
Plugin Discovery, Knowledge, Memory

### 2.5 Session Manager
**Responsibility:** Mengelola persistence Runtime (workspace, runtime state, checkpoint, workflow queue, metadata).

**Interface:**
```python
class SessionManager:
    async def load()
    async def save()
    async def checkpoint()
    async def restore()
```

### 2.6 Shutdown Manager
**Responsibility:** Menutup Runtime secara aman.

**Pipeline:**
Stop Accepting Work → Finish Running Tasks → Persist Session → Flush Telemetry → Shutdown Plugins → Close Database → Exit

**Timeout:** 60 detik default.

### 2.7 Recovery Manager
**Responsibility:** Mengembalikan Runtime ke kondisi operasional.

**Recovery Strategy:**
Detect → Load Session → Restore Checkpoint → Replay Pending Work → Verify → READY

Jika restore gagal: Runtime masuk SAFE_MODE.

---

## Bab 3 — Runtime State Machine

### States

| State | Description |
| :--- | :--- |
| INITIALIZING | Process dibuat |
| BOOTSTRAPPING | Startup pipeline berjalan |
| RECOVERING | Session sedang dipulihkan |
| READY | Runtime siap menerima pekerjaan |
| RUNNING | Runtime aktif |
| DEGRADED | Ada komponen gagal tetapi Runtime tetap hidup |
| PAUSED | Runtime dihentikan sementara |
| UPDATING | Runtime sedang upgrade |
| STOPPING | Shutdown dimulai |
| SHUTDOWN | Runtime berhenti normal |
| CRASHED | Runtime berhenti tidak normal |
| SAFE_MODE | Recovery gagal, hanya capability minimum aktif |

### Diagram Transisi

```
INITIALIZING → BOOTSTRAPPING → RECOVERING → READY → RUNNING
                                      ↓
                                   READY
                                      ↓
                                (crash) → CRASHED → RECOVERING → READY
                                      ↓
                                (recovery fail) → SAFE_MODE
```

### Rules
- Hanya Runtime Coordinator yang boleh mengubah state.
- Setiap perubahan state wajib menghasilkan Lifecycle Event.
- Runtime hanya boleh menerima pekerjaan pada state READY atau RUNNING.
- SAFE_MODE hanya dapat keluar melalui recovery atau restart penuh.

---

## Bab 4 — Lifecycle Events

### Event Schema
```python
class LifecycleEvent:
    event_id: UUID
    event_name: str
    timestamp: datetime
    runtime_state: RuntimeState
    component: str
    severity: Severity
    correlation_id: UUID
    session_id: UUID
    payload: dict
```

### Standard Events
- ApplicationStarting
- ConfigurationLoaded
- WorkspaceReady
- DatabaseReady
- MigrationCompleted
- PluginDiscoveryCompleted
- PluginsLoaded
- KnowledgeLoaded
- MemoryLoaded
- RuntimeReady
- RuntimeStarted
- SessionRestored
- RecoveryStarted
- RecoveryCompleted
- RecoveryFailed
- RuntimeStopping
- RuntimeStopped
- RuntimeCrashed

---

## Bab 5 — Boot Profiles

**Development:**
verbose logging, hot reload, plugin unsigned diperbolehkan, telemetry debug, checkpoint dipercepat.

**Testing:**
deterministic startup, fake provider diperbolehkan, timeout dipersingkat, cleanup otomatis.

**Production:**
semua validasi aktif, plugin tervalidasi, telemetry normal, recovery otomatis, cache aktif, optimasi resource.

**Safe Mode:**
plugin dinonaktifkan, workflow baru ditolak, knowledge read-only, database read-only, hanya Recovery Manager yang aktif.

**Recovery Mode:**
workflow baru ditolak, checkpoint dipulihkan, replay queue dijalankan, plugin hanya dimuat jika lolos validasi.

---

## Bab 6 — Workspace Layout

```
workspace/
├── config/
│   ├── runtime.yaml
│   ├── plugins.yaml
│   └── logging.yaml
├── database/
│   └── sam.db
├── sessions/
├── checkpoints/
├── knowledge/
├── memory/
├── plugins/
├── logs/
├── telemetry/
├── cache/
├── temp/
├── recovery/
└── manifest/
    └── runtime.json
```

---

## Bab 7 — Configuration Hierarchy

1. Runtime Override
2. CLI Override
3. Environment Variable
4. Workspace Configuration
5. Global Configuration
6. Built-in Default

---

## Bab 8 — Failure Classification

| Type | Recovery |
| :--- | :--- |
| Configuration Error | Startup dihentikan |
| Dependency Error | Retry sesuai policy |
| Plugin Error | Plugin diisolasi |
| Runtime Error | Restart komponen |
| Workflow Error | Checkpoint + Replay |
| Infrastructure Error | Safe Mode |

---

## Bab 9 — Plugin Lifecycle

```
DISCOVER → VALIDATE → LOAD → INITIALIZE → START → RUNNING → STOP → UNLOAD
```

**Rules:**
- Plugin tidak boleh melewati tahapan.
- Setiap transisi menghasilkan Lifecycle Event.
- Plugin gagal VALIDATE tidak boleh mencapai LOAD.
- Plugin gagal INITIALIZE harus di-unload otomatis.

---

## Bab 10 — Data Model (Pydantic)

### Mission
```python
class MissionStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    COMPLETED = "completed"

class Objective(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: MissionStatus = MissionStatus.ACTIVE

class Mission(BaseModel):
    id: str
    name: str
    description: str
    objectives: List[Objective]
    priority: int = 1
    min_health: float = 0.8
```

### Desired Operational State (DOS)
```python
class DesiredOperationalState(BaseModel):
    runtime_state: str = "RUNNING"
    plugins_expected: int = 0
    knowledge_loaded: bool = True
    memory_healthy: bool = True
    session_persistent: bool = True
    min_health_score: float = 95.0
    guardian_mode: str = "autonomous"
```

### Runtime State
```python
class RuntimeState(str, Enum):
    INITIALIZING = "initializing"
    BOOTSTRAPPING = "bootstrapping"
    RECOVERING = "recovering"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    PAUSED = "paused"
    UPDATING = "updating"
    STOPPING = "stopping"
    SHUTDOWN = "shutdown"
    CRASHED = "crashed"
    SAFE_MODE = "safe_mode"
```

### Guardian Decision
```python
class GuardianDecision(BaseModel):
    decision_id: str
    event_id: str
    mission_id: str
    severity: str
    risk: str
    action_plan: str
    approved: bool
    executed: bool
    verified: bool
    duration_ms: int
```

### Health Status
```python
class HealthStatus(BaseModel):
    overall: str  # HEALTHY, DEGRADED, UNHEALTHY
    components: Dict[str, str]
    score: float  # 0–100
    last_check: datetime
```

### Session
```python
class Session(BaseModel):
    id: str
    workspace: str
    started_at: datetime
    last_activity: datetime
    state: str
    checkpoints: List[Dict]
```

---

## Bab 11 — Interface & API (Python Protocol)

### Runtime Coordinator
```python
class RuntimeCoordinator(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def recover(self) -> None: ...
    async def pause(self) -> None: ...
    async def resume(self) -> None: ...
    async def status(self) -> RuntimeState: ...
    async def health(self) -> HealthStatus: ...
```

### Bootstrap Manager
```python
class BootstrapManager(Protocol):
    async def bootstrap(self) -> bool: ...
    async def rollback(self) -> None: ...
    async def verify(self) -> bool: ...
```

### Session Manager
```python
class SessionManager(Protocol):
    async def load(self) -> Session: ...
    async def save(self, session: Session) -> None: ...
    async def checkpoint(self, checkpoint: Dict) -> None: ...
    async def restore(self, checkpoint_id: str) -> bool: ...
```

### Shutdown Manager
```python
class ShutdownManager(Protocol):
    async def shutdown(self) -> bool: ...
    async def force_shutdown(self) -> None: ...
```

### Recovery Manager
```python
class RecoveryManager(Protocol):
    async def detect(self) -> bool: ...
    async def restore(self) -> bool: ...
    async def replay(self) -> bool: ...
    async def verify(self) -> bool: ...
```

### Hosting Adapter
```python
class HostingAdapter(Protocol):
    def get_workspace(self) -> str: ...
    def get_environment(self) -> Dict: ...
    def register_signal(self, handler) -> None: ...
    def load_environment(self) -> Dict: ...
    def write_log(self, message: str) -> None: ...
    def stop_signal(self) -> None: ...
```

### HTTP Health Endpoints (untuk Phase 2)
- `GET /health` — liveness
- `GET /ready` — readiness
- `GET /runtime` — status lengkap

---

## Bab 12 — Startup & Recovery Contract

### Startup Contract
- Bootstrap Stage → Health Verification → READY → baru boleh menerima pekerjaan.
- Tidak ada Workflow yang berjalan sebelum READY.
- Setiap tahap bootstrap memiliki timeout 30 detik.
- Jika timeout tercapai, masuk SAFE_MODE.

### Recovery Contract
- Recovery → Validation → Replay → Verification → READY.
- Jika recovery gagal, masuk SAFE_MODE.
- Checkpoint dianggap valid jika memiliki session_id, timestamp, dan payload.
- Replay tidak boleh dijalankan lebih dari 3 kali berturut-turut.

---

## Bab 13 — Flow Diagrams (ASCII)

### Startup Flow
```
Launcher → Coordinator → Bootstrap Manager
    ↓
Configuration → Workspace → Database → Migration
    ↓ (parallel)
Plugin Discovery → Knowledge → Memory
    ↓
Runtime → Services → Health Check
    ↓
READY
```

### Shutdown Flow
```
SIGTERM → Coordinator → Shutdown Manager
    ↓
Stop Accepting Work → Finish Tasks → Persist Session
    ↓
Flush Telemetry → Shutdown Plugins → Close Database
    ↓
SHUTDOWN
```

### Recovery Flow
```
Crash → Coordinator → Recovery Manager
    ↓
Detect → Load Session → Restore Checkpoint → Replay → Verify
    ↓
READY (success) / SAFE_MODE (failure)
```

### Session Restore
```
Startup → Session Manager
    ↓
Load session from workspace/sessions/
    ↓
Restore state → Restore checkpoints
    ↓
Continue
```

### Plugin Loading
```
Discovery → Validation → Load → Initialize → Start → Running
```

---

## Bab 14 — Safe Mode

### Entry Conditions
- Recovery gagal
- Workspace corrupt
- Database tidak dapat dipulihkan
- Required Runtime gagal start
- Konfigurasi tidak valid

### Active Components
- Runtime Coordinator
- Recovery Manager
- Session Manager
- Shutdown Manager
- Hosting Adapter
- Telemetry Runtime
- Monitoring Runtime

### Disabled Components
- Workflow Runtime
- Scheduler
- Job Queue
- Autonomy Runtime
- Federation Runtime
- Plugin Runtime (non-essential)

### Read-Only Components
- Knowledge Runtime (READ ONLY)
- Memory Runtime (READ ONLY)
- Workspace (READ ONLY)
- Configuration (READ ONLY)

### Exit Conditions
- Recovery berhasil
- Health Verification berhasil
- Required Runtime aktif
- Session valid

---

## Bab 15 — Compatibility Layer

### Domains
- Workspace
- Session
- Runtime Manifest
- Checkpoint
- Recovery Point
- Plugin API
- Configuration
- Database Schema

### Semantic Versioning
- MAJOR: Breaking
- MINOR: Backward Compatible
- PATCH: Bug Fix

### Upgrade Contract
Backup → Verify Compatibility → Migration → Validation → Health Verification → Commit → READY

Rollback jika salah satu tahap gagal.

---

## Bab 16 — Runtime Manifest

### File
`workspace/manifest/runtime.json`

### Schema
```json
{
  "runtime_version": "1.1.0",
  "workspace": "default",
  "hosting": "docker",
  "mode": "RUNNING",
  "boot_profile": "production",
  "session_id": "...",
  "plugin_count": 14,
  "knowledge": "READY",
  "memory": "READY",
  "health": "HEALTHY",
  "uptime": 3600,
  "generated_at": "2026-07-27T10:00:00Z"
}
```

### Rules
- JSON valid, UTF-8, overwrite atomically.
- Tidak menyimpan data sensitif.

---

## Bab 17 — Implementation Plan (Phase 0)

| Task | Estimasi | Dependency | Output |
| :--- | :--- | :--- | :--- |
| Runtime Coordinator | 3 hari | - | `src/sam/runtime/coordinator.py` |
| Bootstrap Manager | 3 hari | Coordinator | `src/sam/runtime/bootstrap.py` |
| Session Manager | 2 hari | Bootstrap | `src/sam/runtime/session.py` |
| Shutdown Manager | 2 hari | Coordinator | `src/sam/runtime/shutdown.py` |
| Recovery Manager | 3 hari | Session | `src/sam/runtime/recovery.py` |
| Hosting Adapter | 3 hari | Coordinator | `src/sam/hosting/` |
| Runtime Manifest | 1 hari | Session | `src/sam/runtime/manifest.py` |
| Integration Tests | 3 hari | Semua | `tests/integration/` |

**Total:** ~25 hari kerja

---

## Bab 18 — Hosting Models

| Model | Startup | Shutdown | Persistence | Logging | Recovery |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Desktop | Double-click | Graceful | Workspace | Local | Auto |
| Windows Service | Auto-start | Service Stop | Workspace | Event Log | Auto |
| systemd | systemctl | SIGTERM | Workspace | journald | Auto |
| Docker | docker run | SIGTERM | Volume | STDOUT | Auto |
| Kubernetes | Pod | SIGTERM | PVC | Container | Auto |
| Embedded | API call | API | Host | Host | Host |

---

## Bab 19 — Technical Decisions

### TD-001 Launcher
**Decision:** Hybrid Hosting Model (Desktop, Windows Service, systemd, Docker).
**Reason:** Satu kode untuk empat model hosting.

### TD-002 Linux Hosting
**Decision:** systemd.
**Reason:** native Linux, dependency kecil, restart policy, journal integration.

### TD-003 Docker
**Decision:** Docker sebagai deployment resmi Phase 0.
**Deliverables:** Dockerfile, docker-compose.yml.

### TD-004 OpenClaw Discovery
**Decision:** Pendekatan bertingkat: Explicit Configuration → Workspace Scan → Known Location → Plugin Discovery. Registry Windows tidak digunakan.

### TD-005 Crash Recovery
**Decision:** Recovery dari Checkpoint terakhir: Session → Snapshot → Checkpoint → Replay → Verify → READY. Jika Replay gagal: SAFE_MODE.

### TD-006 Tray Application
**Decision:** TIDAK termasuk Phase 0. Akan masuk Phase 1.

### TD-007 Health Endpoint
**Decision:** HTTP Health Endpoint tersedia di 127.0.0.1:8080. Endpoint: /health, /ready, /runtime. Authentication: Local Only (Phase 0).

### TD-008 Docker Volume
**Decision:** Workspace di /opt/sam/workspace. Volume wajib dipasang.

### TD-009 Signal Handling
**Decision:** Hosting Adapter menerjemahkan semua sinyal (Windows Service Stop, SIGTERM) menjadi Graceful Shutdown Request.

### TD-010 Runtime Manifest
**Decision:** Runtime Manifest diperbarui saat Startup, Recovery, Shutdown, Safe Mode, dan setiap perubahan state.

---

## Appendix — ADR 015–020

### ADR-015 — Hosting Independence
**Decision:** Runtime Core tidak mengetahui platform hosting.
**Reason:** Portabilitas.
**Consequence:** Hosting Adapter wajib ada.
**Rejected:** Platform-specific Runtime.

### ADR-016 — Headless Runtime
**Decision:** Runtime berjalan tanpa GUI.
**Reason:** Desktop, Service, Docker menggunakan Runtime yang sama.
**Rejected:** GUI sebagai bagian Runtime.

### ADR-017 — Runtime State Machine
**Decision:** Runtime menggunakan satu State Machine global.
**Reason:** Lifecycle deterministik.
**Rejected:** State machine per modul.

### ADR-018 — Workspace Layout
**Decision:** Workspace menjadi root seluruh persistence.
**Reason:** Portabilitas, backup sederhana.
**Rejected:** Data tersebar di berbagai lokasi.

### ADR-019 — Recovery Contract
**Decision:** Recovery menggunakan Session → Snapshot → Checkpoint → Replay.
**Reason:** Meminimalkan kehilangan pekerjaan.
**Rejected:** Recovery hanya dari Session.

### ADR-020 — Lifecycle Events
**Decision:** Seluruh perubahan Runtime menghasilkan Lifecycle Event.
**Reason:** Auditability, Observability, Telemetry.
**Rejected:** Logging tanpa event terstruktur.
