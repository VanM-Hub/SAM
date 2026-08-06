# ENG-I - Laporan Akhir Program I (CLI)

**Program:** I (CLI) - **Package:** AP-MISSION-004-001 - **Status:** SELESAI
**Tanggal:** 2026-08-06

---

## 1. Ringkasan

Program I menjadikan CLI sebagai **host resmi Project SAM** - Presentation
Capability yang diakses seluruhnya melalui jalur resmi `runtime_service.api`.
Struktur host dibangun baru (`CLIApplication`, `CLICommand`, `CLICommandRegistry`,
`CLIFormatter`), seluruh command capability di-wire ke gateway runtime via
Dependency Injection di entry. Tidak ada akses langsung ke Runtime/Registry/
Provider/Connector/ExecutionRuntime, dan tidak ada perubahan RuntimeService.

## 2. File Berubah

| File | Peran |
|---|---|
| `src/sam/presentation/cli/application.py` | `CLIApplication` - host (dispatch + render) |
| `src/sam/presentation/cli/commands.py` | `CLICommand`/`CLICommandSpec`/`CLICommandRegistry` (DTO immutable) |
| `src/sam/presentation/cli/formatter.py` | `CLIFormatter` (formatting output) |
| `src/sam/presentation/cli/wiring.py` | `CLIRuntimeWiring` - handler via `runtime_service.api` (DI) |
| `src/sam/presentation/cli/integration.py` | `CLIIntegration` - composition hasil command |
| `src/sam/presentation/cli/__init__.py` | export capability |
| `src/sam/web/server.py` | wiring host CLI di entry (reuse gateway + consumers) |
| `tests/presentation/test_cli_capability.py` | unit + integration test (21) |

## 3. Hasil Test

| Scope | Hasil |
|---|---|
| Unit test CLI capability | **21 passed** |
| Baseline presentation | **250 passed** |
| Regression (presentation+runtime_service+api) | **565 passed** |

> Catatan: `tests/compliance/cli/test_reporter.py::test_two_runs_same_structure`
> flaky pre-existing (variasi `duration_seconds`), tidak terkait file Program I
> (Compliance CLI terpisah; tidak mengimpor file yang diubah).

## 4. Command (Activation Matrix)

Semua command dengan activation path resmi tersedia via `runtime_service.api`:

| Command | Jalur |
|---|---|
| workflow | `preview_with_workflow` |
| policy | `preview_with_policy` |
| audit | `preview_with_audit` |
| preview | `preview` (no execute) |
| knowledge | `preview_with_knowledge` |
| memory | `preview_with_memory` |
| artifact | `preview_with_artifact` |
| approval | pass-through (baca `approved` dari outcome) |
| runtime / health / status | `gateway.api.status()` / `health()` |

## 5. Area Deferred / Escalation

| Area | Keputusan |
|---|---|
| mission | Deferred (no activation path di `runtime_service.api`) - `CLIIntegration.run('mission')` -> status `deferred` |
| import `sam.operations` (di `sam.cli.knowledge`) | STOP (boundary dilarang) - tidak diubah, escalation report |

## 6. Acceptance Criteria

- [x] CLI menjadi host resmi Project SAM.
- [x] Seluruh command dengan activation path resmi tersedia.
- [x] Approval pass-through.
- [x] Mission mengikuti activation path resmi (classifikasi sesuai keputusan Architecture).
- [x] Seluruh akses melalui RuntimeService.
- [x] Tidak ada dependency langsung ke Runtime/Registry/Provider/Connector/ExecutionRuntime.
- [x] Regression PASS.
- [x] Compliance terhadap guardrail architecture (dependency satu arah, DTO immutable, composition-only).
- [x] Tidak ada perubahan baseline Architecture.

## 7. Compliance / Guardrails

- Dependency scan: satu-satunya import keluar di `presentation/cli` adalah
  `sam.runtime_service.api` (diizinkan).
- 0 import langsung ke Runtime/Registry/Provider/Connector/ExecutionRuntime/operations.
- DTO immutable (ADR-023), composition-only, tanpa business logic di presentasi.
- Tidak ada activation path baru, tidak ada perubahan RuntimeService.
- Approval pass-through (tidak buat Approval baru).
- Mission tidak diimplementasi, tidak workaround.

---
*Program I (CLI) SELESAI.*
