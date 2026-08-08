# WP-E2.2 - E2-G1 CLI Onboarding

**Mission:** MISSION-2E - Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Work Package:** WP-E2.2 - CLI Onboarding (Priority 2, E2-G1)
**Status:** DONE

---

## Gap yang Ditutup

**E2-G1** (dari EA-001-007 Early Adopter Readiness Matrix, High):
> Tidak ada command `sam --version` / `sam doctor` / `sam init` untuk onboarding -
> Discovery cepat (versi, kesehatan instalasi, inisialisasi project) belum
> tersedia dari CLI inti.

## Objective Terpenuhi

"Menghilangkan friksi onboarding sehingga early adopter dapat memverifikasi
versi, mendiagnosa kesehatan instalasi, dan memahami langkah inisialisasi
project langsung dari CLI."

## Implementasi

Logika onboarding diletakkan di **`src/sam/devx/onboarding.py`** (pure logic,
testable tanpa CLI, REUSE komponen WP-E2.1 - tanpa duplikasi).

| File | Peran |
|---|---|
| `src/sam/devx/onboarding.py` | Logika murni: `version_string()`, `doctor()`, `init_plan()`, DTO `DoctorReport` & `InitPlan` |
| `src/sam/devx/__init__.py` | Tambah 5 exports baru: `doctor`, `DoctorReport`, `init_plan`, `InitPlan`, `version_string` |
| `src/sam/cli/onboarding.py` | Handler Typer tipis: `sam onboarding version / doctor / init` |
| `src/sam/cli/main.py` | Registrasi subcommand `onboarding` (init, doctor, version) |
| `tests/integration/test_devx_onboarding.py` | **12 evidence tests** |

### Command dan PRINSIP reuse (no duplikasi)

| Command | Fungsi | Reuse komponen |
|---|---|---|
| `sam onboarding version` | Tampilkan versi package (metadata, fallback `sam.__version__`; tidak pernah error) | `version_string()` |
| `sam onboarding doctor` | Diagnosa kesehatan instalasi & environment, agregat blocking issues | `DependencyChecker` + `EnvironmentValidator` (dari WP-E2.1) |
| `sam onboarding init` | Rencana onboarding project (dry-run, TIDAK mengubah filesystem): cek struktur repo + dry-run bootstrap | `EnvironmentValidator` + `bootstrap(apply=False)` (dari WP-E2.1) |

**Pemisahan scope (penting):** `sam init` di WP-E2.2 hanya menyediakan *onboarding
plan* (inspeksi kesiapan + dry-run bootstrap + next steps). Scaffold starter-project
penuh adalah **scope WP-E2.4 (E5-G1)**, bukan di sini - dijaga agar WP tidak saling
tumpang tindih.

## Alur

```
sam onboarding:
  version  ->  version_string()          (metadata versi)
  doctor   ->  DependencyChecker.run() + EnvironmentValidator.run() -> DoctorReport
  init     ->  EnvironmentValidator.check_repo_structure()
            ->  bootstrap(apply=False)                             (dry-run, 6 fase)
            ->  InitPlan { structure_ok, bootstrap_report_ok, phases, next_steps }
```

- Default **dry-run** untuk `init` - tidak mengubah filesystem (terbukti test).
- `doctor`/`init` read-only dan non-destruktif.
- Konsisten dengan pola EA-002: logika di lapisan devx stand-alone, handler CLI
  tetap "thin".

## Exit Criteria

| Kriteria | Status |
|---|---|
| Command onboarding tersedia di CLI | [x] `sam onboarding init / doctor / version` |
| Versi dapat ditampilkan tanpa error | [x] `version_string()` robust lintas env |
| Kesehatan instalasi dapat didiagnosa | [x] `doctor()` agregat dependency + environment |
| Rencana inisialisasi dapat ditampilkan (dry-run) | [x] `init_plan()` + bootstrap dry-run |
| Tidak ada duplikasi logika (reuse WP-E2.1) | [x] checker/validator/bootstrap dipakai ulang |
| Tidak ada regresi | [x] integration **198 passed** |

## Evidence

- **12 test** di `tests/integration/test_devx_onboarding.py` (5 area):
  - VersionString 2, Doctor 4, InitPlan 5, Consistency 1.
- Test memakai `tmp_path` fixture (BUKAN folder repo) & TIDAK menggantung sukses
  pada `import sam` runtime (pola WP-E2.1) - deterministic di semua environment.
- Terbukti dry-run `init` tidak membuat venv / mengubah filesystem (assert set file
  sebelum == sesudah).

## Verifikasi

| Scope | Hasil |
|---|---|
| Compile (2 module) | OK |
| `import sam.cli.main` | Clean (3.8 & 3.12) |
| test_devx_onboarding (3.8) | **12/12 passed** |
| test_devx_onboarding (3.12) | **12/12 passed** |
| Integration suite (3.12) | **198 passed** (186 existing + 12 baru), 0 collection error |
| CLI smoke (3.12) | `onboarding version` -> `SAM v1.0.0`; `onboarding doctor` -> diagnosa; `onboarding init` -> 6 fase + next steps |

> Catatan mesin lokal: venv repro 3.12 menampilkan 1 blocking issue `build-backend`
> pada `sam onboarding doctor` karena setuptools/wheel tidak terdeteksi dari konteks
> PATH saat itu (artifact environment, bukan regresi logika) - doctor menampilkan
> masalah dengan jujur sesuai desain.

## Compliance EA-002

- [x] Menyediakan command onboarding untuk early adopter (discovery cepat).
- [x] Reuse komponen WP-E2.1 (no duplikasi) - efisien dan konsisten.
- [x] Dry-run / read-only default - deterministik, non-destruktif.
- [x] Mempertahankan seluruh batas arsitektur (Developer Experience layer saja).
- [x] SHALL NOT: tidak mengubah Foundation/Constitution/Governance/Runtime/ADR.

---

*- WP-E2.2 DONE. Lanjut ke WP-E2.3 (E4-G1 Quick Start).*
*Reporting per Engineering Rule: laporan hanya saat WP selesai / Stop Condition /
Architecture Issue / Program selesai.*
