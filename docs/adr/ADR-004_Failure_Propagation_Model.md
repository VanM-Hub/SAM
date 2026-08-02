# ADR-004 — Failure Propagation Model (C-05)

Version: 0.1.0

Status: Accepted

Decision Date: 2026-08-03

Author: Chief Architect (Project SAM Architecture Decision Making)

Reviewers: — (opened for architectural review)

Related ADRs: ADR-000 (Deployment Topology), ADR-001 (Approval Decision Model, C-03), ADR-002 (Capability Resolution Policy, C-02), ADR-003 (Idempotency Realization Model, C-04)

Related Documents: SPECIFICATION_FREEZE, GOVERNANCE, SAM_ARCHITECTURE, G0-001_Reference_Runtime_Blueprint, R1-001_Minimal_Reference_Runtime_Design, R2-001_ADR_Decision_Process_Definition, R3-002_ADR003_Terminology_Validation

Related Modules: Execution Scheduler (producer), Approval Coordinator (producer), Registry (producer), Audit Recorder (termination), Contract (boundary mechanism, not propagation actor)

---

# Purpose

Mendefinisikan keputusan arsitektur Project SAM tentang **bagaimana failure yang sudah terdefinisi pada satu komponen Runtime dipropagasikan ke komponen berikutnya dalam rantai Runtime** — tanpa melanggar bounded responsibility, tanpa menciptakan mekanisme/coupling baru, dan tanpa mengubah Foundation/Specification/Governance/Canonical Architecture.

ADR ini menjawab **satu** pertanyaan arsitektur (Failure Propagation Model / C-05) dan **tidak** membahas bagaimana tiap komponen menghasilkan failure (sudah didefinisikan di Specification masing-masing), Capability Resolution (ADR-002), Approval mechanism (ADR-001), Idempotency (ADR-003), Ordering/Concurrency (C-01), External Access (C-07), atau Verification Placement (C-08) — semuanya di luar scope.

Ini adalah **keputusan arsitektur** (bukan analisis/audit/proposal) dan dijamin **tidak bertentangan dengan baseline beku** (SPECIFICATION_FREEZE, GOVERNANCE, Specification) dan **tidak bertentangan dengan ADR-000, ADR-001, ADR-002, ADR-003**.

---

# Context

## Mengapa Failure Propagation masih terbuka oleh Specification

- **G0-001 Blueprint C-05** (L158): "Failure propagation — **How a defined failure (Registry / Contract / Approval / Execution) is surfaced to the Audit Recorder while preserving traceability** — Trade-off between strict propagation and graceful degradation." Blueprint menyatakan C-05 sebagai kandidat arsitektural terbuka yang menyangkut **bagaimana failure disurfacing**, bukan bagaimana failure didefinisikan.
- **R1-001 Audit 3 — Component Interaction** (L98-L118): interaksi antar komponen Runtime adalah **rantai linear satu arah** (Citizen → Capability → Registry → Contract → Approval → Execution → Audit), dengan komunikasi linier di mana `who→whom` ditetapkan oleh relationship antar Specification. "No additional interaction is invented (e.g., **Audit does not feed back**; Execution does not bypass Approval; Registry never executes)" — R1-001 L118.
- **R1-001 Audit 2 — Runtime Responsibility** (L69-L92): 10 responsibilities diderivasi, **0 duplicated, 0 missing, 0 new** — setiap komponen memiliki bounded responsibility, termasuk Approval (R5: authorization before execution), Execution (R6: apply only approved operations), dan Audit (R7: make activity traceable).
- **SAM_ARCHITECTURE Approved Execution Flow:** `Mission → Governance check → Approval → Execution → Verification → Audit` — rantai yang mencerminkan arah pergerakan aktivitas, termasuk failure.
- **AUDIT_SPEC Relationship with Execution** (L193): "**Audit observes and records. It has no influence over what Execution produces.**" Dan **AUDIT_SPEC Boundaries** (L181, L213): "Audit only records and provides traceability. It does not decide, execute, define, or govern. It observes and records."
- **GOVERNANCE Runtime Governance:** "Every Runtime shall: own one bounded responsibility, publish capabilities, expose immutable contracts, support certification, expose health, **participate in auditing**" — partisipasi auditing adalah kewajiban seluruh komponen, bukan hanya Audit Recorder.
- **GOVERNANCE Long-Term Governance:** governance "should remain valid regardless of: deployment topology, runtime distribution" — propagation model harus valid regardless of topology (konsisten dengan ADR-000 single cohesive unit).

Karena itu **bagaimana failure dipropagasikan antar komponen tidak pernah ditetapkan** oleh Foundation/Specification — ia adalah salah satu dari delapan Candidate ADR (C-05) yang sengaja dibuka oleh Blueprint, kini diresmikan.

## Posisi C-05 dalam Rantai Keputusan

