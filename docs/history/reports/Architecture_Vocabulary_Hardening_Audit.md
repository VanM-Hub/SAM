# Architecture Vocabulary Hardening — Semantic Ownership Audit

**Tanggal:** 2026-08-14
**Jenis:** Audit kode (bukan dokumentasi) — tanpa perubahan kode, tanpa penghapusan apa pun
**Metode:** Scan statis seluruh `src\sam\**\*.py` — ekstraksi definisi `class`, pengelompokan per nama, pemetaan import/consumer.

---

## Ringkasan Eksekutif

| Metrik | Nilai |
|---|---|
| Total nama class distinct | **5113** |
| Nama yang muncul di **>1 file** | **526** (≈10%) |
| Konsep domain inti yang bertabrakan | **±40 nama** (lihat daftar bawah) |
| Vocabulary yang **bersih** (tanpa collision) | `Subject`, `SubjectRef`, `Authority`, `AuthorityGrant`, `DelegationGrant`, `Ward`, `CitizenIdentity`, `WardIdentity` |

**Kesimpulan utama:** Risiko *semantic drift* yang diperingatkan Van **terkonfirmasi nyata** — bukan di folder, melainkan di **nama class/model yang bertabrakan**. Polanya jelas: SAM punya **beberapa generasi arsitektur yang hidup berdampingan** (`runtime_kernel` baru vs `runtime` lama vs `agent/state` vs `mission_runtime` vs `operations` vs `universal_*`), dan tiap generasi membawa *vocabulary* sendiri yang namanya saling bertabrakan.

---

## Klasifikasi (3 kategori, sesuai verdict Van)

### A. SEMANTIC DUPLICATE — definisi identik/hampir identik, HARUS jadi SATU canonical

| Nama | Lokasi | Bukti | Status |
|---|---|---|---|
| `RuntimeState` | `contracts/runtime.py:8` **vs** `runtime/state.py:8` | **12 nilai identik persis** (INITIALIZING..SAFE_MODE) | 🔴 duplicate sejati |
| `EvidenceType` | `compliance/catalog/models.py:45` (7 anggota) **vs** `compliance/models/evidence_type.py:6` (10 anggota = superset) | dua-duanya di-import consumer berbeda (`loader.py` pakai catalog; 12 file lain pakai models/evidence_type) | 🔴 duplicate sejati (satu versi tua, satu superset) |

> Ini yang paling berbahaya: dua definisi `EvidenceType` berbeda jumlah anggota → dua bagian SAM bisa "setuju" nilai evidence yang berbeda.

### B. REPRESENTATION BERBEDA — sama *domain concept*, model beda karena layer (storage/preview/transport). SAH, tapi perlu nama yang menjelaskan representasi.

| Konsep | Lokasi & bentuk | Layer |
|---|---|---|
| **KnowledgeFact** | `knowledge/models.py:45` (pydantic `BaseModel`) vs `knowledge_runtime/model/knowledge_fact.py:12` (frozen `dataclass`) | storage vs preview |
| **KnowledgeRelation/Relationship** | `knowledge_runtime/model/knowledge_relation.py` (`KnowledgeRelation`, dataclass) vs `knowledge/models.py:28` (`KnowledgeRelationship`, BaseModel) | preview vs storage |
| **Evidence** | `environment/confidence.py:22` (DTO) · `evidence/models.py:40` (BaseModel storage) · `models/models.py:98` (Entity) · `operations/verification.py:23` (DTO) | 4 bentuk, 4 layer |
| **Mission** | `contracts/mission.py:24` (BaseModel) · `execution_runtime/m7_mission_framework.py:134` · `operations/mission_controller.py:60` | contract vs framework vs ops |

### C. BOUNDED-CONTEXT BERBEDA — nama sama, domain BEDA, masing-masing SAH (tapi rawan saat import lintas konteks)

**State machine (paling banyak, masing-masing domain punya state sendiri):**

| Nama | Jumlah definisi | Contoh nilai berbeda |
|---|---|---|
| `SessionState` | 5 | compliance (`INITIATED..ARCHIVED`) · execution (`CREATED..CLOSED`) · universal_ai (`CREATED..EXPIRED`) · operational_intelligence · universal_agent |
| `RuntimeState` (variant lifecycle) | 3 enum beda | `contracts`==`runtime` (12 nilai) vs `runtime_root/lifecycle.py` (`CREATED/BUILT/STARTED/STOPPED/DISPOSED`) |
| `MissionState` | 3 | agent/session · mission_runtime · operations (`Enum`) |
| `MissionStatus` | 3 | contracts (`str,Enum`) · mission_runtime · guardian/supervisor |

**Provider layer (banyak definisi paralel — execution vs providers vs universal_ai vs observation):**

