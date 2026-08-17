# Audit — Chain Canonical Capability vs MissionUXService (ADR-007 follow-up)

- **Tanggal:** 2026-08-17
- **Pemicu:** STOP AD-ENG-007 implementation (Van). Whitelist capability di MissionUXService berpotensi architectural violation; kita menemukan ada chain canonical yang seharusnya dipakai.
- **Tujuan:** Petakan sejauh mana chain canonical **Capability Manager → Registry → Discovery Resolver → Contract → Approval** benar-benar diwujudkan di Reference Runtime, dan **tepat di mana** MissionUXService memotong/melewati chain itu. Bukan membuat ADR/allowlist baru.
- **Metode:** trace import + struktur kode `src/sam/` (reference source, tanpa eksekusi).

---

## 1. Ringkasan eksekutif

**Reference Runtime sudah mewujudkan chain canonical secara nyata dan utuh** di `src/sam/runtime/` + `src/sam/runtime_root/` (composition root `RuntimeBuilder`), dalam urutan deterministik 7 unit:

```
citizen_host → capability_manager → discovery_resolver → contract_enforcer
            → approval_coordinator → execution_scheduler → audit_recorder
```

**Namun chain ini TIDAK digunakan oleh jalur aplikasi nyata.** `MissionUXService` (`src/sam/application/ux/service.py`) — satu-satunya pintu yang dipakai UI Mission Workspace — **tidak mengimpor satupun modul chain canonical** (`capacibility_manager`, `registry`, `discovery_resolver`, `contract_enforcer`, `approval_coordinator`). Ia membangun whitelist capability sendiri (`_AI_CAPABILITIES` + `_resolve_capability`), dan mengeksekusi lewat `runner.run_mission` sendiri.

**Kesimpulan:** implementasi allowlist capability di MissionUXService = **architectural violation**, karena logika admission capability seharusnya menjadi tanggung jawab Capability Manager / Discovery Resolver canonical (Reference Runtime), bukan whitelist hardcoded di application service.

---

## 2. Chain canonical — APA yang sudah diwujudkan (Reference Runtime)

### 2.1 Lokasi & komponen nyata
| # | Unit chain | Modul canonical | Class nyata | API publik kunci |
|---|---|---|---|---|
| 1 | Citizen Host | `runtime/citizen_host` | `HostService` | domain bounded, certification |
| 2 | **Capability Manager** | `runtime/capability_manager` | `CapabilityManagerService` | `publish(declaration)`, `transition`, `get_capability`, `list_capabilities`, `is_discoverable`, `get_health` |
| 3 | **Registry** | `runtime/registry` (+`runtime/discovery.py`) | `CapabilityRegistry` | canonical registry (compat façade di `sam.runtime.registry`) |
| 4 | **Discovery Resolver** | `runtime/discovery_resolver` | `DiscoveryResolver` | `register_entry`, `resolve(request)→ResolutionResult`, `resolve_exact`, `resolve_compatible`, `list_entries` |
| 5 | **Contract Enforcer** | `runtime/contract_enforcer` | `EnforcerService`, `NegotiatorService` | enforce contract, idempotency, negotiation |
| 6 | **Approval Coordinator** | `runtime/approval_coordinator` | `CoordinatorService` | approval request/decision/identity, boundary/decision validator |
| 7 | Execution Scheduler | `runtime/execution_scheduler` | `SchedulerService` | scheduling, idempotency, ordering, verification |
| 8 | Audit Recorder | `runtime/audit_recorder` | `RecorderService` | audit record, traceability, archive |

**Model inti:** `CapabilityDescriptor` (immutable; identity/name/version/inputs/outputs/constraints/compatibility/lifecycle_state/certification_status, authority CAPABILITY_SPEC R5-001, I0-001 §2.2).

### 2.2 Composition root: RuntimeBuilder
- `src/sam/runtime_root/runtime_builder.py` — `RuntimeBuilder.build()` me-instantiate **persis 7 unit** dalam `PIPELINE` canonical, memvalidasi struktur (jumlah == 7, acyclic, 6 edge adjacency), membangun `RuntimeContainer` (7 dependency), health producer, dan `RuntimeRoot` (BUILT→STARTED→STOPPED).
- `CANONICAL_EDGES` eksplisit: citizen_host→capability_manager→discovery_resolver→contract_enforcer→approval_coordinator→execution_scheduler→audit_recorder.
- Satu-satunya konsumen: `RuntimeBuilder` di-instantiate **hanya di dalam `runtime_root/`** (`main.py`, `runtime_root.py`, `__main__.py`). **Tidak ada konsumen luar.**

