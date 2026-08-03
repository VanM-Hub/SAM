# ADR-007 — Verification Point Placement

Version: 0.1.0

Status: Accepted

Decision Date: 2026-08-03

Author: Chief Architect

Reviewers:

Related ADRs: ADR-000, ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006

Related Documents: CONSTITUTION.md, GOVERNANCE.md, docs/architecture/SAM_ARCHITECTURE.md, docs/design/G0-001_Reference_Runtime_Blueprint.md, docs/specifications/AUDIT_SPECIFICATION.md, docs/specifications/EXECUTION_SPECIFICATION.md, R1-001_Minimal_Reference_Runtime_Design.md

Related Modules:

---

# Purpose

Menentukan secara arsitektural "pada titik mana Verification dilaksanakan" sehingga Reference Runtime tetap deterministik, auditable, dan mempertahankan separation of responsibility sebagaimana ditetapkan oleh Foundation, Specification, dan Blueprint.

---

# Context

- Blueprint (G0-001) menetapkan alur konsep "Approved Execution Flow":

  Mission → Governance check → Approval → Execution → Verification → Audit

  pada level komponen, Runtime didefinisikan dengan tujuh komponen: Citizen Host, Discovery Resolver, Capability Manager, Contract Enforcer, Approval Coordinator, Execution Scheduler, Audit Recorder. Tidak ada komponen terpisah bernama "Verification".

- AUDIT_SPECIFICATION mendefinisikan siklus hidup Audit Record: Recorded → Verified → Archived dan menyatakan Audit "observes and records" serta "does not decide/perform". Audit bertanggung jawab menyediakan traceability (Audit Record harus mereferensi Execution, Approval, Contract, Capability).

- EXECUTION_SPECIFICATION menyatakan Execution "produces operational information that Audit may record" dan bahwa Execution "does not record".

- ADR-004 (Failure Propagation) menegaskan Audit Recorder sebagai titik terminasi propagasi dan prinsip "Audit does not feed back" (tidak ada interaksi tambahan yang ditemukan). R1-001 menegaskan "No additional interaction is invented" dan bahwa Audit tidak mempengaruhi outcome Execution.

- ADR-005 memilih Strict Linear Ordering (Approval-arrival order). ADR-001 memilih Accountable Decision Framework untuk Approval. ADR-006 menetapkan boundary deterministik (Contracts + Registry) untuk akses eksternal.

Semua bukti di atas adalah sumber otoritatif untuk keputusan ini.

---

# Problem Statement

Pada titik mana Verification arsitekturalnya dilakukan agar Runtime tetap deterministik, auditable, dan tanpa melanggar separation of responsibility?

---

# Decision Drivers

Turunan langsung dari evidence (tidak membuat driver baru):

- Determinism — verification tidak boleh mengubah determinisme ordering/hasil Execution (Blueprint; ADR-005; ADR-006).
- Auditability / Traceability — verification harus mendukung Audit Record dengan referensi ke Execution, Approval, Contract, Capability (AUDIT_SPEC).
- Separation of responsibility — Execution tidak boleh diberi tugas recording/verification; Audit tidak boleh mempengaruhi outcome (EXECUTION_SPEC; AUDIT_SPEC; R1-001).
- No additional interaction — tidak boleh menambahkan komponen/authority atau interaksi baru di chain (R1-001; ADR-004).
- Implementation independence — keputusan harus bebas dari bahasa, framework, runtime, atau mekanisme teknis.

---

# Alternatives Considered

Semua alternatif berasal dari bukti yang ada; tidak ditambahkan alternatif baru.

## Alternative A — Embedded Verification within Execution (in-chain)

Description

- Menempatkan tugas verifikasi sebagai perilaku yang dijalankan oleh Execution Scheduler atau sebagai tahap tambahan di dalam komponen Execution.

Strength

- Verification dapat terjadi segera pada saat hasil tersedia; integrasi langsung antara produksi hasil dan verifikasi konseptual.

Weakness

- Bertentangan dengan EXECUTION_SPEC yang menyatakan "Execution does not record" dan pemisahan tanggung jawab; menggabungkan performa dan observability.
- Berisiko memodifikasi determinisme (jika verifikasi menolak/ubah outcome) dan menambah interaksi baru.

Consistency

- Tidak konsisten dengan AUDIT_SPEC (Audit memiliki lifecycle Verified) dan dengan R1-001 (no additional interaction). Akan melanggar separation of responsibility.