| Nama | Jumlah definisi |
|---|---|
| `ProviderStatus` | 5 |
| `ProviderRegistry` | 4 |
| `ProviderHealth` | 3 |
| `ProviderSelector` | 3 |
| `ProviderDescriptor` | 3 |
| `ProviderCapability` | 3 |
| `ProviderIdentity` | 2 |
| `ProviderObservation` | 2 |
| `ProviderSession` | 2 |
| `ProviderSummary` | 2 |

**Capability layer:**

| Nama | Jumlah definisi |
|---|---|
| `Capability` | 3 (execution/connectors · models/Entity · sdk/ABC) |
| `CapabilityDescriptor` | 2 |
| `CapabilityMatrix` | 2 |
| `CapabilityStatus` | 2 |

**Mission layer (agent vs mission_runtime vs operations vs platform):**

| Nama | Jumlah definisi |
|---|---|
| `MissionContext` | 4 |
| `MissionState` / `MissionRegistry` / `MissionRepository` / `MissionRequest` / `MissionPlan` / `MissionSnapshot` / `MissionStep` / `MissionSummary` | 3 tiap |
| `MissionStatus` / `MissionTimeline` / `MissionBuilder` / `MissionSession` | 2–3 tiap |

**Policy / Evidence / reasoning:**

| Nama | Jumlah definisi |
|---|---|
| `PolicyCard` | 8 (UI dashboard card per module) |
| `PolicyEngine` | 3 (approval · guardian · policy_runtime) |
| `PolicyResult` | 3 |
| `PolicyBuilder` / `PolicyDecision` / `ApprovalPolicy` | 2 tiap |
| `EvidenceChain` | 4 |
| `EvidenceRepository` | 4 |
| `EvidenceType` | 3 (2 = duplicate, 1 = evidence/models beda domain) |
| `EvidenceGraph` / `EvidenceNode` | 2 |
| `EvidenceRef` / `EvidenceSet` / `EvidenceItem` / `EvidenceVerification` | 2 tiap |

**Core/state validator:**

| Nama | Jumlah definisi |
|---|---|
| `StateValidator` | 3 (agent · mission_runtime · runtime_kernel) |
| `StateMachine` | 2 (agent · runtime_kernel) |
| `WorkflowStateMachine` | 2 (foundation · recovery) |
| `ObservationEngine` | 2 (autonomy_runtime · operations/brain) |
| `ObservationSummary` | 2 |

---

## Pola Akar Masalah

1. **Beberapa "runtime" hidup berdampingan** — `runtime` (lama) vs `runtime_kernel` (baru) vs `agent/state` vs `mission_runtime` vs `operations` — tiap satu membawa state/model/validator sendiri dengan nama sama.
2. **`universal_*` vs layer lama** — `universal_ai`, `universal_tool`, `universal_agent`, `universal_workflow` (MISSION-5.x) membawa `Provider*`, `Capability*`, `SessionState` paralel dengan `providers/`, `execution/`, `governed_reasoning/`.
3. **`PolicyCard` ×8** adalah sinyal terkuat duplikasi template UI — card identik dicopy ke 8 module dashboard.
4. **`EvidenceType` ×2 (satu superset)** adalah sinyal *drift* paling berbahaya — versi compliance punya 7 vs 10 anggota, consumer beda memakai beda versi.

---

## Yang TIDAK bermasalah (bukti sehat)

- **`Subject`, `SubjectRef`** — hanya di `ward/capability/contracts.py` (tunggal). Bersih.
- **`Authority`, `AuthorityGrant`, `DelegationGrant`** — tidak ada collision (tunggal di `delegated_authority`). Bersih.
- **`CitizenIdentity`, `WardIdentity`** — tunggal. Bersih.
- **`KnowledgeFact`** — sudah ditemukan sebelumnya (verdict Van), tercatat di sini sebagai **representation berbeda** (bukan duplicate folder).

---

## Rekomendasi (TIDAK dieksekusi — menunggu keputusan Van)

1. **Jangan hapus folder** — tidak ada folder duplikat; masalah ada di *nama class*.
2. **Jangan refactor runtime cluster** — dulu keliru (nama folder mirip ≠ duplikat); sekarang fokusnya *class collision*.
3. **Jangan tambah CitizenKind/WardKind** — vocabulary Citizen/Ward sudah bersih.
4. **Tetapkan canonical owner** untuk 2 semantic duplicate paling tajam: `RuntimeState` (contracts vs runtime) dan `EvidenceType` (catalog 7 vs models 10).
5. **Beri nama representasi** untuk `KnowledgeFact`/`KnowledgeRelation` (storage vs preview) — contoh arah: `KnowledgeFact` (domain) / `StoredKnowledgeFact` / `KnowledgeFactPreview` (final naming ditentukan setelah baca kontrak + consumer).
6. **Audit lanjutan per family** (State/Provider/Capability/Mission) — tiap family butuh 1 sesi penamaan canonical sebelum konsolidasi.