- **C-05 consumes dari ADR-003:** C-05 mengonsumsi "Execution Conflict" (ADR-003 L234/L308) — label yang telah divalidasi R3-002 sebagai architectural extension, BUKAN entri daftar tertutup spec. ADR-004 TIDAK mendefinisikan ulang "Execution Conflict"; ia mengonsumsi istilah tersebut, yang merupakan properti dari lapisan Execution (C-04), sebagaimana ia mengonsumsi semua defined failure dari Specification.
- **C-05 tidak mempengaruhi C-02/C-03/C-04:** C-05 adalah konsumen dari defined failure — ia tidak mempengaruhi bagaimana approval/resolusi/idempotensi bekerja (R1-002: C-05 influenced by C-02, tidak sebaliknya; R2-002 Output 7: C-02 influences C-05).

## Status fase

Foundation **CLOSED** → Specification **FROZEN** → Architecture Discovery **CLOSED** → ADR Process **DEFINED** (R2-001) → Root ADR-000..003 **ACCEPTED** → **ADR-004: In Progress**.

---

# Problem Statement

**Pertanyaan arsitektur yang harus dijawab:** Setelah suatu defined failure terjadi pada satu komponen Runtime (Registry / Approval / Execution), **bagaimana failure tersebut dipropagasikan secara arsitektural** — sekaligus bagaimana failure berpindah dari komponen produser ke Audit Recorder, apa batas propagasi, dan apa titik terminasi?

Trade-off (dari G0-001 Blueprint C-05) adalah antara **strict propagation** (failure selalu disurfacing ke Audit Recorder) dan **graceful degradation** (sistem tetap beroperasi meskipun ada failure). Masalah ini **objektif** dan dibatasi pada **propagasi arsitektural**; ia bukan masalah *bagaimana* tiap komponen menghasilkan failure (sudah didefinisikan), *bagaimana* failure ditangani secara operasional, atau *bagaimana* recovery dilakukan.

---

# Decision Drivers

Driver berikut **diekstrak dari Foundation/Specification/Blueprint** — hanya yang didukung dokumen:

| Driver | Dukungan dokumen |
|---|---|
| **Separation of responsibility** | GOVERNANCE Runtime Governance: "own one bounded responsibility"; R1-001 L75: tiap responsibility punya satu owner. Komponen yang memproduksi failure bertanggung jawab mempropagasikannya; komponen lain tidak menyerobot. |
| **Determinism** | REGISTRY_SPEC L147/L149: resolusi "SHALL be deterministic." Propagation path harus **deterministik** — failure tidak boleh bercabang atau mengambil rute berbeda tergantung kondisi runtime. |
| **Traceability** | AUDIT_SPEC L124-L133: "Every Audit Record SHALL be traceable back to its originating objects." GOVERNANCE: "participate in auditing." Propagation harus mempertahankan jejak asal failure agar Audit Record dapat dilacak ke komponen produser. |
| **Auditability** | AUDIT_SPEC L66/L72/L86: "Audit records, in a conceptual form, the operational events that have occurred, so that they can be followed back to their origin." Failure yang dipropagasikan harus terekam dalam bentuk yang dapat diaudit. |
| **Bounded responsibility** | GOVERNANCE Runtime Governance; G0-001: "one domain / one owner"; R1-001 L75. Propagation tidak boleh membuat komponen baru yang bertanggung jawab atas propagasi (tidak ada "propagation coordinator"). Setiap komponen hanya mempropagasikan failure **miliknya sendiri**. |
| **Runtime integrity** | R1-001 L118: "No additional interaction is invented (Audit does not feed back; Execution does not bypass Approval; Registry never executes)." Propagation tidak boleh menciptakan jalur baru yang tidak ada di rantai linear. |
| **Implementation independence** | R1-001 L63: batas Runtime "imposes no topology." ADR tidak boleh menuntut mekanisme implementasi; keputusan tetap **arsitektural** — bentuk propagation, bukan mekanisme routing/transport/event bus. |
| **Architectural survivability** | GOVERNANCE Long-Term Governance: governance valid "regardless of deployment topology, runtime distribution." Propagation model harus bertahan terhadap perubahan deployment/distribusi tanpa mengubah keputusan dasar. |

Catatan: driver yang **tidak** didukung dokumen (mis. keyakinan "failure pasti harus di-catch", "graceful degradation selalu lebih baik", "propagation harus asynchronous") **tidak** dipakai sebagai justifikasi.

---

# Alternatives Considered

Alternatif berikut adalah **seluruh alternatif yang dapat didukung oleh dokumen sumber** — dievaluasi terhadap bukti aktual (bukan diciptakan), dengan R3-002 sebagai preseden bahwa outcome ada di berbagai tingkat abstraksi.

## Alternative A — Local Containment (failure berhenti pada komponen produser)

Deskripsi: Setiap komponen Runtime menangani failure-nya sendiri secara lokal. Failure tidak dipropagasikan ke komponen berikutnya atau ke Audit Recorder; setiap komponen bertanggung jawab atas containment failure sendiri.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| G0-001 C-05 (L158) | "How a defined failure is surfaced to the Audit Recorder while preserving traceability" — failure harus **disurfacing**. | **CONTRADICTS A.** Containment berarti failure tidak pernah sampai ke Audit Recorder → melanggar framing C-05. |
| AUDIT_SPEC L137-L139 | "Audit SHALL reflect a defined failure rather than an inconsistent record" — Audit merefleksikan failure. | **CONTRADICTS A.** Jika failure ditahan lokal, Audit tidak bisa merefleksikannya. |
| GOVERNANCE — participate in auditing | "Every Runtime shall: participate in auditing" — ini kewajiban seluruh komponen. | **CONTRADICTS A.** Containment = komponen menahan failure dari Audit = tidak berpartisipasi dalam auditing. |
| R1-001 L104 | Linear causality chain. | **WEAK SUPPORT.** Chain linearnya ada, tapi containment tidak memakai chain ini. |

