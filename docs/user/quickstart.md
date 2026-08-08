# Quick Start SAM

> Jalur cepat end-to-end untuk early adopter: **install -> verifikasi -> contoh
> pertama**. Menutup gap E4-G1 (Quick Start end-to-end di README) - WP-E2.3,
> Program E (MISSION-2E / EA-002).

Panduan ini untuk siapa saja yang baru mengenal SAM dan ingin segera mencoba.
Tidak perlu memahami arsitektur internal dahulu. Ikuti dari awal sampai akhir
(+/- 10 menit).

---

## 0. Prasyarat

| Kebutuhan | Minimal |
|---|---|
| Python | 3.8+ (disarankan 3.12) |
| pip | terbaru |
| Git | untuk clone |
| OS | Windows / Linux / macOS |

Cek Python terpasang:

```bash
python --version
```

---

## 1. Install

Clone repository lalu masuki folder:

```bash
git clone https://github.com/VanM-Hub/SAM.git
cd SAM
```

**Cara A - One-command bootstrap (disarankan):**

SAM menyediakan perintah bootstrap otomatis (WP-E2.1) yang menyiapkan
virtual environment + instalasi package sekaligus:

```bash
# Cek rencana instalasi (dry-run, tidak mengubah apa pun)
python -m sam.cli.main onboarding init

# Jalankan instalasi sungguhan (membuat venv + install editable)
python -m sam.cli.main onboarding init --apply
```

> `onboarding init --apply` membaca kebutuhan dependency, membuat
> `venv`, dan memasang package SAM beserta extra yang diminta. Aman
> diulang (idempotent).

**Cara B - Manual (kontrol penuh):**

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -e .
# Tambahan yang umum:
pip install -e ".[console]"   # CLI onboarding & health
```

> Di README root, perintah untuk menjalankan SAM langsung tersedia
> (mis. `SAM_Run.bat` di Windows, atau `sam` bila package terpasang).

---

## 2. Verifikasi Instalasi (dari CLI)

Setelah install, pastikan semuanya sehat lewat command onboarding (WP-E2.2):

```bash
# 1. Versi terpasang
python -m sam.cli.main onboarding version
#   -> SAM v1.0.0

# 2. Diagnosa kesehatan instalasi & environment
python -m sam.cli.main onboarding doctor
#   -> SAM Doctor v1.0.0; menampilkan status dependency & environment

# 3. (Opsional) rencana inisialisasi project
python -m sam.cli.main onboarding init
```

- `version` : menampilkan versi package (tidak pernah error, robust lintas env).
- `doctor` : memeriksa dependency (python/pip/setuptools/wheel/SAM) dan
  environment (venv, struktur repo, PYTHONPATH, writable). Read-only.
  Ikuti pesan perbaikan bila ada `!` di bagian `issues`.
- `init` : menampilkan rencana install + langkah berikutnya. Non-destruktif.

> Jika `doctor` melaporkan masalah, perbaiki sesuai pesan lalu ulangi
> `onboarding doctor` sampai bersih. `onboarding init --apply` akan
> menyelesaikan sebagian besar penyiapan otomatis.

---

## 3. Menjalankan SAM

SAM menyediakan beberapa cara menjalankan (detail di `docs/user/cli_reference.md`
dan `docs/user/capability_guide.md`):

```bash
# CLI operasional (butuh extra console)
python -m sam.cli.main health

# Launcher host (tidak butuh extra tambahan)
python -m sam.launcher.cli_entry --version
python -m sam.launcher.cli_entry health

# Di Windows, shortcut sudah tersedia di root repo:
#   SAM_Run.bat  -> jalankan SAM
#   SAM_CLI.bat  -> konsol operasional
#   SAM_Ops.bat  -> dashboard operasional
```

---

## 4. Contoh Pertama

SAM berjalan di atas **mission/workflow** (lihat `docs/user/workflow_guide.md`).
Contoh paling sederhana: cek status sistem.

```bash
# Status agregat sistem (bila environment lengkap)
python -m sam.cli.main status
python -m sam.cli.main health
```

Untuk eksplorasi lebih dalam, lihat:

| Topik | Panduan |
|---|---|
| Konsep dasar & capability | `docs/user/capability_guide.md` |
| Workflow | `docs/user/workflow_guide.md` |
| CLI lengkap | `docs/user/cli_reference.md` |
| REST API | `docs/user/rest_api_guide.md` |
| Integrasi LLM | `docs/user/llm_integration_guide.md` |
| Pemecahan masalah | `docs/user/troubleshooting.md` |

---

## Ringkasan Alur

```
install  ->  verify (version, doctor)  ->  run (health/status)  ->  explore (guides)
```

Selamat mencoba SAM! 
