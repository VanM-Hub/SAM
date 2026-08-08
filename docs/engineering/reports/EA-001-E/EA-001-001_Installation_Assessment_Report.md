# EA-001-001 — Installation Assessment Report

**Mission:** MISSION-2E — Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Workstream:** WP-E1 — Installation Experience
**Bersifat:** Assessment (read-only, berbasis evidence) — TIDAK ada perubahan source/repo/CI/docs.

---

## Ruang Lingkup

Menilai pengalaman pemasangan SAM untuk early adopter: struktur instalasi, launcher, dependency, bootstrap, environment, portable installation, Python version, dan first run.

---

## Inventory Evidence

### 1. Struktur instalasi & entry points

`pyproject.toml` mendefinisikan **5 console entry point** (semua menuju `sam.launcher.cli_entry`):

| Entry point | Fungsi |
|---|---|
| `sam` | CLI operasional utama |
| `sam-console` | Konsol operasional |
| `sam-desktop` | Desktop app |
| `sam-headless` | Mode tanpa UI |
| `sam-diagnostic` | Diagnostik runtime |

Build system: `setuptools >= 64` + `wheel`, backend `setuptools.build_meta`.
`requires-python = ">=3.8"` — sesuai kebijakan Python 3.8 repo.

### 2. Launcher portable

Lima launcher `.bat` tersedia untuk penggunaan lokal tanpa instalasi penuh:

| Launcher | Tujuan |
|---|---|
| `SAM_Run.bat` | Jalur standar |
| `SAM_CLI.bat` | CLI operasional |
| `SAM_Desktop.bat` | Desktop app |
| `SAM_Ops.bat` | Konsol operasional |
| `SAM_Web.bat` | Web dashboard |

Ini mendukung **portable installation** (kemampuan H1 Program D): pakai launcher `.bat` langsung tanpa membangun package.

### 3. Bootstrap & environment

- Virtual environment tersedia (`.`venv`) — bootstrap via venv + `pip install -e .` standar.
- Path Python dilengkapi otomatis untuk penggunaan sumber (PYTHONPATH di-set ke `src/`).
- Tidak ada dependency eksternal wajib untuk core; eksekusi nyata (LLM) adalah opsional (integrasi provider).

### 4. First run & dokumentasi pengguna

`docs/user/` menyediakan panduan instalasi & pemakaian end-user:

| Dokumen | Peran |
|---|---|
| `installation.md` | Langkah instalasi |
| `cli_reference.md` | Referensi CLI |
| `capability_guide.md` | Panduan kemampuan |
| `workflow_guide.md` | Panduan workflow |
| `rest_api_guide.md` | REST API |
| `llm_integration_guide.md` | Integrasi LLM/provider |
| `plugin_guide.md` | Plugin |
| `faq.md` | Tanya-jawab |
| `troubleshooting.md` | Pemecahan masalah |

---

## Temuan Gap (Initial Assessment)

| ID | Severity | Temuan | Keterangan |
|---|---|---|---|
| E1-G1 | **High** | Tidak ada skrip bootstrap otomatis (instal one-shot) | Early adopter harus tahu langkah venv+pip+PYTHONPATH manual; tidak ada `make install`/`install.sh`/`bootstrap.py` |
| E1-G2 | Medium | Python 3.8 sebagai min bergantung pada fitur yang tidak ada di 3.8+ untuk beberapa modul | Konsistensi versi runtime vs dokumentasi perlu diverifikasi manual |
| E1-G3 | Low | Launcher `.bat` tersedia tetapi panduan platform non-Windows tipis | Portable `.bat` spesifik Windows; arah cross-platform belum terdokumentasi |

---

## Kesimpulan

Instalasi sudah kuat untuk pengguna mahir: 5 entry point, 5 launcher portable, venv + pip, dokumentasi pengguna lengkap. Gap utama terletak pada **bootstrap otomatis** (early adopter yang ingin "coba cepat") dan catatan cross-platform.
