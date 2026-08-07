# Journal — Program G (Execution Evolution): Simulation Capability (2026-08-07)

## Tujuan
Membangun **Simulation Capability** di `execution_runtime` sesuai keputusan arsitektur
(2026-08-07): Simulation menjadi **capability dari Execution Runtime** (bukan Runtime
terpisah), menghasilkan evidence deterministik dari metadata governance untuk memperkaya
keputusan Approval — dengan kata kunci "Govern Capability, Never Implementation".

Sasaran V1 (batas dari keputusan arsitektur):
- `SimulationEvidence` — dataclass evidence deterministik dari metadata governance.
- `SimulationEngine` — menghasilkan evidence **tanpa mock engine**, murni perhitungan dari
  artefak governance yang sudah ada.
- Mode `"simulation"` valid di `ExecutionRequest`.
- Wiring ke pipeline/Approval sebagai evidence **OPTIONAL** (kontrak `ApprovalGate`/ADR-001
  tidak berubah).
- Preview & Dry Run where `external_calls = 0`.

Validation & Real Execution sengaja **di luar scope** (program terpisah berikutnya).

## Landasan keputusan
- **Simulation = capability Execution Runtime** (bukan Runtime konstitusional baru).
- **Pipeline konseptual:** Mission → Workflow → Policy → Simulation → Approval → Execution →
  Verification → Audit. Simulation menyediakan evidence (cost, time, risk, expected provider,
  rollback feasibility, side effects, external calls) sehingga Approval = Decision + Evidence.
- **Evidence = deterministik/metadata-based** (dari Mission/Workflow/Capability/Registry/
  Contract/Approval Context/Execution Plan/Provider Metadata), BUKAN mock execution engine.
  Mock/emulator adalah evolusi masa depan (V2 contract semantic, V3 provider emulator,
  V4 sandbox) — di luar V1.
- **ApprovalGate kontrak tidak diubah** — evidence = input opsional yang memperkaya
  decision/explainability/audit, bukan keharusan.

## Kerja
### File baru (`src/sam/execution_runtime/`)
1. **`simulation_evidence.py`** → `SimulationEvidence` (frozen dataclass):
   - Identitas: `simulation_id`, `execution_id`, `provider_id`, `operation`.
   - Governance ter-resolve: `capability_resolved`, `provider_selected`, `approval_required`.
   - Estimasi deterministik (dari metadata, bukan eksekusi): `estimated_external_calls`,
     `estimated_cost`, `estimated_risk`, `estimated_duration_ms`.
   - Analisis konsekuensi: `rollback_possible`, `side_effects`, `expected_artifact`,
     `expected_audit_chain`.
   - `confidence`, `evidence_source` (transparansi/auditability).
   - Method `as_dict()`.
2. **`simulation_engine.py`** → `SimulationReport` (frozen, menggabung `SimulationEvidence` +
   `summary`) dan `SimulationEngine`:
   - `_PROVIDER_PROFILE` — tabel estimasi deterministik per kategori provider (filesystem,
     shell, sqlite, docker, openclaw, openai, anthropic, gemini, deepseek, ollama) + fallback.
   - `__init__(selector, dispatcher)` — composition, default `ProviderSelector()` +
     `ProviderDispatcher()` (sumber metadata provider — dispatch mengembalikan
     `DispatchTarget` immutable: provider_id, operation, mode, available, external_calls=0).
   - `simulate(request)` → `SimulationEvidence` — TIDAK memanggil provider, TIDAK external
     call, TANPA mock engine. Perhitungan deterministik: `approval_required` (mode
     execute/simulation), `est_duration` (bounded ke timeout), `est_cost` (external only),
     `confidence` (base + external + approval, cap 1.0), `side_effects`, `expected_artifact`
     (`{operation}://{provider_id}`), `expected_audit_chain` (7 tahap), `evidence_source`.
   - `run(request)` → `SimulationReport` (evidence + summary string).
3. **`simulation_integration.py`** → `SimulatedExecutionReport` (frozen) dan
   `SimulationIntegration`:
   - `preview(request)` — mode PREVIEW: simulasi, `external_calls=0`, tanpa approval.
   - `dry_run(request)` — pipeline berjalan penuh TAPI `external_calls=0`
     (`approval_applied=request.approved`).
   - `evidence_for_approval(request)` → `SimulationEvidence` (evidence opsional untuk Approval).
   - `_with_mode(request, mode)` — salin request immutable dengan mode berbeda.

