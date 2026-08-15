# PHASE V2 — Representation Naming (KnowledgeFact + KnowledgeRelation)

**Tanggal:** 2026-08-14
**Jenis:** Analisis kontrak + consumer untuk memberi **nama representasi** yang jelas (BUKAN hapus, BUKAN merge).
**Status:** ✅ **V2-EXEC-001 DIEKSEKUSI (Opsi B, direstui Van).** Storage: `KnowledgeFact`/`KnowledgeRelationship` tetap. Preview di-rename: `KnowledgeFactPreview`/`KnowledgeRelationPreview`. (details di bawah)
**Cakupan:** `KnowledgeFact`, `KnowledgeRelation`/`KnowledgeRelationship` (storage vs preview).

---

## Ringkasan

| Konsep | Storage (Lama) | Preview (Runtime) | Klasifikasi |
|---|---|---|---|
| Knowledge Fact | `sam.knowledge.KnowledgeFact` (pydantic `BaseModel`, `statement`/`document_id`) | `sam.knowledge_runtime.KnowledgeFact` (frozen `dataclass`, `subject`/`predicate`/`obj`) | 🔴 **nama bertabrakan**, representasi beda yang SAH |
| Knowledge Relation | `sam.knowledge.KnowledgeRelationship` (pydantic, `relationship_type`) | `sam.knowledge_runtime.KnowledgeRelation` (frozen, `rel_type`) | 🟡 **nama hampir sama**, representasi beda yang SAH |

**Kesimpulan utama:** keduanya **BUKAN semantic duplicate** (struktur field berbeda total — storage berbasis dokumen/BaseModel, preview berbasis SPO/dataclass). Keduanya representasi **berbeda layer** yang sah, tapi nama `KnowledgeFact` **bertabrakan persis** dan `KnowledgeRelation` vs `KnowledgeRelationship` **membingungkan** (hampir sama, beda module). Tugas V2 = **disambiguasi penamaan**, bukan konsolidasi.

**Tidak ada collision runtime aktif** — tidak ada modul yang mengimpor kedua defisi yang bertabrakan dalam namespace yang sama. Consumer storage terpisah dari consumer preview. Jadi rekomendasi ini bersifat *preventif/hardening* (mencegah drift di masa depan), bukan perbaikan bug aktif.

---

## 1. KnowledgeFact — Dua Definisi

### 1.1 Storage: `sam.knowledge.models.KnowledgeFact` (pydantic BaseModel)

| Atribut | Tipe | Keterangan |
|---|---|---|
| `id` | `UUID` | uuid4 |
| `document_id` | `UUID` | doc sumber |
| `statement` | `str` | pernyataan faktual (natural language) |
| `category` | `str` | capability/provider/model/constraint |
| `confidence` | `float` | 0.0–1.0 |
| `metadata` | `dict` | bebas |
| `created_at` | `datetime` | |
| `version` | `int` | =1 |

**Re-export:** `sam.knowledge.__all__` → `KnowledgeFact`.

**Consumer:** `knowledge/store.py` (CRUD, 12 ref), `knowledge/graph.py` (5 ref), `patterns/engine.py`, `persistence/repositories.py`, `knowledge/__init__.py`. **Domain:** knowledge di-ekstrak dari dokumen, disimpan/disimpan-ulang, diperiksa pola.

### 1.2 Preview: `sam.knowledge_runtime.model.KnowledgeFact` (frozen dataclass)

| Atribut | Tipe | Keterangan |
|---|---|---|
| `fact_id` | `str` | |
| `subject` | `str` | ="" |
| `predicate` | `str` | ="is" |
| `obj` | `str` | ="" |
| `source` | `Optional[str]` | =None |
| `preview_only` | `bool` | =True |

+ `is_valid()` → `bool(fact_id) and bool(subject)`.

**Re-export:** `sam.knowledge_runtime.__all__` → `KnowledgeFact`.

**Consumer:** `knowledge_runtime/builder/fact_builder.py`, `knowledge_runtime/model/knowledge_validator.py`, `model/__init__.py`, dan test `tests/knowledge_runtime/`, `tests/unit/test_sprint181.py`. **Domain:** triple SPO untuk pipeline knowledge runtime (deterministik, no write, preview).

### 1.3 Kenapa bukan duplicate

- **Struktur tidak identik**: storage punya `document_id`/`statement`/`category`/`confidence`/`version`; preview punya `subject`/`predicate`/`obj`/`preview_only`. Model konseptual beda (dokumenter vs SPO).
- **Tidak saling mengisi**: tidak ada consumer yang mengonversi satu ke lain secara langsung dalam repo saat ini.
- **Layer berbeda**: storage = persistence/domain; preview = read-only DTO pipeline.
- Keduanya memang "fact knowledge" secara semantik, jadi nama harus memperjelas *bentuk*.