### Assessment
**TIDAK dipilih.** Container failure dari Audit Recorder bertentangan dengan Blueprint C-05 yang secara eksplisit menyatakan C-05 tentang "surfaced to the Audit Recorder," dengan AUDIT_SPEC (failure harus direfleksikan), dan dengan GOVERNANCE (participate in auditing). Meskipun local containment memiliki daya tarik simplicity, ia **tidak sesuai** dengan mandat arsitektural yang mengharuskan failure tercatat di Audit.

---

## Alternative B — Linear Propagation (failure mengikuti rantai ke Audit Recorder, yang menjadi titik terminasi)

Deskripsi: Setiap defined failure yang dihasilkan oleh satu komponen Runtime dipropagasikan **ke depan mengikuti rantai linear** (Registry → Approval → Execution → Audit). Komponen produser bertanggung jawab mempropagasikan failure-nya sendiri ke komponen berikutnya dalam chain. **Propagation tidak menciptakan jalur baru** — ia memanfaatkan jalur interaksi yang sudah didefinisikan oleh R1-001. **Audit Recorder = titik terminasi** ("Audit does not feed back" / "no influence over what Execution produces").

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| R1-001 L104 | "Interaction is a **linear causality along the chain**; the only cross-boundary mechanism is Contracts + Registry." | **SUPPORTS B.** Propagation mengikuti chain yang sudah ada — tidak menciptakan jalur baru. |
| R1-001 L118 | "**No additional interaction is invented** (e.g., Audit does not feed back; Execution does not bypass Approval; Registry never executes)." | **SUPPORTS B.** Linier ke depan sepanjang chain, tidak ada feedback loop, tidak ada bypass. |
| R1-001 L134 I3 | "**Audit does not affect outcome** — 'Audit does not affect the outcome of Execution'; 'Audit has no influence over what Execution produces.'" | **SUPPORTS B.** Audit = terminasi — failure direkam oleh Audit, tidak dipropagasikan lebih jauh. |
| AUDIT_SPEC L193 | "Audit observes and records. It has no influence over what Execution produces." | **SUPPORTS B.** Audit = terminal observer — titik akhir propagasi. |
| AUDIT_SPEC L181/L213 | "Audit only records and provides traceability. It does not decide, execute, define, or govern. It observes and records." | **SUPPORTS B.** Audit bukan propagation actor (tidak meneruskan). |
| SAM_ARCHITECTURE Approved Execution Flow | `Mission → Governance check → Approval → Execution → Verification → Audit` — rantai arah aktivitas unidireksional. | **SUPPORTS B.** Arah rantai = arah propagasi (ke depan). |
| APPROVAL_SPEC L146 | "The Approval process SHALL return a defined failure rather than an unintended decision." | **SUPPORTS B.** Defined failure adalah milik komponen produser; ia dipropagasikan ke depan. |
| REGISTRY_SPEC L166 | "The Registry SHALL return a defined failure instead of silently returning an invalid result." | **SUPPORTS B.** Registry's defined failures dipropagasikan ke depan dalam chain. |
| EXECUTION_SPEC L161-L163 | 6 defined failures; "All failures are observable and defined by this specification." | **SUPPORTS B.** Defined failure Execution (termasuk Execution Conflict) dipropagasikan ke Audit. |
| ADR-003 L277 | "defined failure baru (atau sub-tipe dari Execution Failure yang sudah ada di EXECUTION_SPEC L150-L163)" | **SUPPORTS B.** Execution Conflict = bagian dari defined failure Execution yang dipropagasikan. |
| R3-002 Verdict B | "Execution Conflict = architectural extension, BUKAN entri daftar tertutup spec." | **SUPPORTS B.** C-05 mengonsumsi istilah ini sebagai label arsitektural, bukan mendefinisikan ulang. |

### Advantages
- **Separation of responsibility:** setiap komponen hanya mempropagasikan failure yang ia produksi sendiri — tidak ada komponen yang mempropagasikan failure milik komponen lain.
- **Determinism:** propagation path tunggal dan deterministik — tidak ada percabangan, tidak ada routing — mengikuti chain yang sudah ditetapkan.
- **Traceability & auditability:** failure sampai ke Audit Recorder dengan jejak asal yang utuh — memenuhi GOVERNANCE "participate in auditing" dan AUDIT_SPEC Traceability Rules.
- **Bounded responsibility:** tidak menciptakan komponen/authority baru (tidak ada "propagation coordinator").
- **Runtime integrity:** tidak menciptakan jalur interaksi baru — memanfaatkan chain yang sudah didefinisikan.
- **Implementation independence:** bentuk propagation, bukan mekanisme — tidak menuntut routing/transport/event bus spesifik.
- **Architectural survivability:** linear chain valid regardless of deployment topology (GOVERNANCE Long-Term Governance).

