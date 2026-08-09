# IP-3.5-004 Engineering Verdict - Explainability Experience

- **Mission:** MISSION-3.5 - Platform Experience (AO-ENG-001)
- **IP:** IP-3.5-004 - Explainability Experience
- **Status:** IMPLEMENTATION COMPLETE (engineering)
- **Tanggal:** 2026-08-09
- **Engineering Authority:** AO-ENG-001
- **Bounded context:** `src/sam/platform/` (lanjutan IP-3.5-001/002/003)

---

## Ringkasan

IP-3.5-004 membangun **Explainability Experience**: satu unified evidence
graph yang menyatukan bukti dari berbagai domain (mission, governance,
runtime, citizen, federation) menjadi satu pandangan koheren yang dapat
dijelaskan. Menyediakan agregasi evidence, penjelasan lintas domain, dan
pelacakan rantai dukungan evidence.

Prinsip: platform ***presents*** evidence graph; ia ***never judges***
evidence. Tidak ada verifikasi, penolakan, penerimaan, expiry, atau
publikasi keputusan evidence dari platform. Evidence DIBERIKAN sebagai input;
platform menghubungkan & menyajikan.

## Work Package delivery

| WP | Deliverable | Modul | Status |
|----|-------------|-------|--------|
| WP-24 | Unified Evidence Graph | `evidence_graph.py` (EvidenceGraph, build_evidence_graph) | COMPLETE |
| WP-25 | Evidence Aggregation | `evidence_graph.py` (aggregate_evidence) | COMPLETE |
| WP-26 | Cross-domain Explainability | `explainability.py` (explain_graph) | COMPLETE |
| WP-27 | Evidence Chain Viewer | `evidence_chain.py` (build_chain, orphaned_evidence) | COMPLETE |
| WP-28 | Explainability API | `explain_api.py` (ExplainabilityAPI) + compliance EX | COMPLETE |
| - | Package re-export | `__init__.py` (EX exports) | COMPLETE |
| - | Certification suite | `tests/platform/test_wp40_certification.py` | COMPLETE |

## Guardrail compliance (EX-01..10)

Kompliance Explainability Experience (`explainability_compliance_check`, group
EX) memindai modul untuk forbidden judgment/verification tokens dan marker
presentasi:

- Semua modul explainability di-scan untuk token yang dilarang
  (`verify_evidence`, `reject_evidence`, `accept_evidence`, `decide`,
  `judge`, `infer_authority`, `grant_authority`, `approve_evidence`,
  `publish_decision`, dsb.)
- Min. 1 marker presentasi (graph/aggregate/summary/chain/snapshot) wajib ada
- Hasil: **EX 5/5 ALL PASS** (forbidden-token = none)

## Test evidence (IP-3.5-004)

| Suite | Hasil |
|-------|-------|
| `tests/platform/test_wp40_certification.py` | **14 passed** |
| `tests/platform/` (kumulatif 001+002+003+004) | **64 passed** |
| Explainability Compliance EX | **5/5 passed** |
| Citizen Compliance CX | **4/4 passed** |
| Mission Compliance MEX | **5/5 passed** |
| Platform Compliance PEX | **22/22 passed** |
| citizen regression | **157 passed** |
| autonomy_runtime regression | **91 passed** |
| governance_intelligence regression | **122 passed** |

## Architecture Boundary Checklist (self-verification)

- **Architecture Boundary:** PASS - hanya `src/sam/platform/` yang bertambah
  (evidence_graph, explainability, evidence_chain, explain_api, compliance
  EX). Tidak mengubah evidence internal/runtime.
- **Runtime Responsibility:** PASS - ExplainabilityAPI tidak memverifikasi/
  menolak/expire evidence; murni agregasi & penyajian graph.
- **Constitutional Boundary:** PASS - tidak ada inferensi/pemberian otoritas;
  graph adalah representasi hubungan, bukan keputusan.
- **Capability Boundary:** PASS - platform **menerima** evidence dari luar,
  tidak meniru business logic evidence runtime.
- **Deterministic Behaviour:** PASS - tanpa RNG/time; graph & chain
  deterministik (sorted), BFS deterministik.
- **Auditability:** PASS - tiap evidence membawa domain/type/status/summary;
  chain & orphan terlacak.
- **Explainability:** PASS - coverage pair lintas domain + summary; sesuai
  misi Explainability Experience.
- **Test Coverage:** PASS - 14 test mencakup seluruh WP-24..28 + presentation-
  passive exit check.
- **ASCII-clean:** PASS (0 non-ascii).
- **Python 3.8 compat:** PASS (tanpa walrus / PEP604).

## Design notes

- **Input-driven:** ExplainabilityAPI **tidak mengimpor** evidence internal
  secara deep. Evidence DIBERIKAN sebagai `EvidenceInput` (dataclass frozen)
  dari governed evidence API/caller.
- **Graph deterministik:** nodes & links di-sort; link hanya dibuat bila
  target evidence benar-benar ada (link ke ghost diabaikan).
- **Chain viewer BFS mundur:** `_chain_path` mencari node pendukung target
  secara BFS deterministik, hasil urut akar->target. Bug chain awal (parent
  mapping) diperbaiki; diverifikasi oleh test `test_chain_direct_support`.
- **Status normalized, bukan judgment:** `status_norm` mengkategorikan label
  (COLLECTED/VERIFIED/dst) untuk tampilan; platform tidak mengubah status
  evidence.
- **Immutable DTO:** EvidenceInput, EvidenceGraph, EvidenceAggregate,
  ExplainabilitySummary, EvidenceChain semuanya frozen.

## Evolution ladder

```
MISSION-3.5
  IP-3.5-001 Platform Workspace   COMPLETE (fondasi)
  IP-3.5-002 Mission Experience   COMPLETE
  IP-3.5-003 Citizen Experience   COMPLETE
  IP-3.5-004 Explainability Experience  <-- INI (COMPLETE)
  IP-3.5-005 Platform Integration (e2e + regression + certification + report)
```

## Batas yang dijaga

Explainability Experience **menyajikan** evidence graph - node, link,
agregasi, coverage lintas domain, rantai dukungan - tanpa pernah
**menilai/memutuskan** evidence. Foundation immutable. Governance
authoritative. Determinism before autonomy. Evidence before recommendation.
