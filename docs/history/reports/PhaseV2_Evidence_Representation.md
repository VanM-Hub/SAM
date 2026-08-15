# PHASE V2 — Evidence Representation (verifikasi + penetapan)

**Tanggal:** 2026-08-14
**Jenis:** Analisis kontrak + consumer — verifikasi disambiguasi penamaan domain Evidence.
**Status:** ✅ **VERIFIKASI SELESAI — TIDAK ada perubahan kode** (tidak ada collision nyata → tidak ada rename; sesuai keputusan Van: hanya rename jika ada collision consumer nyata).
**Cakupan:** `EvidenceType` (enum) & `Evidence` (class) di semua bounded context.

---

## Ringkasan

Tidak ada perubahan kode. Semua definisi `EvidenceType`/`Evidence` yang tersisa = representasi beda yang **SAH** di bounded context terpisah, **tanpa collision consumer nyata**. Sama dengan keputusan Van pada `KnowledgeRelationship` (tidak direname karena tidak ada collision).

| Konsep | Definisi | Bentuk | Bounded context |
|---|---|---|---|
| `EvidenceType` (enum) | `sam.compliance.models.evidence_type.EvidenceType` | `Enum` 10 nilai (FILE_*, SOURCE_*, ...) | compliance canonical (V1-EXEC) |
| `EvidenceType` (enum) | `sam.evidence.models.EvidenceType` | `str, Enum` 15 nilai lowercase (health_check, ...) | operational evidence (E3, tidak disentuh V1) |
| `Evidence` (class) | `sam.evidence.models.Evidence` | pydantic `BaseModel` (capability_id, execution_id, type, status, confidence, payload, source, timestamp, metadata) | operational evidence store |
| `Evidence` (class) | `sam.environment.confidence.Evidence` | frozen `dataclass` (source, statement, strength, negative) + `as_dict()` | environment confidence assessment |
| `Evidence` (class) | `sam.models.models.Evidence` | `Entity` subclass (source, evidence_type str, confidence, timestamp, payload) | domain entity layer |

**Tidak masuk scope** (nama berbeda, tidak bentrok): `EvidenceRef` (adaptive_governance & governed_reasoning), `EvidenceModel`/`EvidenceSource`/`EvidenceChain` (operational_intelligence), `EvidenceEntry`/`EvidenceIndex` (observation), `EvidenceRepository` (berbagai — protocol/repo), `EvidenceNode`/`EvidenceEdge`/`EvidenceGraph` (citizen.federation), `CertificationEvidence`/`ToolCertificationEvidence` dll (berbagai cert).

---

## 1. Dua `EvidenceType` — verifikasi

### 1.1 Definisi
- **E2 canonical** (`sam.compliance.models.evidence_type.EvidenceType`): `Enum` murni, 10 anggota (FILE_EXISTS, FILE_ABSENT, SOURCE_CONTAINS, SOURCE_ABSENT, TEST_PASS, TEST_COUNT, IMPORT_LEGAL, IMPORT_ILLEGAL, LIFECYCLE_VALID, TRACE_CHAIN) + helper `from_str()`/`__str__()`. **Canonical compliance type** (V1-EXEC-002, commit `7d62a37`).
- **E3 operational** (`sam.evidence.models.EvidenceType`): `str, Enum`, 15 anggota lowercase (health_check, config_validation, provider_test, runtime_observation, filesystem_check, network_check, permission_check, api_response, execution_trace, error_event, decision_outcome, pattern_match, anomaly_detected, recovery_action, custom). **Operational evidence types** — Evidence Store.

### 1.2 Klasifikasi
**BUKAN duplicate.** Nilai berbeda total, domain berbeda (compliance checks vs operational capability evidence), `str` Enum (E3) vs `Enum` (E2). Satu-satunya kesamaan = nama class.