### Disadvantages
- Tidak menyediakan **graceful degradation** secara eksplisit (failure dipropagasikan, tidak di-recover di tengah chain) — namun graceful degradation adalah **mekanisme implementasi** yang berada di luar scope ADR arsitektural.
- Tidak mengatur **failure batching** atau **failure prioritization** — namun itu adalah mekanisme implementasi (out of scope).

### Assessment
**Dipilih** (dipilih oleh Chief Architect sebagai keputusan proses). Paling **selaras dengan kumpulan dokumen**: linear propagation memanfaatkan rantai yang sudah ada (R1-001), menghormati terminasi di Audit Recorder (AUDIT_SPEC L193), menjaga separation of responsibility (setiap komponen hanya mempropagasikan failure-nya sendiri), deterministik (satu arah, tidak bercabang), dan traceable (jejak asal utuh). **Tidak menciptakan komponen/authority/interaksi baru.**

---

## Alternative C — Central Propagation Coordinator (koordinator sentral yang mengelola propagasi)

Deskripsi: Sebuah komponen/authority baru bertanggung jawab mengumpulkan failure dari semua komponen Runtime dan mendistribusikannya ke Audit Recorder.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| R2-002 (C-02/C-03/C-04/C-06 = A-Certified) | Komponen Certified independent dan atomic — setiap komponen = satu keputusan arsitektural. | **CONTRADICTS C.** Koordinator sentral = komponen ke-8 = melanggar arsitektur 7 komponen. |
| R1-001 L75 | 10 responsibilities derived; 0 duplicated; 0 missing; 0 new. | **CONTRADICTS C.** Koordinator sentral = responsibility baru. |
| R1-001 L118 | "No additional interaction is invented." | **CONTRADICTS C.** Koordinator sentral = interaksi baru. |
| GOVERNANCE Runtime Governance | "own one bounded responsibility." Koordinator sentral = responsibility tambahan. | **CONTRADICTS C.** Responsibility propagation ada pada komponen produser, bukan pada koordinator baru. |

### Assessment
**TIDAK dipilih. Tidak ada bukti** di dokumen Federation yang mendukung keberadaan Central Propagation Coordinator. Menambah komponen/authority baru bertentangan dengan arsitektur 7 komponen (SPECIFICATION_FREEZE), bounded responsibility, dan R1-001 "no additional interaction." Semua evidence menolak C.

---

## Alternative D — Contract-Driven Propagation (propagation mengikuti batas Contract)

Deskripsi: Propagation failure terjadi hanya melalui Contract boundary — failure dipropagasikan hanya saat ada interaksi Contract antar komponen, bukan mengikuti seluruh chain linear.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| R1-001 L104 | "the only cross-boundary mechanism is Contracts + Registry." Contract + Registry = mekanisme lintas batas. | **PARTIAL SUPPORT.** Contract adalah boundary mechanism — tapi bukan propagation **actor**. |
| R1-001 L113-L115 | Interaction triggers: "Contract Enforcer → Approval Coordinator **before any operation**" / "Approval → Execution **only after decision**" / "Execution → Audit **after execution produces activity**." | **PARTIAL SUPPORT.** Ada trigger interaksi, tapi Contract bukan aktor propagasi. |
| EXECUTION_SPEC | Execution menghasilkan failure sendiri (6 defined failures + Execution Conflict), bukan via Contract. | **CONTRADICTS D.** Failure Execution tidak dihasilkan di batas Contract — ia dihasilkan di dalam Execution. |
| AUDIT_SPEC L193 | Audit = terminal untuk Execution. Jika propagasi hanya saat Contract interaction, failure Execution bisa terlewat. | **WEAK SUPPORT.** |

### Assessment
**TIDAK dipilih.** Contract adalah **boundary mechanism**, bukan propagation **actor**. Alternative D mengidentifikasi dimensi yang benar (propagation tidak boleh melintasi batas sembarang), tetapi tidak cukup sebagai model propagasi utama — failure tidak selalu terjadi di batas Contract (Execution menghasilkan failure internal). D adalah **prinsip pendukung** (propagation hanya melalui chain yang ada), bukan keputusan terpisah.

---

# Decision

Chief Architect **telah memilih Alternative B** sebagai keputusan arsitektur ADR-004.

**Keputusan (exact wording):** Secara arsitektural, **failure yang terdefinisi pada satu komponen Runtime dipropagasikan ke depan mengikuti rantai linear Runtime (Registry → Approval → Execution → Audit), dari komponen produser ke Audit Recorder yang menjadi titik terminasi propagasi**. Setiap komponen bertanggung jawab **hanya** atas propagasi failure yang ia produksi sendiri. Audit Recorder mencatat dan tidak meneruskan (no feedback loop, no influence on outcome). Propagation tidak menciptakan jalur interaksi baru — ia memanfaatkan chain yang sudah didefinisikan oleh R1-001 Component Interaction.