Impact

- Memerlukan perubahan pada Execution SPEC atau ADR lama; berpotensi memperkenalkan authority baru atau interaksi balik.

## Alternative B — Verification as Audit-observed State Transition (out-of-chain) [Selected]

Description

- Menafsirkan "Verification" sebagai fase/konfirmasi dalam siklus hidup Audit Record (Recorded → Verified). Verification dilaksanakan oleh Audit concern (Audit Recorder / Audit Engine) sebagai observasi terhadap Execution outcomes, menggunakan referensi Contract + Registry untuk memastikan traceability. Verification tidak mengubah hasil Execution dan tidak memberi umpan balik ke chain operasional.

Strength

- Konsisten dengan AUDIT_SPEC (lifecycle Verified), EXECUTION_SPEC (Execution hanya menghasilkan informasi), ADR-004 dan R1-001 (Audit observes, no feedback). Menjaga determinism dan separation of responsibility.

Weakness

- Verification terjadi sebagai tindakan observasi setelah hasil dihasilkan; jika proses verifikasi menemukan definisi failure, itu menghasilkan defined failures yang harus tercermin di Audit (mis. Missing Reference). Verification tidak mencegah outcome yang tidak terverifikasi sebelumnya terjadi.

Consistency

- Sepenuhnya konsisten dengan Foundation, Specification, Blueprint, dan ADR-000..ADR-006.

Impact

- Tidak membutuhkan perubahan ADR atau Specification; menempatkan beban verifikasi pada Audit Engines dan proses yang mengonsumsinya.

## Alternative C — Verification as Separate Gate/Authority Component

Description

- Menambahkan komponen arsitektural baru (mis. Verification Gate) yang memeriksa hasil Execution sebelum Audit dan dapat mempengaruhi outcome (mis. menolak, menunda, atau memodifikasi hasil).

Strength

- Verification terjadi sebelum finalisasi hasil; dapat mencegah tidak-terverifikasi outcome terdistribusi.

Weakness

- Menambahkan authority/komponen baru yang tidak ada di Blueprint; bertentangan dengan "No additional interaction is invented" (R1-001). Mengubah alur dan mungkin Specification; melanggar prinsip bahwa Audit tidak mempengaruhi outcome.

Consistency

- Tidak konsisten dengan Blueprint dan Specification; akan memerlukan perubahan ADR/Specification.

Impact

- Membutuhkan ADR/Specification baru dan kemungkinan perubahan pada ADR-000..ADR-006; memperkenalkan domain/authority baru.

---

# Decision

Diterima: Alternative B — Verification dilaksanakan sebagai observasi Audit yang terefleksi sebagai transisi state pada Audit Record (Recorded → Verified). Verification bukan komponen baru; ia adalah fase dalam siklus hidup Audit Record dan berlangsung tanpa memberikan umpan balik pada Execution.

Keputusan ini memenuhi semua ketentuan: berbasis evidence, implementation-independent, tidak menambah authority, tidak mengubah baseline, dan tidak memerlukan perubahan ADR lain.

---

# Architectural Rationale

Referensi bukti dan hubungan ke tingkat otoritas:

- Constitution / Governance: Kebijakan arsitektural dan pembagian tanggung jawab diturunkan dari Governance dan Constitution; keputusan ini tidak menambah authority baru dan menghormati batas-batas kewenangan.

- Architecture / Specification: SPECIFICATION (EXECUTION_SPEC, AUDIT_SPEC) memisahkan peran Execution dan Audit. Execution menghasilkan observable outcome; Audit memiliki lifecycle yang mencakup Verified. Keputusan ini menempatkan Verification di domain Audit tanpa mengubah spesifikasi yang dibekukan.

- Blueprint (G0-001): Golden Rule menempatkan Verification antara Execution dan Audit; blueprint juga mendefinisikan 7 komponen dan menyatakan bahwa Audit adalah terminal recorder. Keputusan ini menafsirkan Verification sebagai fase observasi yang konsisten dengan posisi blueprint.

- ADR sebelumnya: ADR-001 (Approval model), ADR-005 (Strict Ordering), ADR-004 (Failure Propagation), ADR-006 (External Access Boundaries) semuanya mendukung pemisahan tanggung jawab, determinisme ordering, dan bahwa Audit tidak melakukan feedback. Keputusan ini kompatibel dengan semua ADR-000..ADR-006.

---

