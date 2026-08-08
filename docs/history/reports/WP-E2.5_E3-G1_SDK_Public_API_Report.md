# WP-E2.5 - E3-G1 SDK Public API Expansion

**Mission:** MISSION-2E - Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Work Package:** WP-E2.5 - SDK Public API Expansion (Priority 5, E3-G1)
**Status:** DONE

---

## Gap yang Ditutup

**E3-G1** (dari EA-001-003 SDK Readiness Report, High):
> Public API sangat sempit (hanya `SAM` di root). `Conversation`/`MissionSession`
> disebut di docstring tetapi tidak diekspor di `__all__` - early adopter SDK
> mungkin bingung.

## Objective Terpenuhi

"Membuat public surface SDK sesuai kontrak yang didokumentasikan: seluruh
simbol STABLE_API (`SAM`, `Conversation`, `MissionSession`) benar-benar
diekspor dari root package `sam` - sehingga early adopter SDK dapat memakai
contract yang dijanjikan tanpa kebingungan."

## Implementasi

| File | Peran |
|---|---|
| `src/sam/__init__.py` | Ekspor `SAM`, `Conversation`, `MissionSession` di `__all__` (sesuai docstring STABLE_API) |
| `tests/unit/test_sdk_public_api.py` | 7 test evidence (masuk baseline CI via `tests/unit`) |

### Perubahan root package

Sebelum:
```python
__all__ = ["SAM"]
```

Sesudah:
```python
from .operations.conversation_api import Conversation
from .operations.conversation_api import SAM
from .operations.session import MissionSession

__all__ = ["SAM", "Conversation", "MissionSession"]
```

- Tidak mengubah definisi kelas/behavior; hanya memperluas ekspor ke permukaan
  publik yang sudah diklaim STABLE_API di docstring.
- `SAM.observe()` tetap satu-satunya entry point yang mengembalikan `Conversation`
  (kontrak utama dipertahankan).
- Tidak ada perubahan testpaths baseline CI: test diletakkan di `tests/unit`
  (sudah termasuk baseline) - memenuhi rule "capability tidak Operational tanpa
  evidence di baseline CI" tanpa perlu perluasan folder.

## Exit Criteria

| Kriteria | Status |
|---|---|
| `Conversation` & `MissionSession` diekspor dari root | [x] `__all__ = ["SAM","Conversation","MissionSession"]` |
| Import root & `from sam import *` bekerja | [x] diverifikasi 3.8 & 3.12 |
| `sam.observe()` kontrak Conversation dipertahankan | [x] tidak diubah |
| Evidence suite dalam baseline CI | [x] tests/unit/test_sdk_public_api.py (7 test) |
| Tanpa regresi | [x] baseline unit 2970 passed; integration 211 passed |

## Evidence

- Root `sam.__all__` = `["SAM", "Conversation", "MissionSession"]`; `from sam
  import *` hanya mengekspor 3 simbol publik (tidak ada leak internal).
- `sam.SAM`, `sam.Conversation`, `sam.MissionSession` dapat di-import, valid
  (type).
- `SAM.observe()` mengembalikan `Conversation` (kontrak dipertahankan).
- 7/7 test public API lulus pada 3.8 & 3.12.
- Baseline unit suite (3.8): **2970 passed** (1 skipped), no regression.
- Integration suite (3.12): **211 passed**, 0 collection error, no regression.
- File source & test baru ASCII-clean.

## Compliance EA-002

- [x] Perluas public surface SDK sesuai kontrak STABLE_API (gap E3-G1 High).
- [x] Hanya ekspor (tidak mengubah behavior/definisi) - aman & non-destruktif.
- [x] Evidence masuk baseline CI tanpa mengubah testpaths.
- [x] SHALL NOT: tidak mengubah runtime/governance/Foundation/ADR; tidak ada
  Runtime Responsibility baru.

---

*- WP-E2.5 DONE.*
