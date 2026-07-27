# SAM Framework

**Self-evolving AI Operations Framework**

SAM (Self-evolving AI Manager) adalah framework untuk mengelola, memonitor, dan mengoperasikan runtime AI secara otonom. Dari runtime kernel hingga web dashboard — SAM menangani seluruh siklus operasi.

## Fitur v2.0

| Fitur | Deskripsi |
|---|---|
| **Runtime Kernel** | State machine (12 state), bootstrap, session, shutdown, recovery |
| **Guardian Kernel** | Observe-Analyze-Decide-Act-Verify (GDP) pipeline |
| **Hosting** | Desktop, Docker, Windows Service, systemd, Desktop Launcher |
| **Observability** | Telemetry events, metrics collector, FastAPI REST API |
| **OpenClaw Integration** | Discovery, health check, log analysis |
| **Operational Intelligence** | Incident detection, root cause analysis, recommendations |
| **Autonomous Operations** | Auto restart, recovery, resume, isolate, escalate, human approval |
| **Web Dashboard** | 8 halaman: Dashboard, Runtime, Workflow, Incidents, Autonomous, OpenClaw, Knowledge, Settings |
| **CLI** | 17 commands — status, health, session, runtime, guardian, events, logs, metrics, service, openclaw, intelligence, autonomous |

## Quick Start

```bash
# Clone repo
git clone https://github.com/VanM-Hub/SAM.git
cd SAM

# Set PYTHONPATH (PowerShell)
$env:PYTHONPATH = ".\src"
$env:PYTHONIOENCODING = "utf-8"

# Lihat semua CLI commands
python -m sam.cli.main --help

# Lihat status runtime
python -m sam.cli.main status

# Start web dashboard
python -m sam.cli.main web --port 8080
# Buka http://127.0.0.1:8080
```

## CLI Commands (17)

```
status       — Tampilkan status Runtime
health       — Tampilkan status kesehatan
session      — Kelola session runtime
runtime      — Runtime Container Tree
plugins      — Daftar plugin runtime
knowledge    — Knowledge Store
memory       — Memory Store
workflow     — Workflow Engine
events       — Event stream dan history
guardian     — Guardian Kernel
service      — Kelola service runtime
logs         — Telemetry logs (--follow)
metrics      — Runtime metrics (CPU, memory, uptime)
openclaw     — OpenClaw integration (discover, status, monitor)
intelligence — Operational intelligence (incident, rca, recommend)
autonomous   — Autonomous operations (status, approve, deny, history)
web          — Web Dashboard (--host, --port)
```

## Web Dashboard

```bash
sam web --host 127.0.0.1 --port 8080
```

- **Dashboard** — Ringkasan state, health, metrics, incidents, pending actions
- **Runtime** — Detail runtime, hosting, metrics
- **Workflow** — Workflow list dengan progress bars
- **Incidents** — Incident dashboard dengan severity counters
- **Autonomous** — Pending approvals dan action history
- **OpenClaw** — Discovered workspaces dan component health
- **Knowledge** — Knowledge explorer dengan search
- **Settings** — DOS dan Mission YAML (read-only)

## Testing

```powershell
$env:PYTHONPATH = ".\src"
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests/unit/ tests/integration/ -v --tb=short
```

287 tests, 0 regresi.

## Arsitektur

Dokumentasi arsitektur lengkap di `docs/architecture/`:

- `SAM_CONSTITUTION.md` — 10 pasal, hukum tertinggi SAM
- `SAM_ARCHITECTURE_MASTER.md` — 7 layer + Golden Rule
- `runtime-kernel-specification-v1.md` — 19 bab spesifikasi
- `design/operations-console.md` — 11 bab CLI
- `adr/ADR-015-020.md` — 6 ADR terkait

## Lisensi

MIT — lihat file LICENSE.