---

## 2. KnowledgeRelation vs KnowledgeRelationship

### 2.1 Storage: `sam.knowledge.models.KnowledgeRelationship` (pydantic BaseModel)

| Atribut | Tipe |
|---|---|
| `id` | UUID |
| `source_id` | UUID |
| `target_id` | UUID |
| `relationship_type` | str (supports/depends_on/requires/contradicts/related_to) |
| `metadata` | dict |
| `created_at` | datetime |

**Consumer:** `knowledge/graph.py` (8 ref), `knowledge/__init__.py`. **Domain:** relasi dokumen-terpusat untuk simpanan knowledge.

### 2.2 Preview: `sam.knowledge_runtime.model.KnowledgeRelation` (frozen dataclass)

| Atribut | Tipe |
|---|---|
| `relation_id` | str |
| `source_id` | str |
| `target_id` | str |
| `rel_type` | str ="relates_to" |

+ `is_valid()`.

**Consumer:** `knowledge_runtime/builder/relation_builder.py`, `knowledge_validator.py`, `model/__init__.py`, test `test_sprint181.py`. **Domain:** relasi triple untuk pipeline preview.

### 2.3 Kenapa bukan duplicate

- Mirip secara konsep (keduanya relasi source→target), dan **field-nya paralel** (`source_id`/`target_id` sama; `relationship_type` vs `rel_type`; `id` UUID vs `relation_id` str).
- Tapi layer beda: storage (pydantic, persistable, metadata, datetime) vs preview (frozen dataclass, string id, no write).
- Mempertahankan keduanya sah; yang perlu dibereskan = **kesamaan nama** supaya tidak kelihatan duplikat.

---

## 3. Rekomendasi Penamaan (DRAFT — menunggu keputusan Van)

Prinsip (konsisten dengan V1 & "Folder ≠ Semantic Identity"):
- **Jangan merge** — keduanya representasi sah.
- **Beri nama yang memperjelas layer**: storage/persistent vs preview/read-only.
- **Pertahankan `KnowledgeFact` untuk yang paling banyak dipakai / canonical secara semantik.**

### Opsi A — Awalan kanonik (Recommended)

| Konsep | Storage | Preview |
|---|---|---|
| Fact | `StoredKnowledgeFact` | `KnowledgeFact` (tetap, = canonical SPO untuk domain knowledge) |
| Relation | `StoredKnowledgeRelation` | `KnowledgeRelation` (tetap) |

Rasional: `knowledge_runtime` = domain "knowledge" baku (Sprint 181–187, pipeline aktif, 85 ref) → layak memegang nama `KnowledgeFact`/`KnowledgeRelation` kanonik. `knowledge` (lama, storage dokumen) → diganti `Stored*` untuk menandakan representasi persistence.

### Opsi B — Awalan suffix layer

| Konsep | Storage | Preview |
|---|---|---|
| Fact | `KnowledgeFact` (tetap) | `KnowledgeFactPreview` |
| Relation | `KnowledgeRelationship` (tetap) | `KnowledgeRelationPreview` |

Rasional: meminimalkan perubahan (storage paling banyak consumer berubah sedikit/0), menandai preview sebagai turunan.

### Opsi C — Awalan domain eksplisit

| Konsep | Storage | Preview |
|---|---|---|
| Fact | `DocumentKnowledgeFact` | `FactTriple` |
| Relation | `DocumentKnowledgeRelationship` | `RelationTriple` |

Rasional: paling deskriptif, tapi paling invasif (ubah kedua-duanya).

> Rekomendasi awal: **Opsi A** (yang paling sedikit risiko karena `knowledge_runtime` sudah dominan & preview punya helper `is_valid`; storage diberi awalan). Tapi ini keputusan Van — aku siap eksekusi opsi mana pun yang dipilih.

---

## 4. Tidak Disentuh (tetap)

- **`KnowledgeRecord`, `KnowledgeContext`, `KnowledgeTag`** — bukan bagian dari tumpang-tindih ini (tetap di `knowledge_runtime`).
- **`KnowledgeDocument`, `KnowledgeHistory`** — domain storage (`knowledge`) yang tidak bertabrakan, tetap.
- **`PreviewBuilder`, `KnowledgePreviewDTO`** — sudah punya nama preview yang jelas, tetap.
- **Semua modul pipeline `knowledge_runtime` lain** — tidak disentuh.

---

## 5. Impact jika dipilih eksekusi (analisis awal)

| Opsi | Modul yang berubah | File |
|---|---|---|
| A | rename class di `knowledge/models.py` (+ re-export `knowledge/__init__.py`) + consumer | `store.py`, `graph.py`, `patterns/engine.py`, `persistence/repositories.py` |
| B | rename class di `knowledge_runtime/model/*` (+ `__init__.py`) + consumer preview | `fact_builder.py`, `relation_builder.py`, `knowledge_validator.py`, test sprint181/knowledge_runtime |
| C | keduanya | semua di atas |

