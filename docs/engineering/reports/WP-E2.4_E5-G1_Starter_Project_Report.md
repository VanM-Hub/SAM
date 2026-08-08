# WP-E2.4 - E5-G1 Starter Project / Template Repository

**Mission:** MISSION-2E - Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Work Package:** WP-E2.4 - Starter Project / Template Repository (Priority 4, E5-G1)
**Status:** DONE

---

## Gap yang Ditutup

**E5-G1** (dari EA-001-005 Template & Sample Assessment, High):
> Tidak ada starter project / template repository untuk project SAM baru.
> Ada `examples/plugins/sample-plugin`, tetapi tidak ada scaffold yang
> menghasilkan struktur project lengkap (Mission + Workflow + Runtime).

## Objective Terpenuhi

"Memberi early adopter titik awal konkret untuk membuat project SAM sendiri
(Mission + Workflow + Runtime minimum), langsung dari CLI - tanpa harus
membaca dokumentasi dulu."

## Implementasi

| File | Peran |
|---|---|
| `src/sam/devx/scaffold.py` | **Pure logic scaffold**: `build_files()`, `scaffold_project()`, `ScaffoldProject` |
| `src/sam/devx/__init__.py` | Ekspor `scaffold_project`, `ScaffoldProject`, `build_files` |
| `src/sam/cli/onboarding.py` | Opsi baru `sam onboarding init --scaffold <name>` (+ `--scaffold-dir`, `--apply`) |
| `tests/integration/test_devx_scaffold.py` | 13 test evidence (WP-E2.4) |
| `docs/user/cli_reference.md` | Dokumentasi command `--scaffold` |

### Struktur yang dihasilkan (8 file)

```
<project>/
├── pyproject.toml            # metadata + dependency sam-ops
├── README.md                 # panduan ringkas
├── mission.yaml              # Mission definition (objectives awal)
├── workflow.yaml             # Workflow awal (steps + transition)
└── src/<pkg>/
    ├── __init__.py           # package
    ├── mission/__init__.py   # Mission layer
    ├── workflow/__init__.py  # Workflow layer
    └── runtime/__init__.py   # Runtime layer
```

Menutup gap E5-G1: struktur lengkap Mission + Workflow + Runtime untuk
project SAM baru, dapat dihasilkan sekali perintah.

## CLI

```bash
# Dry-run (tidak menulis apa pun)
python -m sam.cli.main onboarding init --scaffold myproject

# Menulis file ke ./myproject
python -m sam.cli.main onboarding init --scaffold myproject --apply

# Tentukan direktori tujuan
python -m sam.cli.main onboarding init --scaffold myproject \
    --scaffold-dir /path/to/target --apply
```

- `--scaffold` menggantikan jalur `init_plan()`: mengisi janji next-steps
  `sam onboarding init --scaffold` (WP-E2.2).
- Reuse prinsip WP-E2.2: pure logic (scaffold.py) + thin Typer handler,
  tanpa duplikasi. Default dry-run non-destruktif; `--apply` menulis.
- Idempotent: file yang sudah ada tidak ditimpa (dilewati).

## Exit Criteria

| Kriteria | Status |
|---|---|
| Scaffold menghasilkan struktur project SAM lengkap | [x] 8 file (Mission+Workflow+Runtime+pyproject+package) |
| CLI menyediakan perintah scaffold | [x] `sam onboarding init --scaffold` |
| Tidak menulis saat dry-run | [x] default apply=False, tidak sentuh disk |
| Idempotent & aman (tidak timpa existing) | [x] skipped list |
| Evidence suite | [x] 13 test, masuk CI integration |

## Evidence

- `sam.devx.scaffold` diverifikasi 13 test (build_files, dry-run, apply,
  idempotent, validasi) - lolos 3.8 & 3.12.
- CLI smoke: dry-run menampilkan rencana 8 file; `--apply` menulis 8 file;
  apply kedua melewati semua (idempotent); nama invalid ditolak value error.
- Integration suite (3.12): **211 passed** (198 previous + 13 scaffold),
  0 collection error, no regression.
- File baru ASCII-clean (0 non-ascii).

## Compliance EA-002

- [x] Starter project / template untuk project SAM baru (gap E5-G1 High).
- [x] Mengisi janji `sam onboarding init --scaffold` dari WP-E2.2.
- [x] Pure logic di `sam.devx` + thin CLI adapter - tanpa alur paralel.
- [x] SHALL NOT: tidak mengubah runtime/governance/Foundation/ADR.

---

*- WP-E2.4 DONE. Lanjut ke WP-E2.5 (E3-G1 SDK Public API).*
