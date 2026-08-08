# EA-001-002 — CLI Experience Report

**Mission:** MISSION-2E — Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Workstream:** WP-E2 — CLI Experience
**Bersifat:** Assessment (read-only, berbasis evidence)

---

## Ruang Lingkup

Menilai pengalaman CLI untuk early adopter: command discovery, help, error messages, shell usability, interactive mode, autocomplete readiness.

---

## Inventory Evidence

### 1. Command discovery

CLI utama dibangun di atas **Typer** (`src/sam/cli/main.py`), dengan **26 modul command** terdaftar:

`status, health, session, runtime, plugins, knowledge, memory, workflow, events, guardian, service, logs, metrics, openclaw, intelligence, autonomous, history, task, settings, explain, web` — plus modul pendukung (autonomy_app, cluster_app, evolution_app, federation_app, etc.).

Command dikelompokkan via sub-command Typer (`app.add_typer(...)`) sehingga hierarchy alami:
- `sam status`, `sam health`, `sam session`, `sam runtime`, `sam plugins`
- `sam knowledge`, `sam memory`, `sam workflow`, `sam events`, `sam guardian`
- `sam logs`, `sam metrics`, `sam service`
- `sam openclaw`, `sam intelligence`, `sam autonomous`
- `sam history`, `sam task`, `sam settings`, `sam explain`

### 2. Help

Typer otomatis menghasilkan help (`--help`), usage, dan default.

### 3. Interactive mode & autocomplete

Typer menyediakan **shell autocomplete** (bash/zsh/fish/PowerShell) secara bawaan; tidak ditemukan prompt interaktif REPL tersendiri di `src/sam/cli/` (scan tidak menemukan `prompt_toolkit`/`readline`/`completer`). Mode interaktif operasional disediakan oleh layer lain (operations console / desktop), bukan CLI murni.

### 4. Shell usability

Entry points console tersedia global (`sam`, `sam-console`, `sam-desktop`, `sam-headless`, `sam-diagnostic`) via `[project.scripts]` — usable setelah `pip install -e .`.

### 5. Error messages

Typer mengelola error argument; belum terverifikasi whether custom error handling UX (human-readable, suggestion) konsisten di semua command (menunggu penilaian lintas command).

---

## Temuan Gap (Initial Assessment)

| ID | Severity | Temuan | Keterangan |
|---|---|---|---|
| E2-G1 | **High** | Tidak ada command `sam --version` / `sam doctor` / `sam init` untuk onboarding | Discovery cepat (versi, kesehatan instalasi, inisialisasi project) belum tersedia dari CLI inti |
| E2-G2 | Medium | Error message belum terstandar (belum audit UX lintas 26 command) | Konsistensi wording/saran recoverability belum terverifikasi |
| E2-G3 | Low | Tidak ada REPL interaktif di CLI | Autocomplete ada (Typer), tetapi mode interaktif chat belum ada di lapisan CLI |

---

## Kesimpulan

CLI kaya dan terstruktur (26 command, Typer, autocomplete, 5 entry point). Gap utama untuk early adopter: **tidak ada command onboarding** (`--version`/`doctor`/`init`) dan konsistensi pesan error belum auditor secara UX.
