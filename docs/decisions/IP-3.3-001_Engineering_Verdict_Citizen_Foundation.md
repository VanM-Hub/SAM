# IP-3.3-001 Engineering Verdict - Citizen Foundation

- **Mission**: MISSION-3.3 - Citizen Ecosystem
- **Implementation Package**: IP-3.3-001
- **Architecture Order**: AO-3.3-001
- **Lead Engineer Directive**: ED-3.3-001
- **Status**: **IMPLEMENTATION COMPLETE** (foundation layer, registry/discovery only)
- **Tanggal**: 2026-08-09
- **Oleh**: Lead Implementation Engineer (ZARA)

---

## Ringkasan

IP-3.3-001 membangun **Citizen Foundation** - abstraksi konstitusional bersama
yang mendasari seluruh peserta platform (Runtime, Provider, Workflow, Mission,
Policy, Capability, dan jenis Citizen lain). Bukan sekadar registry baru; ini
pergeseran pusat arsitektur dari *Runtime-centric* menjadi *Citizen-centric*:
Runtime menjadi **salah satu jenis Citizen**, bukan entitas istimewa. Konsisten
dengan prinsip **Citizen Equality**.

Bounded context baru `src/sam/citizen/` dibangun terpisah dari
`autonomy_runtime/` (Citizen bukan Runtime; Runtime akan menjadi konsumen model
Citizen). Fokus engineering IP-3.3-001: **identitas, registrasi, deskripsi,
capability, lifecycle, discovery, compliance**. Belum ada kolaborasi antar-
citizen (federation/negotiation/collaboration/compatibility/ecosystem
intelligence - di tahap berikutnya).

## Pergeseran Pusat Arsitektur

```
SEBELUM (Runtime-centric):          SESUDAH (Citizen-centric):
  Mission                              Mission
     |                                    |
  Governance                            Governance
     |                                    |
  Runtime                                 |
                                          v
                                        Citizen
                                           |
                    +----------------------+-----------------+
                    v          v          v          v          v
                 Runtime   Provider   Workflow   Mission   Policy/Capability
```

Runtime tidak lagi entitas istimewa; ia memakai model Citizen bersama.

## Deliverables (WP-01 s/d WP-10)

| WP | Capability | Output | Status |
|---|---|---|---|
| WP-01 | Citizen Identity Model | `cit/identity/models.py` - `CitizenIdentity` (immutable, unique) | COMPLETE |
| WP-02 | Citizen Registry | `cit/registry/registry.py` - `CitizenRegistry` (indexed, unique) | COMPLETE |
| WP-03 | Citizen Descriptor | `cit/descriptor/descriptor.py` - `CitizenDescriptor` (completeness) | COMPLETE |
| WP-04 | Citizen Capability Model | `cit/capability/models.py` - `CitizenCapability`, `CapabilityContract` | COMPLETE |
| WP-05 | Citizen Discovery Engine | `cit/discovery/engine.py` - `CitizenDiscoveryEngine` (deterministic) | COMPLETE |
| WP-06 | Citizen Health Model | `cit/health/models.py` - `CitizenHealth`, `CitizenHealthAnalyzer` | COMPLETE |
| WP-07 | Citizen Lifecycle Model | `cit/lifecycle/models.py` - `CitizenLifecycle` (proposal-only) | COMPLETE |
| WP-08 | Citizen API | `cit/api/citizen.py` - `CitizenAPI` (read-only facade) | COMPLETE |
| WP-09 | Citizen Compliance | `cit/compliance/checker.py` (10 check) | COMPLETE |
| WP-10 | Integration & Certification | `tests/citizen/test_wp10_certification.py` (22 tests) | COMPLETE |

## Package Structure

