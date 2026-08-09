# IP-3.5-003 Engineering Verdict - Citizen Experience

- **Mission:** MISSION-3.5 - Platform Experience (AO-ENG-001)
- **IP:** IP-3.5-003 - Citizen Experience
- **Status:** IMPLEMENTATION COMPLETE (engineering)
- **Tanggal:** 2026-08-09
- **Engineering Authority:** AO-ENG-001
- **Bounded context:** `src/sam/platform/` (lanjutan IP-3.5-001/002)

---

## Ringkasan

IP-3.5-003 membangun **Citizen Experience**: pandangan terpadu citizen +
federation di dalam platform. Citizen Workspace, Federation Workspace,
Collaboration Workspace, Compatibility Workspace, dan Certification Workspace
disuguhkan melalui satu facade read-only (CitizenExperienceAPI).

Prinsip guardrail MISSION-3.5 dikunci keras: platform ***MUST NOT modify
citizens***. Citizen Experience ***presents*** citizen/federation; ia ***never
runs*** action citizen/federation. Tidak ada approval citizen, tidak ada
start collaboration, tidak ada negosiasi, tidak ada issue/revoke certification,
tidak ada join/leave federation.

## Work Package delivery

| WP | Deliverable | Modul | Status |
|----|-------------|-------|--------|
| WP-17 | Citizen Workspace | `citizen_workspace.py` (CitizenInput, CitizenWorkspaceView) | COMPLETE |
| WP-18 | Federation Workspace | `citizen_workspace.py` (FederationInput, FederationWorkspaceView) | COMPLETE |
| WP-19 | Collaboration Workspace | `collaboration_workspace.py` | COMPLETE |
| WP-20 | Compatibility Workspace | `collaboration_workspace.py` (assess_compatibility) | COMPLETE |
| WP-21 | Certification Workspace | `collaboration_workspace.py` (CertificationStatus) | COMPLETE |
| WP-22 | Unified Citizen/Federation UX | `citizen_api.py` (CitizenExperienceAPI) | COMPLETE |
| WP-23 | Citizen Compliance | `compliance.py` (CX-01..10) | COMPLETE |
| - | Package re-export | `__init__.py` (CX exports) | COMPLETE |
| - | Certification suite | `tests/platform/test_wp30_certification.py` | COMPLETE |

## Guardrail compliance (CX-01..10)

Kompliance Citizen Experience (`citizen_compliance_check`, group CX) memindai
modul citizen untuk forbidden action tokens dan marker presentasi:

- Semua modul citizen di-scan untuk token aksi yang dilarang
  (`approve_citizen`, `modify_citizen`, `start_collaboration`,
  `issue_certification`, `certify`, `negotiate`, `join_federation`,
  `admit_member`, `trust_member`, dsb.)
- Min. 1 marker presentasi (snapshot/view/manifest/compat/status) wajib ada
- Hasil: **CX 4/4 ALL PASS** (forbidden-token = none)

## Test evidence (IP-3.5-003)

| Suite | Hasil |
|-------|-------|
| `tests/platform/test_wp30_certification.py` | **14 passed** |
| `tests/platform/` (kumulatif 001+002+003) | **50 passed** |
| Citizen Compliance CX | **4/4 passed** |
| Mission Compliance MEX | **5/5 passed** |
| Platform Compliance PEX | **18/18 passed** |
| citizen regression | **157 passed** |
| autonomy_runtime regression | **91 passed** |
| governance_intelligence regression | **122 passed** |

## Architecture Boundary Checklist (self-verification)

- **Architecture Boundary:** PASS - hanya `src/sam/platform/` yang bertambah
  (citizen_workspace, collaboration_workspace, citizen_api, compliance CX).
  Tidak mengubah citizen/federation internal.
- **Runtime Responsibility:** PASS - CitizenExperienceAPI tidak memanggil
  action citizen/federation; murni agregasi & penyajian.
- **Constitutional Boundary:** PASS - kompatibilitas & sertifikasi bersifat
  presentational (penilaian/status), bukan penerbitan otoritas.
- **Capability Boundary:** PASS - platform **menerima** data citizen dari luar,
  tidak meniru/menduplikasi business logic citizen runtime.
- **Deterministic Behaviour:** PASS - tanpa RNG/time; seluruh view/assessment
  deterministik & diurutkan.
- **Auditability:** PASS - setiap assessment membawa rationale; certification
  membawa criteria & verdict.
- **Explainability:** PASS - compatibility rationale eksplisit (sebutkan
  capability yang kurang).
- **Test Coverage:** PASS - 14 test mencakup seluruh WP-17..23 + presentation-
  passive exit check.
- **ASCII-clean:** PASS (0 non-ascii).
- **Python 3.8 compat:** PASS (tanpa walrus / PEP604).

## Design notes

- **Input-driven:** CitizenExperienceAPI **tidak mengimpor** citizen internal
  secara deep. Data citizen/federation/collaboration/certification **diberikan**
  sebagai input (dataclass immutable) dari governed capability API/caller.
- **Platform tidak memegang otoritas apa pun atas citizen.** Tidak ada path
  code untuk approve/modify/start/issue/negotiate/join - diverifikasi oleh
  compliance CX + unit test `test_citizen_api_has_no_action_verbs`.
- **Compatibility = penilaian deklaratif:** `assess_compatibility` membandingkan
  capability source vs target terhadap required set; deterministik; membawa
  rationale. Bukan negosiasi/execution.
- **Immutable DTO:** CitizenInput, FederationInput, CompatibilityAssessment,
  CertificationStatus, CitizenSnapshot semuanya frozen.
- **Naming:** facade diberi nama `CitizenExperienceAPI` di platform untuk
  menghindari konflik nama dengan `CitizenAPI` milik capability citizen.

## Evolution ladder

```
MISSION-3.5
  IP-3.5-001 Platform Workspace   COMPLETE (fondasi)
  IP-3.5-002 Mission Experience   COMPLETE
  IP-3.5-003 Citizen Experience   <-- INI (COMPLETE)
  IP-3.5-004 Explainability Experience (unified evidence graph) [next]
  IP-3.5-005 Platform Integration (e2e + regression + certification + report)
```

## Batas yang dijaga

Citizen Experience **menyajikan** citizen & federation - manifest, anggota,
kolaborasi, kompatibilitas, status sertifikasi - tanpa pernah **menjalankan/
memodifikasi** citizen. Foundation immutable. Governance authoritative.
Trust over convenience. Evidence before recommendation.