Yang **bukan** bagian keputusan ini:
- **Bukan** mendefinisikan **bagaimana** setiap komponen menghasilkan failure (sudah didefinisikan di Specification masing-masing — REGISTRY_SPEC L164-L173, APPROVAL_SPEC L142-L155, EXECUTION_SPEC L150-L163, AUDIT_SPEC L137-L150).
- **Bukan** mendefinisikan mekanisme implementasi (bukan routing, transport, event bus, callback, exception, error channel, message passing, atau failure serialization format).
- **Bukan** mendefinisikan recovery / retry / graceful degradation — itu adalah mekanisme implementasi.
- **Bukan** mendefinisikan failure prioritization atau failure batching.
- **Bukan** membahas failover, circuit breaker, timeout, retry policy, atau operational resilience.
- **Bukan** authority baru: ADR ini adalah **kanal pencatatan** di bawah Specification beku (R2-001 Audit 5; G1a/F1a).

Keputusan ini **tidak menciptakan satu pun komponen, authority, atau interaksi baru.** Ia hanya menetapkan **bentuk propagation** dari defined failure yang sudah ada, mengikuti chain yang sudah didefinisikan.

---

# Architectural Rationale

Keputusan ini terhubung ke Constitutional/Governance/Specification/Blueprint sebagai berikut:

- **Constitution (bounded responsibility & integrity):** Linear propagation menghormati bounded responsibility — setiap komponen mempropagasikan hanya failure yang ia produksi sendiri, tidak menyerobot failure milik komponen lain. Tidak menciptakan komponen/authority baru. Determinism (REGISTRY_SPEC L147/L149) terjaga karena propagation path tunggal dan deterministik.
- **Governance (lower never contradict higher):** Propagation model tidak mengubah kewajiban "participate in auditing" (GOVERNANCE Runtime Governance) — semua komponen berpartisipasi dengan mempropagasikan failure ke depan. GOVERNANCE Long-Term Governance menyatakan governance valid "regardless of deployment topology" — model linear valid regardless of topology.
- **Specification (observable failures & defined boundaries):** Setiap Specification mendefinisikan failure yang harus dikembalikan (REGISTRY L164-L173: Citizen missing/Capability not found/Descriptor corrupted/Version not compatible; APPROVAL L142-L155: Approval Conflict + defined states; EXECUTION L150-L163: 6 defined failures + Execution Conflict via ADR-003 L277; AUDIT L137-L150: Broken Traceability/Incomplete Record/Invalid Record/Duplicate Record). Linear propagation memastikan failure-failure ini **disurfacing ke Audit Recorder** yang merefleksikannya (AUDIT_SPEC L137-L139).
- **Blueprint (C-05):** Konsisten dengan C-05 *"How a defined failure is surfaced to the Audit Recorder while preserving traceability"* — linear propagation menjawab "how" (mengikuti chain, dari produser ke Audit) dan *"preserving traceability"* (jejak asal failure utuh dari produser sampai ke Audit Record).
- **R1-001 (Component Interaction):** Linear propagation memanfaatkan chain yang sudah didefinisikan (L104: "linear causality along the chain"; L118: "no additional interaction is invented"). Ini menghormati invariant I3 (Audit does not affect outcome — Audit = termination point, bukan propagation forwarder).
- **ADR-003 (Execution Conflict):** C-05 mengonsumsi "Execution Conflict" (ADR-003 L234/L308) sebagai defined failure Execution — yang divalidasi R3-002 sebagai architectural extension. Propagation model tidak mendefinisikan ulang istilah ini; ia hanya menetapkan bahwa Execution Conflict mengikuti model propagasi yang sama dengan defined failure Execution lain.

**Mengapa ini terbaik:** Alternative B **paling selaras dengan kumpulan dokumen** — linear propagation memanfaatkan chain yang sudah ada (bukan menciptakan jalur baru), menghormati terminasi di Audit Recorder (bukan feedback loop), menjaga separation of responsibility (setiap komponen mempropagasikan failure sendiri), deterministik (satu arah), traceable, dan tidak menciptakan komponen/authority/interaksi baru. Alternative A (containment) bertentangan dengan Blueprint C-05 dan AUDIT_SPEC; Alternative C (coordinator) tidak didukung evidence; Alternative D (Contract-driven) hanya menangkap dimensi boundary, bukan model propagasi penuh. Pilihan B paling tepat secara arsitektural dan paling sedikit mengubah apa yang sudah didefinisikan.

---

# Consequences

## Positive

- **Separation of responsibility:** setiap komponen mempropagasikan failure **miliknya sendiri** — tidak ada tumpang tindih.
- **Deterministic propagation path:** failure mengikuti satu jalur linear — tidak bercabang, tidak ambigu, tidak tergantung kondisi runtime.
- **Traceability & auditability:** failure sampai ke Audit Recorder dengan jejak asal yang utuh (produser → chain → Audit Record) — memenuhi GOVERNANCE "participate in auditing" dan AUDIT_SPEC Traceability Rules.
- **Bounded responsibility:** tidak menciptakan komponen/authority baru — propagation adalah **perilaku dari komponen eksisting**, bukan komponen baru.
- **Runtime integrity:** tidak menciptakan jalur interaksi baru — propagation menggunakan chain yang sudah didefinisikan R1-001.
- **Implementation independence:** bentuk propagation arsitektural, bukan mekanisme implementasi.
- **Architectural survivability:** linear chain valid regardless of deployment topology.