### 2.3 Status kedewasaan (referensi source)
- Chain lengkap: **DIWUJUDKAN** (bukan kerangka kosong) — ada interface, service, state, validation, lifecycle, health per unit.
- Approval: `approval_coordinator` (canonical chain) — lengkap.
- Fokus audit ini (per arahan Van): bagian **Capability Manager → Registry → Discovery Resolver → Contract** untuk admission capability.

---

## 3. Jalur yang DIPAKAI produksi — MissionUXService (application/ux)

`MissionUXService` adalah pintu yang dipakai UI (M9/M10). Struktur capability/approval/eksekusinya:

| Fungsi | Implementasi di ux | Sumber authority |
|---|---|---|
| Advertise capability | `_AI_CAPABILITIES` (sebelumnya 8, ADR-007 → 7 ops) — **hardcoded list** | service.py, TIDAK dari CapabilityManager |
| Admission/validasi capability | `_resolve_capability` (ADR-007) — **whitelist hardcoded lokal** | service.py, TIDAK dari DiscoveryResolver |
| Eksekusi mission | `runner.run_mission` — dispatcher self-contained (prefix `github.*`/`web.*`/`http.*`/`environment.*`) | runner.py, TIDAK dari ExecutionScheduler |
| Approval | `ApprovalGate` (**dari `sam.execution_runtime.approval_gate`**) | gate canonical execution_runtime (BUKAN `approval_coordinator` Reference Runtime) |

### Import aktual `service.py`
Hasil trace: `service.py` hanya mengimpor dari `sam.application.ux.*` (approval, plan, runner, state, store, mission_request, metrics, persistence, pgstore). **TIDAK ada import `sam.runtime.*`** (capability_manager/registry/discovery_resolver/contract_enforcer/approval_coordinator).

### Registry milik ux sendiri
- `mission_registry.py` → `MissionRegistry` / `MultiMissionService` — registry **mission**, bukan capability.
- Tidak ada `CapabilityRegistry` canonical di jalur ux.

---

## 4. Bypass — tepat di mana MissionUXService memotong chain

Mapping antara chain canonical vs jalur yang benar-benar dipakai:

| Langkah canonical | Reference Runtime (diwujudkan) | Dipakai MissionUXService? | Keterangan bypass |
|---|---|---|---|
| Capability Manager (publish/admission) | ✅ `capability_manager` | ❌ **TIDAK** | ux pakai `_AI_CAPABILITIES` hardcoded |
| Registry | ✅ `registry`/`CapabilityRegistry` | ❌ **TIDAK** | ux tanpa capability registry |
| Discovery Resolver (resolve capability) | ✅ `discovery_resolver.resolve()` | ❌ **TIDAK** | ux pakai `_resolve_capability` (whitelist lokal) |
| Contract Enforcer | ✅ `contract_enforcer` | ❌ **TIDAK** | ux tanpa enforced contract |
| Approval | ✅ `approval_coordinator` | ⚠️ **SEBAGIAN** | ux pakai `ApprovalGate` `execution_runtime` (bukan `approval_coordinator` Runtime Reference) |
| Execution | ✅ `execution_scheduler` | ❌ **TIDAK** | ux pakai `runner.run_mission` |
| Audit | ✅ `audit_recorder` | ❌ **TIDAK** | ux observability/state sendiri |

**Inti bypass:** MissionUXService memotong **seluruh rantai hulu** (Manager→Registry→Discovery→Contract) untuk **admission capability**, dan menggantinya dengan **whitelist hardcoded** (`_AI_CAPABILITIES` + `_resolve_capability`) di application service. Itulah **architectural violation** yang Van tunjuk: admission capability seharusnya dievaluasi oleh Reference Runtime (Capability Manager → Discovery Resolver), bukan oleh service UX.

---

## 5. Temuan, Severity, Rekomendasi