Detail impact per opsi akan diukur ulang saat keputusan Van turun (scan consumer penuh → regression).

**Belum dieksekusi.** Menunggu keputusan Van: pilih opsi penamaan (A / B / C) — lalu aku jalankan rename + leaf check + regression sesuai pola V1-EXEC.

---

## 6. V2-EXEC-001 — EKSEKUSI (Opsi B, APPROVED Van 2026-08-14)

**Keputusan Van:** Opsi B. Storage tidak diubah namanya; preview di-rename dengan sufiks `*Preview`. `Stored*` ditolak (mengikatkan mekanisme persistence ke nama model → melanggar implementation independence). `KnowledgeRelationship → KnowledgeRelation` rename tambahan ditolak.

### Perubahan final

| Konsep | Storage (tetap) | Preview (rename) |
|---|---|---|
| Fact | `sam.knowledge.KnowledgeFact` | `sam.knowledge_runtime.KnowledgeFact` → **`KnowledgeFactPreview`** |
| Relation | `sam.knowledge.KnowledgeRelationship` | `sam.knowledge_runtime.KnowledgeRelation` → **`KnowledgeRelationPreview`** |

### File yang diubah
- `knowledge_runtime/model/knowledge_fact.py` — `class KnowledgeFactPreview`
- `knowledge_runtime/model/knowledge_relation.py` — `class KnowledgeRelationPreview`
- `knowledge_runtime/model/__init__.py` — re-export `KnowledgeFactPreview`/`KnowledgeRelationPreview`
- `knowledge_runtime/model/knowledge_validator.py` — tipe hint → `*Preview`
- `knowledge_runtime/builder/fact_builder.py` — import/return → `KnowledgeFactPreview`
- `knowledge_runtime/builder/relation_builder.py` — import/return → `KnowledgeRelationPreview`
- `knowledge_runtime/__init__.py` — public surface re-export `*Preview`
- `tests/unit/test_sprint181.py` — import/instansiasi → `*Preview`
- `tests/knowledge_runtime/test_knowledge_runtime_contract_suite.py` — import/instansiasi → `*Preview`

### Yang TIDAK diubah (sesuai aturan Van)
- `sam.knowledge` (storage) — tidak disentuh: `KnowledgeFact`, `KnowledgeRelationship`, `KnowledgeDocument`, `KnowledgeHistory`, store/graph/loader/patterns/persistence.
- `evidence/models.py` — tidak disentuh.
- Struktur bounded context / lokasi package — tidak berubah.
- Behaviour / schema / field — tidak berubah (hanya rename identifier).
- Tidak ada merge storage + preview.
- Tidak ada compatibility alias (public surface `sam.knowledge_runtime` sekarang `*Preview`; tidak ada consumer eksternal terverifikasi yang perlu alias).

### Verifikasi
- Smoke import: `KnowledgeFactPreview`/`KnowledgeRelationPreview` resolve dari `sam.knowledge_runtime` konsisten (identity `is` True).
- Skim: 0 referensi nama lama `KnowledgeFact`/`KnowledgeRelation` (tanpa sufiks) tersisa di seluruh `knowledge_runtime`; 0 import nama lama dari jalur `knowledge_runtime`.
- **Ruff clean** (exit 0).
- **Regression:** `tests/knowledge_runtime/` + `tests/unit/test_sprint181.py` + `test_sprint182.py` = **75 passed**. Full `tests/unit/` = **2941 passed, 1 skipped**.

### Acceptance criteria (dedicated)

| Criterion | Hasil |
|---|---|
| no ambiguous KnowledgeFact definitions in same semantic vocabulary | ✅ `KnowledgeFact` hanya di `sam.knowledge` (storage); `KnowledgeFactPreview` di `knowledge_runtime` |
| no ambiguous KnowledgeRelation definitions | ✅ `KnowledgeRelationship` di storage; `KnowledgeRelationPreview` di preview |
| storage consumers resolve to storage models | ✅ store/graph/patterns/persistence tak berubah |
| preview consumers resolve to preview models | ✅ builder/validator/pipeline/test → `*Preview` |
| no runtime behavior change | ✅ rename-only; 2941+75 passed hijau |
| no new architectural boundary | ✅ |
| no authority/responsibility leakage | ✅ |
| leak check = 0 | ✅ |
| ruff = clean | ✅ |
| targeted regression = green | ✅ |

**V2-EXEC-001 SELESAI.** Sisa V2: Evidence representation + Mission representation (belum dieksekusi, menunggu Van).
