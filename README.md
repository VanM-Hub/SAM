# SAM Framework

**Self-evolving AI Operations Framework**

SAM (Self-evolving AI Manager) adalah framework untuk mengelola, memonitor, dan mengoperasikan runtime AI secara otonom. Dari runtime kernel hingga web dashboard dan desktop console — SAM menangani seluruh siklus operasi.

## Fitur v3.0

| Fitur | Deskripsi |
|---|---|
| **Telemetry Foundation** | Event Taxonomy (36 types), Ring Buffer (1000 events), SQLite cache, JSON Schema |
| **Operations Engine** | Context, Status, Task, Knowledge, History, Settings, Explainability engines |
| **Desktop Console** | 8 halaman: Home, Task, Timeline, Knowledge, History, Settings, Explainability |
| **CLI** | 22+ commands, termasuk task, history, settings, knowledge, explain |
| **Runtime Kernel** | State machine (12 state), bootstrap, session, shutdown, recovery |
| **Guardian Kernel** | Observe-Analyze-Decide-Act-Verify (GDP) pipeline |
| **Service Layer** | Windows Service, systemd, Docker, Desktop Launcher |
| **Observability** | Telemetry events, metrics collector, FastAPI REST API |
| **Operational Intelligence** | Incident detection, root cause analysis, recommendations |
| **Autonomous Operations** | Auto restart, recovery, resume, isolate, escalate, human approval |
| **Explainability** | Template-based explanations with evidence, impact, recommendations |

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

209 tests, 0 regressions.

## Arsitektur

```
Runtime -> Telemetry -> Operations Engine -> Experience Model -> Desktop/CLI
                                                          |
                                                     (Human Language)
```

Dokumentasi arsitektur: `docs/architecture/`

## Kontribusi

Baca [CONTRIBUTING.md](CONTRIBUTING.md) sebelum memulai.

## Lisensi

MIT — lihat file LICENSE.
