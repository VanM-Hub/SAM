# OP-3000 — Presentation Layer (Program F) Complete

**Versi:** v30.0.0 · **Tanggal:** 2026-08-01 · **Status:** Released

> **Catatan revisi:** Program F awalnya direncanakan sebagai "Desktop Runtime" (OP-2900,
> v29.0.0). Sesuai revisi arsitektur, konsep tersebut dihapus dan diganti menjadi
> **Presentation Layer**. v29.0.0 di-*skip*; hasil final dirilis sebagai **v30.0.0**.
> OP-2900 dipertahankan sebagai riwayat rencana awal.

## Ringkasan

Program F menetapkan **Presentation Layer** — UI resmi SAM sebagai lapisan tampilan
(komposisi) yang menghubungkan seluruh subsystem. Murni tampilan, **tanpa business logic,
tanpa engine, tanpa pipeline, tanpa runtime sendiri**; semua operasi menuju RuntimeService.
Sesuai **Presentation Principle** (`docs/CONSTITUTION.md` Article XVI).

## Apa yang Berubah (refactor dari Desktop Runtime)

| Aspek | Sebelum (v29 plan) | Sesudah (v30 final) |
|-------|--------------------|---------------------|
| Folder | `src/sam/desktop_runtime/` | `src/sam/presentation/` |
| Konsep | Runtime | Presentation Layer (bukan runtime) |
| Folder `runtime/` | ada | **dihapus** → `navigation/ commands/ viewmodels/ composition/` |
| Simbol | `DesktopRuntime` dkk. | `PresentationLayer`, `PresentationController`, `PresentationCoordinator`, `PresentationPipeline`, `PresentationSummary` |
| Test | `tests/desktop_runtime/` | `tests/presentation/` |
| Entry point | `sam.desktop_runtime` | `sam.presentation` |

## Struktur Final

```
src/sam/presentation/
├── foundation/       # contract, metadata, descriptor, capability, registry
├── workspace/        # model, layout, state, session, validator, dock_manager
├── panels/           # panel_model, panels_registry (10 panel)
├── dashboard/        # card, composer, layout, snapshot, runtime
├── navigation/       # coordinator (orchestrasi tampilan)
├── commands/         # controller (kirim perintah)
├── viewmodels/       # summary (model tampilan)
├── composition/      # pipeline (komposisi deskriptif)
├── monitoring/       # health, metrics, snapshot, report, monitor
├── certification/    # dimension, manifest, report, certifier
├── integration/      # manifest, integration_pipeline
├── conversation/     # bridge (read-only)
└── dashboard_bridge/ # bridge (read-only)
```

Tidak ada folder `runtime/`.

## Presentation Principle (Article XVI)

- Presentation Layer **tidak pernah berisi business logic**.
- Presentation Layer **tidak pernah menjadi runtime coordinator**.
- Presentation Layer **berkomunikasi hanya melalui RuntimeService**.
- Semua eksekusi tetap berada di Execution Runtime, di belakang Approval Gate.

## Constraint Terjaga

- **Composition-only**; **preview-only**; **deterministic**; **synchronous**
- **0 forbidden imports** di `presentation/` (asyncio/threading/socket/network/IO)
- **0 async / 0 threading / 0 multiprocessing / 0 socket / 0 network**
- **DTO immutable** (`frozen=True`); Bridge read-only
- **0 layer violation** — hanya import internal + stdlib
- **Tidak mengubah subsystem lama** (mis. `operations/`, `desktop/` PySide6 lama tetap utuh)

## Verifikasi

- `pytest tests/presentation` → **189 passed** (regression = 0; semua test dipertahankan)
- Full suite → **3338 passed, 1 skipped**
- `ruff check src/sam/presentation` → **0 errors**
- 0 forbidden imports (AST) di `presentation/`
- CI GitHub Actions → **semua 7 job hijau**

## Dokumentasi Terkait

- `docs/CONSTITUTION.md` — Article XVI: Presentation Principle
- `docs/PHILOSOPHY.md` — Why Presentation Exists
- `docs/releases/v30.0.0_release.md`
- `ROADMAP.md` — Program F: Presentation Layer