## Negative

- Tidak menetapkan **graceful degradation** — propagation linear tidak menyediakan mekanisme recovery di tengah chain (failure selalu sampai ke Audit Recorder). Namun ini disengaja: graceful degradation adalah mekanisme implementasi, bukan keputusan arsitektural.
- Tidak menetapkan **cascading failure protection** — jika satu komponen gagal mempropagasikan failure, failure itu tidak sampai ke Audit. Namun setiap komponen memiliki defined failure (termasuk failure internal seperti Descriptor corrupted) yang juga dipropagasikan — termasuk kegagalan propagasi itu sendiri jika didefinisikan.

## Accepted Trade-offs

- **Strict propagation** vs **graceful degradation:** dipilih strict propagation pada tingkat arsitektural, dengan graceful degradation **terbuka** sebagai mekanisme implementasi.
- **Linear chain adherence** vs **routing flexibility:** dipilih kepatuhan pada chain yang sudah ada — chain linear sudah didefinisikan, deterministik, dan tidak memerlukan routing kompleks.

---

# Impact Analysis

## Terhadap Runtime
- Menetapkan arah dan terminasi propagasi failure: **komponen produser → ke depan sepanjang chain → Audit Recorder (terminasi).**
- Tidak menambah komponen Runtime atau mengubah tanggung jawab komponen eksisting.

## Terhadap Komponen Spesifik

| Komponen | Dampak |
|---|---|
| Registry | Failure resolusi (Citizen missing / Not Found / Descriptor corrupted / Version Mismatch) dipropagasikan ke depan ke Approval/Execution/Audit. |
| Approval Coordinator | Failure approval (defined states + Approval Conflict) dipropagasikan ke depan ke Execution → Audit. |
| Execution Scheduler | Failure eksekusi (6 defined failures + Execution Conflict) dipropagasikan ke Audit. |
| Audit Recorder | **Titik terminasi.** Mencatat failure yang diterima; tidak meneruskan ("Audit does not feed back"; I3). |

## Terhadap Future ADR
- **C-01 (Ordering):** propagation model tidak mempengaruhi ordering — ordering mengatur urutan eksekusi, bukan propagasi failure.
- **C-07 (Reference Boundaries):** ADS-004 menyediakan model propagasi yang konsisten dengan rantai internal Runtime; C-07 tetap ditulis lewat lifecycle R2-001.
- **C-08 (Verification Point Placement):** propagation model tidak mempengaruhi penempatan verification point; C-08 tetap independent.
- **Tidak mengubah validitas ADR-000..003** (non-contradiction).

## Terhadap Implementation
- Implementasi harus memastikan failure dipropagasikan dari komponen produser ke komponen berikutnya sesuai chain.
- Implementasi harus memastikan Audit Recorder adalah titik terminasi (failure direkam, tidak diteruskan).
- Mekanisme implementasi (routing, transport, callback, exception, channel) **tidak diatur** oleh ADR ini.

---

# Dependency Impact

- **Tidak memperkenalkan dependency baru** ke komponen/arsitektur (propagation menggunakan chain yang sudah ada).
- **Tidak menghapus dependensi** atau mengubah interface (Registry + Contract tetap; G4 lower-never-contradict-higher).
- **Tidak mengubah layering** (Mission → Constitution → Governance → Architecture → Specification → ADR → Implementation; R1-004). ADR-004 berada di lapisan ADR, di bawah Specification beku.
- **Konsisten** dengan aturan dependensi: failure propagation bersifat **perilaku memanfaatkan jalur yang sudah ada**, bukan dependency baru.

---

# Risk Assessment

Menggunakan RISK_MODEL Project SAM (5 dimensi).

| Dimension | Assessment |
|---|---|
| Probability | **Low** — keputusan perilaku (menggunakan chain yang sudah ada); risiko kegagalan keputusan rendah; tidak mengubah spec/behaviour komponen. |
| Impact | **Low** — tidak mengubah perilaku komponen; hanya menetapkan arah propagasi; tidak ada kehilangan fungsi/data. |
| Recoverability | **Very High** — keputusan dapat ditinjau/diubah lewat Future ADR atau ADR Superseded (ADR_TEMPLATE); no irreversible change. |
| Blast Radius | **Low** — mempengaruhi terutama arah propagasi failure & konteks authoring ADR berikutnya; tidak menyebar ke seluruh platform. |
| Reversibility | **Very High** — keputusan reversible (model propagasi dapat dievaluasi ulang sebagai Future ADR tanpa mengubah Foundation). |

**Kategori risiko yang relevan:** Configuration Risk (rendah), Architectural Risk (rendah). **Tidak ada dimensi yang dinilai sangat tinggi/berisiko.**

---

# Trust Assessment