### 1.3 Verifikasi collision
**0 collision runtime aktif.** Tidak ada modul yang mengimpor kedua `EvidenceType` dari `sam.compliance` DAN `sam.evidence` dalam satu namespace. Consumer compliance (`sam.compliance.*`) terisolasi dari consumer operational (`sam.evidence.*`, `sam.runtime` via `EvidenceStore`).

### 1.4 Keputusan
**TIDAK rename.** Dua `EvidenceType` = konsep berbeda (compliance vs operational) di bounded context terpisah, tanpa collision. Menurut keputusan Van (`Stored*` ditolak, "tidak perlu rename terminologi kecuali ada collision consumer nyata"), kedua nama tetap. `sam.compliance` sudah punya 1 canonical (V1). `sam.evidence` = bounded contextual operational yang sah.

---

## 2. Tiga `Evidence` — verifikasi

### 2.1 Definisi
| # | Lokasi | Bentuk | Atribut |
|---|---|---|---|
| EV1 | `sam.evidence.models` | pydantic `BaseModel` (frozen) | id, capability_id, execution_id, type:`EvidenceType`, status:`EvidenceStatus`, confidence, payload, source, timestamp, metadata |
| EV2 | `sam.environment.confidence` | frozen `dataclass` | source, statement, strength, negative + `as_dict()` |
| EV3 | `sam.models.models` | `Entity` subclass | source, evidence_type (str), confidence, timestamp, payload |

### 2.2 Klasifikasi
**BUKAN duplicate.** EV1 (operational record pakai enum `EvidenceType`) vs EV2 (confidence fact: source/statement/strength — konsep beda) vs EV3 (domain entity layer lama, `evidence_type` sebagai string). Struktur beda, tujuan beda.

### 2.3 Verifikasi collision
Scan seluruh src+tests: **0 collision namespace**. Satu-satunya file yang mengimpor dari 2 jalur (`sam.evidence` + `sam.models`) adalah `src/sam/runtime/context.py` — tapi impornya `EvidenceStore` (dari `sam.evidence.store`) dan `CorrelationContext` (dari `sam.models`), **bukan class `Evidence`**. Tidak ada kesamaan nama dalam namespace yang sama.

### 2.4 Keputusan
**TIDAK rename.** Tiga `Evidence` = konsep berbeda di bounded context terpisah, tanpa collision. Konsisten dengan prinsip "duplicate name ≠ duplicate concept".

---

## 3. Kesimpulan V2 Evidence representation

| Pertanyaan | Jawaban |
|---|---|
| Apakah ada duplicate sejati `EvidenceType`? | Tidak (sudah disatukan di V1: catalog → canonical). `sam.evidence` operational = beda, tidak disentuh. |
| Apakah ada duplicate sejati `Evidence`? | Tidak (3 representasi beda, bounded context berbeda). |
| Apakah ada collision runtime aktif? | **Tidak** — 0 untuk keduanya. |
| Perlu rename? | **Tidak.** Tidak ada alasan arsitektural (konsisten keputusan Van). |
| Perlu merge? | **Tidak.** |

**Catatan:** ini hasil yang diharapkan — V2 bukan proyek global class deduplication. Evidence domain sudah sehat setelah V1 menetapkan canonical compliance `EvidenceType`. Tidak ada `*Preview`/`Stored*` yang perlu diberi awalan di sini karena tidak ada pasangan storage-vs-preview yang bertabrakan nama dalam satu konsep.

---

## 4. Persilangan dengan V3-V7

Evidence vocabulary juga disinggung di V7 (`Evidence vocabulary`, per sequence Van). V2 ini memverifikasi representasi `Evidence`/`EvidenceType` secara menyeluruh; bila V7 nanti menemukan collision nyata di kosakata evidence yang lebih luas (mis. `EvidenceChain`, `EvidenceRepository`, `EvidenceModel`), itu akan ditangani di V7, bukan sekarang (konsisten "jangan dikerjakan sekaligus").