```
src/sam/citizen/
|-- identity/     models.py       CitizenIdentity (immutable, equality)
|-- registry/     registry.py     CitizenRegistry (unique, indexed)
|-- descriptor/   descriptor.py   CitizenDescriptor (completeness)
|-- capability/   models.py       CitizenCapability, CapabilityContract
|-- discovery/    engine.py       CitizenDiscoveryEngine (contract-driven)
|-- health/       models.py       CitizenHealth, CitizenHealthAnalyzer
|-- lifecycle/    models.py       CitizenLifecycle (proposal, not mutation)
|-- api/          citizen.py      CitizenAPI (read-only facade)
|-- compliance/   checker.py      10 checks (CIT-01..10)
`-- __init__.py   CitizenAPI, CitizenSummary
```

## Engineering Constraints Compliance

### SHALL (terpenuhi)
| Requirement | Verifikasi |
|---|---|
| citizen equality | identity equal untuk semua kind; API by_kind; no privileged (CIT-08) |
| immutable identity | `frozen=True` + semantic id (CIT-02) |
| registry discovery | `CitizenRegistry` indexed (by id/kind/name) (CIT-03) |
| contract-driven lookup | `DiscoveryQuery(contract=...)` (CIT-07) |
| deterministic discovery | no random/time; hasil ter-urut (CIT-07) |
| explainable metadata | descriptor `basis` + `validity()` (CIT-04) |
| capability-first modeling | `CitizenCapability` + contract (CIT-05) |

### SHALL NOT (tidak terjadi)
| Forbidden | Verifikasi |
|---|---|
| privileged citizen | CIT-08 (no `is_privileged` impl) |
| runtime special-case | citizen/ tidak import runtime (diverifikasi terpisah) |
| governance mutation | CIT-09 (no authority acquisition) |
| authority acquisition | CIT-09 |
| hidden registration | CIT-10 (register eksplisit) |
| implicit discovery | discovery butuh eksplisit criteria (test no_implicit) |

## Dua Engineering Risk (dijaga sejak awal)

1. **Citizen != Runtime** - Diverifikasi: `citizen/` TIDAK memiliki dependensi
   `sam.runtime` / `sam.autonomy_runtime` (scan import bersih). Model Citizen
   mendahului dan tidak bergantung pada Runtime. Dependency yang benar:
   `Citizen <- Runtime` (Runtime memakai/mengonsumsi model Citizen).

2. **Registry != Authority** - Registry/discovery/API hanya menyimpan identitas,
   melakukan discovery, menyediakan metadata. TIDAK ada `activate_citizen`,
   `deactivate_citizen`, `transition_lifecycle`, `run_capability` di Citizen API
   (diverifikasi oleh test `test_exit_criteria_end_to_end`). Lifecycle hanya
   `propose_transition` (proposal), penerapan tetap wewenang authorized
   actor/governance.

## Test Evidence

| Suite | Jumlah | Hasil |
|---|---|---|
| `tests/citizen/test_wp10_certification.py` (IP-3.3-001) | 22 | **22 passed** |
| `tests/autonomy_runtime/` (IP-3.2-001..005) | 91 | **91 passed** (tanpa regresi) |
| `tests/governance_intelligence/` (MISSION-3.1) | 122 | **122 passed** (tanpa regresi) |
| Compliance Citizen | 10 | **10/10 passed** |
| Import check seluruh modul citizen/ | 18 | **18/18 OK** |
| Dependensi citizen/ -> runtime | - | **Bersih (tidak ada)** |
| ASCII-clean seluruh file citizen | - | **0 non-ascii** |

## Exit Criteria Verification

Platform kini mampu menjawab deterministik:
- [x] **Citizen apa saja yang tersedia?** -> `CitizenAPI.all()` / `count` / `kinds()`
- [x] **Capability apa yang dimiliki setiap citizen?** -> `capabilities_of(id)`
- [x] **Apa status kesehatannya?** -> `health_of(id)` / `CitizenHealth`
- [x] **Apa lifecycle-nya?** -> `lifecycle_of(id)` / `CitizenLifecycle`
- [x] **Bagaimana citizen ditemukan?** -> `discover(contract=...)` (deterministik)
- [x] **Apa kontrak yang didukung?** -> `contracts_of(id)`
- [x] **Apakah citizen compliant?** -> `compliance_check` (10/10)
- [x] **Mengapa citizen dianggap valid?** -> `validity(id)` -> (valid, basis explainable)

Tanpa memperkenalkan mekanisme kolaborasi antar-citizen (federation dll).

## Object-Oriented Design Notes

```python
# identity: immutable semantic id (deterministic, reconcilable)
rt = CitizenIdentity.new("runtime", "sam-runtime", version="1.0")

# registry: unique identity (duplicate -> RegistryConflictError)
reg = CitizenRegistry()
reg.register(rt)  # explicit registration (no hidden)

# descriptor: contract-driven, explainable
d = build_descriptor(rt, contracts=("health",), capabilities=("observe",))

# discovery: deterministic & contract-driven
eng = CitizenDiscoveryEngine(reg)
found = eng.discover(DiscoveryQuery(contract="health"))  # no implicit

# lifecycle: proposal only, never mutation
ok, why = analyzer.propose_transition(lc, "active")  # requires authorized actor

# api: read-only facade answering citizen questions
api = CitizenAPI(reg, descriptors=..., healths=..., lifecycles=...)
```

## Batas Scope (Fase Berikutnya, BUKAN IP-3.3-001)

- **Federation** - kolaborasi antar-citizen lintas domain/organisasi
- **Negotiation** - tawar-menawar kontrak/capability antar citizen
- **Collaboration** - koordinasi eksekusi bersama antar citizen
- **Compatibility** - verifikasi kesesuaian kontrak lintas versi/implementasi
- **Ecosystem Intelligence** - analisis kesehatan ekosistem secara kolektif

Ini semua membutuhkan Architecture Order sendiri dan bukan bagian Citizen
Foundation.

## Catatan Baseline CI

`tests/citizen/` saat ini **belum menjadi bagian baseline CI** (Opsi A,
`ci.yml` tidak diubah). Perluasan baseline = bagian Program A (bertahap +
persetujuan). Test ter-commit namun belum dieksekusi CI. IP-3.3-001 belum
dinyatakan Operational sampai baseline diperluas + review Chief Architect.

## Fase MISSION-3.3

**Citizen Foundation (IP-3.3-001) -> Federation (IP-3.3-002+) -> ...**

Fondasi Citizen yang equal & tidak berotoritas kini berdiri - abstraksi
konstitusional bersama yang akan menaungi semua peserta platform. Runtime,
Provider, Workflow, Mission, Policy, Capability semuanya citizen yang setara.
Ini menjadi dasar penting bagi Federation pada tahap berikutnya.