# Consequences

## Positive

- Menjaga determinisme: Execution tetap tidak berubah oleh proses verifikasi.
- Mempertahankan separation of responsibility: Execution tidak diberi tugas recording/verification; Audit tetap sebagai observer.
- Memenuhi traceability: Verification sebagai transisi pada Audit Record mendukung referensi ke Execution/Approval/Contract/Capability sebagaimana diatur oleh AUDIT_SPEC.
- Tidak memperkenalkan authority atau komponen baru; baseline tetap utuh.

## Negative

- Verification tidak mencegah terjadinya outcome yang ternyata tidak terverifikasi pada saat terjadi; ketidak-lolosan verifikasi tercatat sebagai defined failures dalam Audit, yang memerlukan proses penanganan yang terpisah (operasional).

## Trade-offs

- Mengorbankan "preventive gating" untuk tetap menjaga prinsip arsitektural no-additional-interaction dan separation of responsibility. Verifikasi bersifat reaktif/observasional bukan pre-emptive.

---

# Impact Analysis

- Framework / Modules: Tidak ada modul baru. Audit Engines dan Audit Recorder diharapkan mengimplementasikan dan melaporkan transisi Recorded→Verified.
- Documentation: Menambahkan ADR ini sebagai decision record; tidak mengubah Specification atau Blueprint.
- Tooling / Users: Implementer Audit Engines perlu memetakan state lifecycle dan melaporkan defined failures sesuai AUDIT_SPEC.

---

# Dependency Impact

Hubungan terhadap ADR-000..ADR-006 (tanpa menciptakan dependency baru):

- ADR-000 (Deployment Topology): Tidak berubah. Deployment topology tidak dipengaruhi.
- ADR-001 (Approval Decision): Approval tetap memutuskan; Verification tidak mengubah proses Approval.
- ADR-002 (Capability Resolution): Resolution tetap sama; Verification hanya mengandalkan referensi yang ditetapkan oleh Contract + Registry.
- ADR-003 (Idempotency): Tidak terpengaruh — Verification memeriksa traceability dan integritas record, bukan idempotency mechanism.
- ADR-004 (Failure Propagation): Konsisten — defined failures terangkat ke Audit (linear propagation) dan Verification dapat mencatat defined failures.
- ADR-005 (Execution Ordering): Execution ordering tetap sesuai Approval-arrival order; Verification tidak mengubah ordering.
- ADR-006 (External Access Boundaries): Verification mengamati hasil melalui boundary deterministik (Contract + Registry) — konsisten.

---

# Implementation Independence

Keputusan ini tidak memilih bahasa, framework, runtime, protocol, database, algorithm, serialization, atau concurrency model. Ia hanya menetapkan lokasi arsitektural (Audit concern / Audit Record lifecycle) untuk Verification.

---

# Out of Scope

- Mekanisme operasional untuk menangani defined failures setelah tercatat (operational playbooks).
- Implementasi Audit Engine, format serialisasi, transport, penyimpanan, atau API.
- Penambahan komponen arsitektural baru.

---

# Risk Assessment

| Dimension | Assessment |
|---|---|
| Probability | Low — keputusan mengikuti pola yang sudah ada di Specification (Verified state ada di AUDIT_SPEC). |
| Impact | Low — tidak mengubah execution flow atau authority. |
| Recoverability | Very High — kesalahan dapat di-tweak di implementasi Audit Engine tanpa mengubah ADR. |
| Blast Radius | Low — mempengaruhi Audit Engines dan proses konsumsi record saja. |
| Reversibility | Very High — ADR dapat di-supersede jika diperlukan. |

---

# Trust Assessment

Evidence:

- G0-001 Reference Runtime Blueprint (Golden Rule; component list)
- AUDIT_SPECIFICATION (Audit Record lifecycle Recorded → Verified; traceability requirements)
- EXECUTION_SPECIFICATION (Execution produces observable info; does not record)
- ADR-004 (Failure Propagation: Audit Recorder termination; Audit does not feed back)
- ADR-005 (Ordering), ADR-001 (Approval model), ADR-006 (External boundary determinism)

Confidence: High — keputusan merupakan konsekuensi langsung dari Specification dan Blueprint.

Unknowns: Operasional handling untuk defined failures berada di luar scope ADR.

---

# Implementation Notes

