# WP-B2 — Architecture Issue Report: Mission Runtime Activation Path

**Program:** MISSION-2B / Program B (Runtime Realization) **Work Package:** WP-B2 (Governance: Policy / Workflow / Mission)
**Artifact:** Architecture Issue Report **Tanggal:** 2026-08-08
**Oleh:** ZARA (Lead Implementation Engineer) **Tujuan:** verifikasi wajib — permintaan keputusan Software Architect

> Sesuai Mission Operational Directive & prinsip *Verification over Assumption* (Verdict Van, 2026-08-08):
> *"Sebelum membuat source code baru (mission_preview.py), Engineering harus menjawab satu pertanyaan berbasis
> evidence: Apakah RuntimeService saat ini memang belum memiliki activation path resmi menuju Mission Runtime,
> atau activation path tersebut sudah ada melalui mekanisme lain yang belum teridentifikasi? Jika memang tidak ada
> activation path sama sekali, barulah Engineering menyusun Architecture Issue Report dengan evidence lengkap."*

---

## 1. Pertanyaan yang Dijawab

**Apakah `sam.mission_runtime` memiliki activation path resmi menuju RuntimeService / jalur eksekusi, selain
`mission_preview.py` yang sudah diketahui tidak ada?**

**Jawaban (berbasis evidence): TIDAK ADA.** Verifikasi read-only deterministik di seluruh `src/` menemukan **0 jalur
eksekusi aktual** menuju `sam.mission_runtime`. Detail di bawah.

---

## 2. Evidence Deterministik (diamankan, read-only — tanpa perubahan source)

### 2.1 Inventaris file preview di `runtime_service/api/`

| Runtime | File preview consumer | Runnable |
|---|---|---|
| Memory | `memory_preview.py` | ✅ |
| Knowledge | `knowledge_preview.py` | ✅ |
| Policy | `policy_preview.py` | ✅ |
| Workflow | `workflow_preview.py` | ✅ |
| Artifact | `artifact_preview.py` | ✅ |
| Audit | `audit_preview.py` | ✅ |
| **Mission** | **`mission_preview.py` — TIDAK ADA** | ❌ |

6 dari 7 runtime governance/foundation punya preview consumer di `runtime_service/api/`. **Mission adalah satu-satunya
yang tidak** di antara runtime yang di-assess dalam WP-B2.

### 2.2 Seluruh import `sam.mission_runtime` di source non-mission

Pencarian `from sam.mission_runtime` / `import mission_runtime` / `sam.mission_runtime` di **seluruh `src/`** di luar
folder `mission_runtime/` sendiri:

```
<kosong> — 0 hasil
```

Hasil per-dir besar tambahan (semua **kosong**): `runtime_service/`, `web/`, `api/`, `launcher/`, `runtime/`,
`runtime_root/`, `presentation/`, `cli/`, `operations/`.

→ **`mission_runtime` tidak di-import oleh komponen source manapun.**

### 2.3 Referensi "Mission" di runtime_service = label kontraktual, bukan eksekusi

| Lokasi | Bentuk referensi | Sifat |
|---|---|---|
| `runtime_service/runtime_pipeline.py` `PIPELINE_STAGES` | `"Mission"` sebagai nama tahap | Stage kontraktual; `run()` hanya membuat `PipelineStageResult(stage=s)` — **tidak mengeksekusi** |
| `runtime_service/dashboard_runtime_service.py:34` | `views = ("mission", ...)` | Label dashboard view |
| `presentation/integration/presentation_integ_manifest.py:15` | `"mission_runtime"` | String label manifest |

`RuntimePipeline.run()` (diverifikasi): hanya menghasilkan `PipelineStageResult` per nama stage, tanpa instansiasi
runtime apapun → **bukan activation path**.

### 2.4 Referensi "mission" lain di source = agent/legacy, bukan Mission Runtime

| Lokasi | Merujuk | Bukan |
|---|---|---|
| `cli/health.py`, `cli/status.py` | `sam.mission.loader.MissionLoader`, `sam.dos.loader` | **legacy `sam.mission`**, bukan `sam.mission_runtime` |
| `api/llm_wiring.py` (mission_agent) | `AgentRuntime` untuk "LLM Mission Contract" | agent, bukan Mission Runtime |

---

## 3. Analisis (Temuan berbasis bukti)

| # | Temuan | Severity | Detail |
|---|---|---|---|
| T1 | **`mission_runtime` tidak terhubung ke jalur eksekusi manapun** | High | 0 import di seluruh `src/` non-mission; tidak ada preview consumer |
| T2 | **Tidak ada `mission_preview.py`** | High | 6 runtime lain punya; Mission tidak — absen dari pola preview operational |
| T3 | **"Mission" di pipeline hanya label kontraktual** | Medium | `RuntimePipeline.run()` tidak mengeksekusi stage; bukan jalur aktual |
| T4 | **Jalur CLI yang menyebut Mission memakai runtime legacy** | Medium | `sam.mission` (lama), bukan `sam.mission_runtime` — divergensi dua implementasi mission |
| T5 | **Mission belum bisa dinyatakan Operational** | High | Sesuai rule arsitektur 2026-08-08: butuh evidence suite di baseline CI **dan** activation path resmi |

**Severity keseluruhan: HIGH.** Capability konstitusional Mission (tahap pertama pipeline) belum dapat direalisasikan
tanpa activation path resmi menuju `mission_runtime`.

---

## 4. Rekomendasi (menunggu keputusan — bukan eksekusi langsung)

Sesuai Verdict (tanpa workaround / tanpa menambah `mission_preview.py` langsung), direkomendasikan agar Software
Architect memutuskan salah satu jalur:

| Opsi | Deskripsi | Catatan |
|---|---|---|
| **A** | Anggap deployment produksi hanya perlu **runtime governance yang sudah punya path** (memory/knowledge/policy/workflow/artifact/audit); Mission didefer hingga prioritas berikutnya | Menghindari penambahan komponen baru; Mission tetap belum Operational |
| **B** | Instruksikan **minimal-implementation `mission_preview.py`** (pola `XxxPreviewConsumer` paralel 6 runtime lain) sebagai Program B work | Membutuhkan keputusan bahwa jalur ini memang merupakan activation path resmi yang sah |
| **C** | Verifikasi lebih lanjut apakah activation path intended via **jalur agent/legacy** (`sam.mission` + `llm_wiring`) cukup untuk menjawab kebutuhan "Mission" — sehingga `mission_runtime` bisa dinyatakan **bukan jalur produksi utama** | Menghindari duplikasi; perlu keputusan SoT Mission runtime |

---

## 5. Status & Dampak

- **Status pekerjaan WP-B2:** Assessment ✅ · Evidence ✅ · Validation ✅ · Implementasi **tertahan** (menunggu keputusan).
- **Tidak ada perubahan source** yang dilakukan pada verifikasi ini (read-only).
- **Baseline CI:** tidak berubah (3022 passed, 1 skipped — test `tests/mission_runtime/` belum di baseline, menunggu
  keputusan perluasan baseline Program A / A2).
- **Architecture drift:** tidak ditemukan (sesuai Verdict) — pertanyaan ini murni verifikasi jalur aktual.

---

*Diterbitkan oleh ZARA (Lead Implementation Engineer) — 2026-08-08. Menunggu keputusan Software Architect.*