- **Evidence:** keputusan berdasar bukti dokumen (R1-001 L104/L118/L134; AUDIT_SPEC L193/L181/L213; SAM_ARCHITECTURE Approved Execution Flow; GOVERNANCE Runtime Governance; Bluprint C-05 L158; APPROVAL_SPEC L146; REGISTRY_SPEC L166; EXECUTION_SPEC L161-L163; ADR-003 L277; R3-002 Verdict B) — **Evidence Before Opinion** (DECISION_MODEL).
- **Confidence:** **High** — konsisten lintas sumber independen (Foundation, Specification, Blueprint, R-series, ADR-003); reproducible & selaras dengan evidence di Constitution, Specification Layer, dan R1-001 Component Interaction.
- **Unknowns:** mekanisme implementasi (routing, batching, prioritization) — **dinyatakan out of scope**, bukan diasumsikan terpecahkan.

---

# Implementation Notes

Hanya **batas implementasi** — bukan desain implementasi:
- Implementasi harus mempropagasikan failure **mengikuti urutan chain linear** (Registry → Approval → Execution → Audit).
- Setiap komponen mempropagasikan **hanya** failure yang ia produksi sendiri.
- **Audit Recorder = titik terminasi** — tidak boleh ada feedback loop atau propagasi dari Audit ke komponen hulu.
- Mekanisme propagasi (error channel, callback, exception, event bus, message passing) **tidak diatur** — bebas implementasi.
- Implementasi harus **tidak bertentangan** dengan baseline beku (B2/F1a).

---

# Migration Strategy

- **Tidak ada migrasi arsitektur** karena belum ada implementasi formal Reference Runtime — propagation model baru didefinisikan di ADR ini.
- Bila suatu saat model berubah (mis. adopsi graceful degradation di tingkat arsitektural): migrasi dilakukan melalui ADR Superseded / Future ADR sesuai lifecycle R2-001, tanpa mengubah Foundation/Specification.

---

# Success Criteria

Bagaimana mengetahui keputusan ini berhasil:
1. Reference Runtime mengimplementasikan failure propagation ke depan sepanjang chain linear tanpa menciptakan jalur/jalur interaksi baru.
2. Failure sampai ke Audit Recorder dengan **jejak asal utuh** (dapat dilacak ke komponen produser).
3. Audit Recorder **tidak** meneruskan failure ke hulu (no feedback loop).
4. **Separation of responsibility:** tidak ada komponen yang mempropagasikan failure milik komponen lain.
5. Tidak ada kebutuhan mengubah Foundation/Specification untuk mewujudkan propagasi (**zero escalation**).
6. Dokumentasi keputusan terbaca jelas oleh implementer & reviewer (ADR_TEMPLATE kelengkapan).

---

# Future Reassessment

Situasi yang seharusnya memicu tinjauan/reassessment ADR-004:
- Kebutuhan **graceful degradation di tingkat arsitektural** (bukan hanya mekanisme implementasi).
- Model distribusi Runtime (Future ADR deployment distribution) yang menuntut propagation lintas host.
- Umpan balik implementasi/operasional yang menunjukkan model linear tidak lagi memadai.

---

# Related Documents

- GOVERNANCE (Runtime Governance, Long-Term Governance)
- SPECIFICATION_FREEZE (F1a/F3/F4/F5)
- SAM_ARCHITECTURE (Approved Execution Flow, Responsibility Matrix)
- G0-001_Reference_Runtime_Blueprint (C-05)
- R1-001_Minimal_Reference_Runtime_Design (Component Interaction L98-L118, Invariant I3)
- R2-001_ADR_Decision_Process_Definition
- AUDIT_SPECIFICATION (L137-L150, L181, L193, L213)
- APPROVAL_SPECIFICATION (L146)
- REGISTRY_SPECIFICATION (L164-L173)
- EXECUTION_SPECIFICATION (L150-L163)
- ADR-003 (Equation for L277 "Execution Conflict"; R3-002 Verdict B)

---

# Validation

## Audit 1 — Problem Coverage
**LULUS.** ADR menjawab **satu** pertanyaan arsitektur (Failure Propagation Model / C-05) secara tuntas di `# Problem Statement`, dengan boundary in/out eksplisit (`# Purpose`/`# Context`: tidak membahas bagaimana failure didefinisikan, mekanisme implementasi, recovery/retry). Setiap penyebutan istilah di-luar-scope hanya sebagai pernyataan batas.

## Audit 2 — Alternative Coverage
**LULUS.** `# Alternatives Considered` mencakup **seluruh alternatif yang dapat didukung oleh evidence** (A: Local Containment, B: Linear Propagation, C: Central Coordinator, D: Contract-Driven) — **tidak menciptakan alternatif tanpa evidence**. Tiap alternatif dievaluasi terhadap evidence aktual (Evidence Evaluation table).

## Audit 3 — Foundation Compliance
**LULUS.** Semua decision driver ber-anchor dokumen (R1-001 Component Interaction L104/L118; AUDIT_SPEC L193; SAM_ARCHITECTURE Approved Execution Flow; GOVERNANCE Runtime Governance). Tidak ada driver yang merupakan opini pribadi / preferensi teknologi.