### File dimodifikasi
- **`execution_request.py`** — mode valid jadi `preview|simulation|execute|rollback`;
  default tetap `"preview"`; validasi `ValueError` untuk mode tak dikenal.
- **`execution_metadata.py`** — comment mode + izinkan `simulation`.
- **`__init__.py`** — export `SimulationEvidence`, `SimulationEngine`, `SimulationReport`,
  `SimulationIntegration`, `SimulatedExecutionReport`.

### Dokumen repo
- **`ROADMAP.md`** — tambah "Program G (Execution Evolution)" di bagian Roadmap Produk
  (post-1.0): G.1 Simulation Capability, G.2 Preview & Dry Run + wiring, G.3 Validation
  (program berikutnya). Diberi catatan bahwa ini BEDA dari "Program G – Conversation as
  Presentation Capability" (0.30, sudah selesai).

## Hasil (verifikasi)
- **Test baru:** `tests/execution_runtime/test_program_g_simulation.py` — 14 test:
  - SimulationEvidence frozen + `as_dict()` lengkap.
  - SimulationEngine deterministik (same input → same output).
  - No external call dalam simulasi (provider local → `estimated_external_calls=0`).
  - External provider di-flag (`estimated_external_calls=1`, cost > 0, side_effect
    `external_call`).
  - Rollback + audit chain (7 tahap).
  - Confidence & risk bounded 0.0–1.0 untuk semua KNOWN_PROVIDERS.
  - `run()` → SimulationReport dengan summary.
  - Mode `simulation` valid; mode invalid → `ValueError`.
  - Preview: `external_calls=0`, tanpa approval.
  - Dry run: `external_calls=0`, `approval_applied` sesuai request.
  - Approval tetap berjalan tanpa evidence (kontrak tidak berubah) + evidence bisa
    di-attach sebagai input opsional.
  - **Semua 14 PASS.**
- **Regression:** `tests/execution_runtime/` = **209 passed** (termasuk 14 baru).
  - 2 kegagalan di `test_sprint260.py` = **pre-existing** (diverifikasi: gagal identik di
    HEAD bersih via `git stash`). Akar: `providers/execution/provider_executor.py` butuh
    `base_url` untuk eksekusi LLM — di luar scope Program G.
- **Kualitas:** 0 karakter non-ASCII di 7 file yang tersentuh; semua class bisa di-import;
  demo `SimulationIntegration().preview()` berjalan (provider=openai → cost 0.02, risk 0.45,
  rollback yes, actual external_calls 0).

## Catatan teknis
- **Konsep penting:** `estimated_external_calls` = estimasi DARI METADATA (boleh 1 utk provider
  eksternal seperti openai), BUKAN call nyata. Report-level `external_calls` = 0 untuk SEMUA
  mode simulation/preview/dry-run — artinya tidak benar-benar memanggil provider.
- Ada satu test awal yang keliru mendesain: meng-assert `estimated_external_calls==0` di mode
  preview untuk provider openai — salah karena itu estimasi metadata (benar 1), bukan call
  nyata. Test diperbaiki ke konsep yang benar (assert report-level `external_calls==0`).
- SimulationEngine memakai composition (`selector`/`dispatcher`), bukan inheritance; `dispatcher`
  (sumber metadata provider) tidak memiliki logic provider-spesifik / tidak ada network — paling
  cocok sebagai sumber `provider_selected` + `external_calls=0` untuk evidence.

## Blocker
Tidak ada.

## Handoff
- **Belum di-commit / di-push** — perubahan ada di working tree; menunggu konfirmasi Van
  (+ checklist push sebelum push).
- Update `ROADMAP.md` menyangkut dokumen resmi repo (keputusan arsitektur) — sudah ditambahkan
  per permintaan Van; tetap butuh konfirmasi sebelum commit bersama.
- Program berikutnya: **Validation** (G.3) dan **Real Execution** (Program H) — terpisah,
  menunggu go Aster.
