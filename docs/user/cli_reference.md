# CLI Reference

> Semua cara menjalankan SAM dari command line (SAM 1.0, Program G-K).

Project SAM menyediakan **dua jalur CLI**. Pastikan Anda tahu mana yang Anda
gunakan, karena keduanya berbeda:

| Jalur | Entry point | Kebutuhan ekstra | Tujuan |
|---|---|---|---|
| **Launcher CLI** (baru, rekomendasi) | `sam`, `sam-console`, `sam-desktop`, `sam-headless`, `sam-diagnostic` | tidak ada | Menjalankan host SAM via launcher pipeline |
| **Legacy CLI** | `python -m sam.cli.main` | `console` | Perintah operasional klasik (health, run, workflow, dst.) |

---

## 1. Launcher CLI (baru)

Entry points yang terpasang ketika package diinstal:

```bash
sam
sam-console
sam-desktop
sam-headless
sam-diagnostic
```

Juga dapat dijalankan via modul:

```bash
python -m sam.launcher.cli_entry [ARGUMEN]
```

### Argumen launcher

| Argumen | Pilihan | Deskripsi |
|---|---|---|
| `--host` | `auto` (default), `console`, `desktop`, `headless`, `api_server` | Host target |
| `--safe-mode` | `NORMAL` (default), `SAFE`, `READ_ONLY`, `MINIMAL` | Mode startup |
| `--workspace` | path | Folder workspace (default `SAM_WORKSPACE` atau cwd) |
| `--report` | - | Cetak laporan startup |
| `--version` | - | Tampilkan versi launcher |

Contoh:

```bash
# Jalankan dengan host otomatis (deteksi dari SAM_HOST / console)
sam

# Jalankan mode desktop
sam-desktop

# Cek versi launcher
sam --version

# Jalankan console dengan laporan startup
sam --host console --report

# Jalankan headless dalam mode safemode
sam --host headless --safe-mode SAFE
```

`sam-diagnostic` menjalankan pemeriksaan diagnostik lalu keluar:

```bash
sam-diagnostic
# SAM Diagnostics - N checks
#   Passed:   X
#   Failed:   Y
```

> Health launcher tidak perlu ekstra tambahan dan tidak memerlukan database.

---

## 2. Legacy CLI

Jalur klasik yang membutuhkan ekstra `console`:

```bash
python -m sam.cli.main [COMMAND] [ARGS]
# atau jika terinstal sebagai package:
sam [COMMAND] [ARGS]
```

> Catatan: perintah di bawah membutuhkan extra `console` (typer) **dan**
> environment SAM yang lengkap (workspace dengan aset mission / database).

### onboarding (init, doctor, version) — Program E

Command onboarding untuk early adopter (menutup gap E2-G1, WP-E2.2, Program E):

```bash
# Versi package SAM (tidak pernah error, robust lintas environment)
sam onboarding version

# Diagnosa kesehatan instalasi & environment
sam onboarding doctor
sam onboarding doctor --json   # Output JSON

# Rencana inisialisasi project (default dry-run, tidak mengubah filesystem)
sam onboarding init
sam onboarding init --path <project_root>
sam onboarding init --apply   # jalankan bootstrap aplikasi penuh

# Buat starter project SAM baru (WP-E2.4, menutup gap E5-G1)
sam onboarding init --scaffold <nama>          # dry-run: tampilkan rencana file
sam onboarding init --scaffold <nama> --apply   # tulis 8 file ke ./<nama>
sam onboarding init --scaffold <nama> --scaffold-dir <dir> --apply  # target tertentu
```

- `init` default **dry-run**: cek struktur repo + dry-run bootstrap + tampilkan
  next-steps.
- `init --scaffold <nama>` membuat **starter project SAM baru** (struktur lengkap
  Mission + Workflow + Runtime + pyproject + package, 8 file, WP-E2.4/E5-G1).
  Default dry-run non-destruktif; `--apply` menulis file. Idempotent (tidak
  menimpa file yang sudah ada).
- Logika `init` berada di `sam.devx.onboarding`; logika scaffold di
  `sam.devx.scaffold`. Keduanya memakai ulang komponen WP-E2.1 tanpa duplikasi.

### `health`

Menampilkan status kesehatan sistem secara agregat.

```bash
sam health
sam health --json   # Output JSON
```

### `run <capability_id>`

Menjalankan satu capability berdasarkan ID.

```bash
sam run diagnose-runtime
sam run repair-provider
```

### `workflow <steps>`

Menjalankan workflow dengan daftar capability.

```bash
sam workflow "diagnose-runtime,repair-provider,deploy-workspace"
```

### Autonomy Commands

```bash
sam autonomy status
sam autonomy set observe|recommend|assist|supervise|autonomous
sam autonomy history
sam autonomy guardrails
sam autonomy escalate "pesan"
sam autonomy degrade
sam autonomy upgrade
```

### Evolution Commands

```bash
sam evolution list [--status approved|pending]
sam evolution show <proposal_id>
sam evolution approve <proposal_id>
sam evolution reject <proposal_id>
```

### Cluster Commands

```bash
sam cluster status
sam cluster sync
sam cluster strategies-list
sam cluster strategies-vote <proposal_id> --approve
```

### Federation Commands

```bash
sam federation status
sam federation clusters
```

### Graph Commands

```bash
sam graph run examples/monitoring_graph.yaml
```

---

## Cara Menentukan Jalur yang Dipakai

Jika Anda hanya ingin menjalankan SAM (bukan perintah operasional klasik),
gunakan **Launcher CLI**. Jika Anda menjalankan perintah operasional seperti
`autonomy`, `evolution`, `cluster`, gunakan **Legacy CLI** dengan ekstra
`console` dan environment lengkap.