## Audit 4 — Specification Compliance
**LULUS.** Keputusan **tidak bertentangan** dengan Specification beku: tidak mengubah Registry/Approval/Execution/Audit Specification; propagation memanfaatkan chain yang sudah didefinisikan, tidak menciptakan mekanisme baru. B2 non-contradiction terhadap baseline beku.

## Audit 5 — Architectural Consistency
**LULUS.** Keputusan konsisten lintas layer (Mission → Constitution → Governance → Architecture → Specification → ADR → Implementation) dan tidak mengubah layering/Gov/Canonical Architecture. Selaras dengan G4 (lower-never-contradict-higher) dan R1-001 Component Interaction.

## Audit 6 — Future ADR Compatibility
**LULUS.** ADR-004 **tidak mengubah validitas** ADR-000..003 (non-contradiction). Tidak mempengaruhi C-01/C-07/C-08. Propagation model menyediakan fondasi untuk ADR turunan yang mengonsumsi failure propagation.

## Audit 7 — Implementation Independence
**LULUS.** ADR memberi **batas implementasi**, bukan desain: `# Implementation Notes` hanya batas (chain linear, terminasi di Audit, setiap komponen mempropagasikan failure sendiri); tidak menetapkan mekanisme routing/transport/event bus.

## Audit 8 — Final ADR Validation
**LULUS.** ADR lengkap menurut ADR_TEMPLATE, metadata terisi, risiko (RISK_MODEL) & trust (TRUST_MODEL) dinilai, trade-off jujur, non-contradiction, STOP tidak aktif. **Siap dipublikasikan** (Status: Accepted).

---

# STOP Condition

STOP apabila ditemukan salah satu kondisi berikut → jangan memaksakan ADR, jangan mengubah dokumen lain; hanya lapor.

| Trigger | Hadir? | Bukti |
|---|---|---|
| **Perlu mengubah Foundation** | **Tidak** | ADR tidak menyentuh MISSION/CONSTITUTION/GOVERNANCE; keputusan berada di lapisan ADR (R1-004). |
| **Perlu mengubah Specification** | **Tidak** | ADR mencatat keputusan tanpa mengubah 7 Specification (F3/F4; B2 non-contradiction). |
| **Perlu mengubah Canonical Architecture** | **Tidak** | Propagation menggunakan chain yang sudah didefinisikan SAM_ARCHITECTURE. |
| **Perlu membuat authority/domain baru** | **Tidak** | ADR = kanal pencatatan subordinat, bukan authority (R2-001 Audit 5; G1a/F1a). Tidak menambah komponen/domain. |
| **Perlu taksonomi failure baru** | **Tidak** | ADR tidak menciptakan kategori/tipe failure baru — ia hanya menetapkan bagaimana defined failure yang sudah ada dipropagasikan. "Execution Conflict" dikonsumsi dari ADR-003 (C-04), bukan didefinisikan di sini. |
| **Perlu lifecycle baru** | **Tidak** | ADR-004 ditulis lewat lifecycle R2-001 yang sama. |
| **Perlu kontradiksi ADR-000/001/002/003** | **Tidak** | Propagation model konsisten dengan semua ADR terdahulu — ADR-000 (single unit, propagation internal ke satu Runtime), ADR-001 (Approval = gate, failure Approval = bagian dari rantai), ADR-002 (resolusi deterministik = failure deterministik), ADR-003 (idempotensi via Contract, Execution Conflict = failure Execution yang dipropagasikan). |
| **Keputusan ternyata dua keputusan** | **Tidak** | ADR-004 hanya Failure Propagation Model (C-05); tidak mencakup ordering/concurrency/boundaries/verification. |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP TIDAK AKTIF.** ADR-004 sah untuk dipublikasikan sebagai keputusan arsitektur (Accepted).

---

# Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-03 | Chief Architect | Accepted (draft → Accepted) — dibuka untuk review arsitektur. |

---

# Author Checklist

- [x] Problem clearly defined
- [x] Alternatives documented (A/B/C/D; tidak menciptakan tanpa evidence)
- [x] Decision justified (Alternative B, keputusan proses)
- [x] Trade-offs documented
- [x] Risks evaluated (RISK_MODEL)
- [x] Trust assessment completed (TRUST_MODEL)
- [x] Related documents referenced
- [x] Terminology follows GLOSSARY.md
- [x] Consistent with CONSTITUTION.md

---

# Common Mistakes

Tidak dilanggar: tidak mendeskripsikan implementasi, tidak mengomit alternatif (A/B/C/D dicatat & dievaluasi), tidak mengabaikan trade-off, tidak merekam opini tanpa evidence (semua driver ber-anchor dokumen; Evidence Evaluation table per alternatif), tidak mencampur prosedur operasional dengan keputusan arsitektur, tidak membuat ADR untuk perubahan editorial sepele (keputusan arsitektur nyata).

---

# Completion Checklist

- [x] Metadata complete
- [x] Cross references validated
- [x] Review completed
- [x] Status updated (Accepted)
- [x] Ready for repository publication
