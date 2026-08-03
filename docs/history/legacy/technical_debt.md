# Technical Debt Report — SAM v3.3.0 (post OP-43)

> **Tanggal:** 2026-07-28
> **Tujuan:** Inventarisasi — BUKAN perbaikan.
> **Aturan:** Jangan hapus apa pun. Catat saja.

---

## 1. DEAD CODE

| Item | Lokasi | Alasan | Dampak |
|---|---|---|---|
| `ops.py` legacy commands | `ops.py:120-240` | `cmd_briefing`, `cmd_situation`, `cmd_home`, `cmd_activity`, `cmd_work`, `cmd_approvals`, `cmd_knowledge`, `cmd_history`, `cmd_settings` — semua via `_get_engine()` (ExperienceEngine compat). Tidak ada yang pakai NarrativeEngine lagi. | Medium — masih bisa dipakai, tapi tidak relevan untuk Conversation API. |
| `config.json` | root? | Mungkin sisa dari versi awal. | Low |
| `.github/workflows/ci.yml` condition | `.github/` | Mungkin masih valid. Perlu dicek apakah pipeline masih jalan. | Low |

## 2. COMPATIBILITY LAYER

| Item | Lokasi | Alasan | Dampak |
|---|---|---|---|
| `ExperienceEngine` | `src/sam/experience/engine/experience_engine.py` (700+ lines) | COMPAT. Masih dipakai Desktop. Build dagging untuk semua legacy. | **High** — blocker untuk v4. Desktop harus migrasi ke `sam.observe()`. |
| `QuestionEngine` | `src/sam/operations/question_engine.py` | COMPAT. Sudah digantikan `conversation_api.py`. Tapi masih di-import ExperienceEngine. | **High** — mati setelah ExperienceEngine dihapus. |
| `TelemetryService` — direct import by Desktop | `src/sam/desktop/main.py` | Desktop import `sam.telemetry` langsung. | Medium — harus lewat Conversation API. |

## 3. TEMPORARY ADAPTER

| Item | Lokasi | Alasan | Dampak |
|---|---|---|---|
| `experience_contract.py` | `src/sam/operations/` | Hanya berisi `HumanExplainer` Protocol. Bisa merge ke file lain. | Low |
| `story.py` | `src/sam/operations/` | `StoryBuilder` masih dipanggil oleh `UnderstandingEngine` untuk activity_changes. Bisa inline. | Low |
| `presentation.py` | `src/sam/operations/` | `PresentationEngine` masih dibuat oleh `UnderstandingEngine`. Output sudah diserap ConversationObject. | Low |

## 4. TODO / FIXME

| Item | Lokasi | Detail |
|---|---|---|
| Pydantic V2 migration | `src/sam/telemetry/event.py:63` | `@validator` deprecated. 69 warnings. |
| `desktop/pages/home.py` | Seluruh page | Masih pakai `experience.get_live_answer()`. Harus migrasi ke `sam.observe()`. |
| `desktop/pages/assistant.py` | Seluruh page | Sama, pakai ExperienceEngine. |

## 5. LEGACY TEST FILES

| Item | Lokasi | Alasan | Dampak |
|---|---|---|---|
| `test_api.py` | `tests/unit/` | Import `sam.telemetry.models` yang tidak ada. | **Error on collection.** Blocker untuk `pytest tests/`. |
| `test_contracts.py` | `tests/unit/` | Import `Mission` dari `sam.contracts` yang sudah berubah. | **Error on collection.** |
| `test_guardian.py` | `tests/unit/` | Import `DesiredOperationalState` dari `sam.contracts`. | **Error on collection.** |
| `test_legacy_proposal_lifecycle.py` | `tests/unit/` | Sama, import legacy contracts. | **Error on collection.** |

## 6. DUPLICATE LOGIC

| Item | Lokasi | Detail |
|---|---|---|
| `UnderstandingEngine` vs old `build_home()` | `understanding.py` | UnderstandingEngine sintesis ConversationObject. Tapi `ExperienceEngine.build_home()` masih ada untuk compat. Dua jalur untuk satu tujuan. |
| HumanAnswer rendering | `render/cli.py` vs `human_answer.py` (old display_cli yang sudah dihapus) | Clean — sudah dipisah. Tapi `display_cli()` masih direferensi di test. |

## 7. FUTURE CLEANUP

| Prioritas | Item | Target untuk |
|---|---|---|
| **P1** | Desktop migrasi ke `sam.observe()` | v4.0 |
| **P2** | Hapus ExperienceEngine | v4.0 (setelah Desktop migrasi) |
| **P3** | Hapus QuestionEngine | v4.0 (bersama ExperienceEngine) |
| **P4** | Hapus legacy commands di ops.py | v4.0 |
| **P5** | Fix 4 legacy test files (atau hapus) | v4.0 |
| **P6** | Pydantic V2 migration | v4.1 |
| **P7** | Merge story.py → understanding.py | v4.1 |
| **P8** | Merge experience_contract.py → intent.py (HumanExplainer) | v4.1 |

## Ringkasan

| Kategori | Jumlah | Prioritas Tertinggi |
|---|---|---|
| Dead Code | 3 | Low |
| Compatibility Layer | 3 | **High** |
| Temporary Adapter | 3 | Low |
| TODO/FIXME | 3 | Medium |
| Legacy Test Files | 4 | **High** (blocking pytest) |
| Duplicate Logic | 1 | Medium |
| **Total** | **17** | |

**Prioritas untuk v4:**
1. Desktop migrasi ke `sam.observe()`
2. Hapus ExperienceEngine + QuestionEngine
3. Fix/hapus 4 legacy test files
4. Sisanya insidental