- Audit Engines / Audit Recorder SHALL implement the Audit Record lifecycle and expose the Recorded → Verified transition.
- Verification is an observation that asserts traceability and consistency; it SHALL be recorded as a lifecycle transition and may include failure codes as defined by AUDIT_SPEC.

---

# Migration Strategy

Because this is the Reference Runtime first ADR for Verification placement: Migration = None.

---

# Success Criteria

Derived from evidence:

- Audit Records include a Verified state and exhibit Recorded → Verified transitions where traceability succeeds.
- Verified records can be traced back to Execution, Approval, Contract, and Capability as required by AUDIT_SPEC.
- No changes required to Execution behavior, Approval ordering, or Specification.

---

# Future Reassessment

Reassess if any of the following occur (derived from evidence):

- AUDIT_SPEC is changed to add feedback or change lifecycle semantics.
- Blueprint is amended to add a dedicated Verification component.
- Any ADR modifies the separation of responsibility between Execution and Audit.

---

# Validation — 8 Audits

## Audit 1 — Problem Coverage

- Cakupan: Apakah ADR ini menjawab pertanyaan arsitektur (satu pertanyaan)?
- Hasil: LULUS — ADR menempatkan Verification sebagaimana ditanyakan (pada Audit Record lifecycle). Problem statement terjawab.

## Audit 2 — Alternative Coverage

- Cakupan: Apakah semua alternatif yang muncul dari evidence dipertimbangkan?
- Hasil: LULUS — Alternative A (in-chain Execution), B (Audit-observed state), C (gate/authority) dibahas; keputusan memilih B.

## Audit 3 — Foundation Compliance

- Cakupan: Apakah keputusan melanggar Foundation/Constitution/Governance?
- Hasil: LULUS — tidak mengubah atau menambah authority; konsisten dengan prinsip separation of responsibility.

## Audit 4 — Specification Compliance

- Cakupan: Apakah keputusan konsisten dengan Specification (AUDIT_SPEC, EXECUTION_SPEC)?
- Hasil: LULUS — memanfaatkan Recorded→Verified lifecycle; Execution tetap hanya menghasilkan informasi.

## Audit 5 — Consistency with ADR-000..ADR-006

- Cakupan: Memeriksa kontradiksi atau kebutuhan mengubah ADR lama.
- Hasil: LULUS — tidak perlu mengubah ADR-000..ADR-006; keputusan kompatibel.

## Audit 6 — Architectural Integrity

- Cakupan: Memeriksa cycle, authority leakage, atau pengenalan domain baru.
- Hasil: LULUS — tidak ada cycle; tidak ada authority leakage; tidak menambah domain baru.

## Audit 7 — Implementation Independence

- Cakupan: Memeriksa bahwa keputusan tidak memilih teknologi atau mekanisme implementasi.
- Hasil: LULUS — keputusan arsitektural dan implementasi-independent.

## Audit 8 — Final ADR Validation

- Cakupan: Validasi akhir terhadap STOP conditions dan kriteria ADR acceptance.
- Hasil: LULUS — STOP conditions tidak aktif (tidak perlu mengubah Foundation/Specification/Blueprint/ADR lama; tidak menambah authority/terminology/domain). ADR siap diterima.

---

# STOP Condition

STOP akan aktif jika diperlukan perubahan pada Foundation, Specification, Blueprint, ADR lama, muncul authority baru, domain baru, atau terminology baru yang mengubah Specification.

Untuk ADR ini: **STOP tidak aktif** — semua tindakan terselesaikan dalam batas evidence yang ditentukan.

---

# Related Documents

- CONSTITUTION.md
- GOVERNANCE.md
- docs/architecture/SAM_ARCHITECTURE.md
- docs/design/G0-001_Reference_Runtime_Blueprint.md
- docs/specifications/AUDIT_SPECIFICATION.md
- docs/specifications/EXECUTION_SPECIFICATION.md
- R1-001_Minimal_Reference_Runtime_Design.md

---

# Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-03 | Chief Architect | Accepted |

---

# Author Checklist

- [x] Problem clearly defined
- [x] Alternatives documented
- [x] Decision justified
- [x] Trade-offs documented
- [x] Risks evaluated
- [x] Trust assessment completed
- [x] Related documents referenced
- [x] Terminology follows GLOSSARY.md
- [x] Consistent with CONSTITUTION.md

---

# Completion Checklist

- [x] Metadata complete
- [x] Cross references validated
- [x] Review completed
- [x] Status updated (Accepted)
- [x] Ready for repository publication
