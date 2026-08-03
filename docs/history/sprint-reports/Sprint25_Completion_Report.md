# Sprint 25 — Completion Report

**Sprint:** 25 — Institutional Intelligence  
**Tanggal:** 2026-07-25  
**Branch:** `feature/sprint13-plugin-runtime`  
**Total Tests:** 1026 passed, 30 deselected, 0 regressions  

---

## Ringkasan

Sprint 25 membangun **Institutional Intelligence** — kemampuan SAM untuk belajar dari seluruh pengalaman operasional di seluruh cluster dan menjadi lebih pintar seiring waktu. Dua fase selesai dalam sprint ini.

---

## Fase 1 — Institutional Memory (Tertinggi)

### File Baru

| File | Deskripsi |
|------|-----------|
| `src/sam/institutional/__init__.py` | Public API exports |
| `src/sam/institutional/memory.py` | InstitutionalMemory model + InstitutionalMemoryManager |
| `src/sam/institutional/lesson.py` | Lesson model + LessonManager |
| `src/sam/persistence/migrations/027_add_institutional_memory.sql` | Tabel `institutional_memory` + `lessons` dengan indexes |
| `test_institutional_memory.py` | 31 test cases |

### Fitur

**InstitutionalMemory** — Entry memori institusional dengan:
- `id`, `type` (KNOWLEDGE, PATTERN, RECOMMENDATION, LESSON), `content` (Dict), `source`, `confidence`
- `success_count` / `failure_count` — riwayat keberhasilan
- `last_used_at`, `created_at`, `updated_at`

**InstitutionalMemoryManager:**
| Method | Fungsi |
|--------|--------|
| `store()` | Simpan/overwrite memory |
| `get()` | Ambil by ID |
| `search()` | Cari by type, source (substring), min_confidence |
| `update_success_rate()` | Increment success/failure counter |
| `get_most_successful()` | Leaderboard per type |

**Lesson** — Pelajaran dari eksekusi intent:
- `intent_id`, `graph_id` — linkage ke eksekusi spesifik
- `what_worked`, `what_failed`, `insight` — narasi
- `evidence_ids` — bukti pendukung

**LessonManager:**
| Method | Fungsi |
|--------|--------|
| `record_lesson()` | Simpan lesson baru |
| `get_lessons()` | Query by intent_id, graph_id, atau semua |

### Migration 027
```sql
institutional_memory (id, type, content, source, confidence, success_count,
                      failure_count, last_used_at, created_at, updated_at)
lessons (id, intent_id, graph_id, what_worked, what_failed, insight,
         confidence, evidence_ids, timestamp)
```
Dengan 6 indexes untuk performa query.

### Tests
- 7 model tests (validasi tipe, confidence, roundtrip serialization)
- 12 manager tests (CRUD, search, filtering, success rate, leaderboard)
- 4 lesson model tests (validasi, serialization)
- 8 lesson manager tests (record, query by intent/graph, empty, multiple)
- **Total: 31 tests**

### Commit
`3f88f2c` — `feat(sprint25): Fase 1 - Institutional Memory`

---

## Fase 2 — Template Evolution (Tinggi)

### File Baru

| File | Deskripsi |
|------|-----------|
| `src/sam/institutional/evolution.py` | TemplateEvolution model + TemplateEvolutionManager |
| `src/sam/persistence/migrations/028_add_template_evolution.sql` | Tabel `template_evolutions` |
| `test_template_evolution.py` | 28 test cases |

### Fitur

**TemplateEvolution** — Proposal evolusi template dengan lifecycle:
- `PROPOSED` → `APPROVED` → `APPLIED` → `ROLLED_BACK`
- Atau `PROPOSED` → `REJECTED`

**TemplateEvolutionManager:**

| Method | Fungsi | Validasi Status |
|--------|--------|-----------------|
| `evaluate_template()` | Evaluasi performa template via InstitutionalMemory | - |
| `propose_evolution()` | Buat proposal baru | - |
| `approve_evolution()` | Setujui proposal | Harus PROPOSED |
| `apply_evolution()` | Terapkan perubahan | Harus APPROVED |
| `rollback_evolution()` | Kembalikan ke asal | Harus APPLIED |
| `reject_evolution()` | Tolak proposal | Harus PROPOSED |
| `get_evolution_history()` | Riwayat perubahan per template | - |

**Evaluasi Template (evaluate_template):**
Membutuhkan minimal **3 eksekusi** (MIN_EVALUATION_EXECUTIONS) di Institutional Memory sebelum memberikan rekomendasi:
- `success_rate >= 0.8` → `stable`
- `success_rate >= 0.5` → `needs_review`
- `success_rate < 0.5` → `needs_improvement`

**Prinsip Aman:** Template tidak langsung berubah — harus melalui pipeline approval: PROPOSED → APPROVED → APPLIED. Setiap perubahan tercatat (audit trail). Rollback selalu tersedia.

### Migration 028
```sql
template_evolutions (id, template_id, original_version, new_version, changes,
                     reason, evidence, status, proposed_at, applied_at,
                     created_at, updated_at)
```
Dengan CHECK constraint `status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'APPLIED', 'ROLLED_BACK')`.

### Tests
- 6 model tests (minimal, full, invalid status, all statuses, roundtrip, JSON parse)
- 5 evaluation tests (no memory, insufficient data, stable, needs_improvement, no data)
- 2 proposal tests (create, multiple)
- 3 approval tests (proposed, already approved, nonexistent)
- 3 apply tests (approved, non-approved, nonexistent)
- 3 rollback tests (applied, non-applied, nonexistent)
- 2 reject tests (proposed, non-proposed)
- 4 history tests (ordered, empty, full lifecycle, evidence)
- **Total: 28 tests**

### Commit
`753ab1e` — `feat(sprint25): Fase 2 - Template Evolution`

---

## Test Results

| Sesi | Jumlah | Perubahan |
|------|--------|-----------|
| Baseline (sebelum Sprint 25) | 967 | — |
| + Fase 1 (Institutional Memory) | 998 | +31 |
| + Fase 2 (Template Evolution) | 1026 | +28 |
| **Final** | **1026 passed** | **+59 total, 0 regressions** |

30 tests di-deselect (pre-existing: test_schedule, test_reporting, test_importer).

---

## Struktur Direktori (Sprint 25)
```
src/sam/institutional/
├── __init__.py        # Public API
├── evolution.py       # TemplateEvolution + TemplateEvolutionManager  (NEW Fase 2)
├── lesson.py          # Lesson + LessonManager                        (NEW Fase 1)
└── memory.py          # InstitutionalMemory + InstitutionalMemoryManager (NEW Fase 1)

src/sam/persistence/migrations/
├── 027_add_institutional_memory.sql   # institutional_memory + lessons tables  (NEW)
└── 028_add_template_evolution.sql     # template_evolutions table              (NEW)

test_institutional_memory.py     # 31 tests (NEW)
test_template_evolution.py       # 28 tests (NEW)
```

---
