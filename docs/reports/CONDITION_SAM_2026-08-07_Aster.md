# Ringkasan Kondisi Repo SAM — untuk Rencana Roadmap Selanjutnya

_Tanggal rangkuman: 2026-08-07_
_Pembuat: Engineer (untuk diteruskan ke Chief Architect / Aster)_

---

## 1. Identitas & Versioning

| Item | Nilai |
|---|---|
| Nama proyek | **SAM** (System for Adaptive Mission) |
| Branch aktif | `main` |
| Remote | `https://github.com/VanM-Hub/SAM.git` |
| Versi teknis (`pyproject.toml`) | `1.0.0` |
| `sam.__version__` | `1.0.0` |
| Tag rilis | `v1.0.0` (menunjuk commit `7842765`) |

> Catatan versioning: Repo kini diposisikan sebagai **republik bersih / rilis pertama**.
> Seluruh tag internal lama (skema 0.01–0.30, hingga v30.0.0) telah dihapus dari repo karena
> dianggap sebagai tahap pengembangan fondasi, bukan rilis publik. Hanya `v1.0.0` yang tersisa.

## 2. Kontrol Versi — Riwayat Terakhir

Commit terakhir (HEAD = `7842765`):

```
7842765 docs: bersihkan referensi buntu INDEX journal (jurnal yang sudah dihapus)
0881c09 docs: samakan penamaan Simulation & Preview (bagian dari Program C); hapus jurnal engineering usang
f736109 feat(execution-runtime): Program G Simulation Capability (V1)
2a88959 fix(desktop): selaraskan versi host desktop (1.0.0) via sam.__version__
3d65d38 fix(console): selaraskan versi SAM Console (v1.0.0) via sam.__version__
```

## 3. Status Pekerjaan (Uncommitted / Catatan)

- **ROADMAP.md** memiliki **perubahan lokal yang BELUM di-commit** (penyesuaian narasi Fase
  Fondasi). Keputusan masih ditahan — belum disepakati final.
- **Pertanyaan terbuka untuk roadmap selanjutnya** menunggu arahan.

## 4. Posisi Rilis & Arah Roadmap Saat Ini

- **SAM 1.0 (1.0.0)** adalah **rilis publik pertama** — Foundation stabil pertama.
- Keseluruhan fase pengembangan fondasi (0.01 → 0.30, 279 sprint + Program A–K) diposisikan
  sebagai **pre-1.0 / fondasi**, bukan riwayat rilis.
- Arah post-1.0 (per naskah saat ini di ROADMAP): menuju **SAM 2.0 (skalabilitas)** dan
  **ekosistem** — **belum final**, menunggu rencana baru.

## 5. Kemampuan yang Sudah Dirilis (SAM 1.0)

- **Conversation** sebagai Presentation Capability (read-only bridge, preview-first).
- **Dashboard** — konsol operasional (Mission, Workflow, Execution, Approval, Audit, Connector, Provider, Runtime, Health, Telemetry).
- **CLI** — 11 perintah resmi (mission, workflow, policy, audit, artifact, connector, provider, execution, preview, dashboard).
- **REST API** — via `runtime_service.api` (missions, workflow, approval, execution-preview, audit, artifact, policy).
- **LLM Runtime Activation** — 5 provider (OpenAI, Anthropic, Gemini, DeepSeek, Ollama) via Connector → Provider → Agent.
- Arsitektur deterministik: preview-first, approval mandatory sebelum execute, eksekusi cancellable, rollback metadata, full audit, DTO immutable, kredensial hanya dari environment.

## 6. Catatan Arsitektural Penting

- **Program C (Real Execution Runtime)** adalah fondasi eksekusi; **Simulation & Preview**
  resmi menjadi **bagian dari Program C** (menambahkan lapisan Simulation antara Policy dan
  Approval → approval gate menjadi Decision + Evidence, bukan "buta").
- **ARC-001 (Simulation)** — terimplementasi (SimulationEngine, SimulationEvidence, wiring, uji).
- **ARC-002 (Real Execution)** — masih terbuka: `execute(provider)` belum dibuka; pipeline masih
  preview-first / deterministik; menunggu Simulation matang + arahan.

---

## Permintaan ke Aster

Menunggu **rencana Roadmap selanjutnya** dengan mempertimbangkan:
1. Penguatan **SAM 2.0 (Development)** dan **SAM 3.0 (Product)** sebagai tahapan pasca-1.0.
2. Status **ARC-002 (Real Execution)** sebagai open item utama yang perlu arah.
3. Sinkronisasi **ROADMAP.md** (termasuk perubahan lokal yang masih ditahan) agar mengikuti
   keputusan final.