### F-1 (CRITICAL) — Admission capability yang dipakai aplikasi = whitelist lokal, bukan chain canonical
- **Temuan:** `service.py` memakai `_AI_CAPABILITIES` + `_resolve_capability` (whitelist hardcoded) untuk menentukan operation admissible. Reference Runtime `CapabilityManagerService`/`DiscoveryResolver` tidak dipanggil.
- **Dampak:** capability truth tidak sinkron dengan canonical chain; tiap capability harus di-hardcode ulang di service UX; LLM candidate diterima/ ditolak oleh logika duplikat yang bisa drift dari authority.
- **Rekomendasi:** wire admission ke Reference Runtime — `MissionUXService` harus bertanya ke `CapabilityManager`/`DiscoveryResolver` (resolve capability) dan memakai `CapabilityDescriptor` canonical, bukan whitelist sendiri. **Hapus `_AI_CAPABILITIES`/`_resolve_capability` sebagai authority; jadikan mereka thin passthrough ke chain canonical.**

### F-2 (HIGH) — Dua keluarga runtime capability tidak pernah bertemu
- **Temuan:** `sam.runtime.*` (Reference, E1-001) lengkap tapi tak dipakai; `sam.execution_runtime.*` + `application/ux` dipakai tapi tanpa capability manager/registry/discovery/contract yang masuk chain. `execution_runtime` punya `execution_capability.py`/`execution_registry.py`/`execution_contract.py` — tapi itu objek `execution_*` ad-hoc, bukan chain canonical (tidak memakai `CapabilityDescriptor`/`DiscoveryResolver`).
- **Dampak:** duplikasi konsep, authority capability ambigu, risiko drift.
- **Rekomendasi:** tentukan satu source of truth (Reference Runtime `sam.runtime`), lalu `execution_runtime`/`application/ux` **meminta** capability ke chain itu (inversion: ux tidak punya whitelist; ia resolve via Reference Runtime).

### F-3 (MEDIUM) — Approval dua sumber
- **Temuan:** ux pakai `ApprovalGate` (`execution_runtime`); Reference Runtime punya `approval_coordinator`. Keduanya hidup berdampingan tanpa wiring.
- **Rekomendasi:** konsolidasi ke satu chain; pastikan approval mission melewati approval coordinator canonical bila Reference Runtime jadi spine.

### F-4 (LOW/INFO) — RuntimeBuilder tanpa konsumen luar
- **Temuan:** `RuntimeBuilder` hanya di-instantiate di `runtime_root/` sendiri. Tidak ada test integrasi yang terbukti memakai chain penuh dari aplikasi.
- **Rekomendasi:** jadikan `runtime_root` composition root yang benar-benar di-wire di startup aplikasi, atau dokumentasikan status reference vs production.

---

## 6. Rekomendasi wiring yang BENAR (arah perbaikan, bukan ADR baru)

1. **Reference Runtime = spine admission.** MissionUXService submit harus: minta operation candidate (LLM) → **resolve via `DiscoveryResolver.resolve(CapabilityRequest)`** → tanam disetujui/disetujui → CapabilityDescriptor. Validator deterministik = Discovery Resolver canonical (LLM tetap candidate).
2. **Hapus whitelist hardcoded sebagai authority.** `_AI_CAPABILITIES`/`_resolve_capability` di service.py **tidak boleh** jadi otoritas admission; ganti dengan call ke chain canonical. (INI YANG MEMBUAT ADR-007 IMPLEMENTASI JADI VIOLATION — karena ia menguatkan whitelist lokal, bukan beralih ke chain.)
3. **Capability advertisement dari registry.** `_AI_CAPABILITIES` diambil dari `CapabilityManager.list_capabilities()`/`is_discoverable()`, bukan list literal.
4. **Bounded context tetap.** MissionUXService tetap thin; ia meminta, bukan memutus. Executor `runner.run_mission` tetap satu-satunya jalur eksekusi, tapi **opsi operation yang sah berasal dari hasil resolve chain** — runner `startswith` prefix yang toleran menjadi masalah terpisah (technical debt, hardening terpisah).
5. **Konsolidasi approval.** Pilih satu authority approval (execution_runtime `ApprovalGate` yang sudah teruji M10 vs `approval_coordinator` Reference) dan wire konsisten.

---

## 7. Artefak terkait & scope (tidak diubah di audit ini)
- Audit ini **tidak mengubah kode**. Hanya pemetaan + rekomendasi arah.
- AD-ENG-007 proposal & implementasi working-tree: **STOPPED** (belum di-commit). Whitelist `_resolve_capability` akan di-review terhadap rekomendasi F-1 (batal sebagai authority, ganti resolve chain) — keputusan wiring menunggu Van.
- Dokumen: `docs/engineering/decisions/AD-ENG-007_Invalid_Unresolved_Intent_Safety_Boundary_Proposal.md`.
