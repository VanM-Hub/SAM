# ADR-003 — Idempotency Realization Model

| Field | Value |
|---|---|
| **Decision ID** | ADR-003 |
| **Title** | Idempotency Realization Model |
| **Status** | Accepted |
| **Date** | 2026-08-03 |
| **Architecture Domain** | Execution — Idempotency |
| **Root Candidate** | C-04 (Idempotency Realization) |
| **Decision Type** | Architectural decision (policy) |
| **Owner** | Project SAM |
| **Author** | ZARA |

---

## Purpose

This ADR records the single architectural decision by which the **idempotency property** of an Execution is made **observable**, respecting the constraints that the Execution Specification already defines idempotency behaviorally but deliberately does **not** dictate a technical mechanism. It resolves Root Candidate **C-04** of Blueprint G0-001.

This ADR answers **one question only**:

> **Bagaimana properti idempotency suatu operasi dibuat observable oleh Execution Layer tanpa mekanisme teknis yang dimandatkan oleh Specification?**

It does **not** expand into cache design, retry strategy, hashing schemes, UUID generation, deduplication tokens, storage backends, transport-level guarantees, or implementation-specific idempotency mechanisms. All are out of scope.

---

## Decision Drivers

Drivers are drawn **only** from the frozen Foundation, the Specification Layer, the Blueprint, and the prior ADR records (ADR-000, ADR-001, ADR-002). No assumption outside the documents is used.

| # | Driver | Source |
|---|---|---|
| D-01 | Execution SHALL NOT be re-executed as a new Execution unless the operation is idempotent, when a prior Execution has Completed. | EXECUTION_SPEC L175 |
| D-02 | An operation may be repeated when repeating it produces the same outcome as performing it once. | EXECUTION_SPEC L173 |
| D-03 | An operation SHALL NOT be repeated when repetition could produce a different or unintended outcome. | EXECUTION_SPEC L174 |
| D-04 | Idempotency is a property of the operation under its Contract. | EXECUTION_SPEC L177 |
| D-05 | The Execution Specification does not dictate a technical mechanism for achieving idempotency. | EXECUTION_SPEC L177 |
| D-06 | Governance must always remain deterministic — identical inputs produce identical governance decisions. | PHILOSOPHY "Why Determinism Matters" L307–L353 |
| D-07 | The Execution Scheduler SHALL NOT act without an Approval decision and SHALL NOT skip verification or audit. | G0-001 L72 |
| D-08 | The current Execution lifecycle state SHALL be observable. | EXECUTION_SPEC L120 |
| D-09 | The Execution Scheduler observes Execution lifecycle, result, and idempotency status. | G0-001 L55–L56 |
| D-10 | Archived is terminal. An archived Execution SHALL NOT transition to any other state. | EXECUTION_SPEC L146 |
| D-11 | Execution derives its authority from the Constitution and Canonical Architecture. It extends none of them. Execution does not decide, discover, or define; it performs. | EXECUTION_SPEC L56, L66 |
| D-12 | Discovery SHALL be idempotent; an identical request SHALL produce an identical result. | REGISTRY_SPEC L129 |
| D-13 | C-04 is an independent, atomic, Certified (A) architectural decision. It does not depend on any other candidate; it is decidable alone. | R2-002 Output 3–4, Output 6 |
| D-14 | Each ADR must not contradict the frozen baseline (Foundation, Specification, prior ADRs). | SPECIFICATION_FREEZE; R2-001 |

---

## Context

### Status fase

Project SAM telah menyelesaikan tiga keputusan arsitektur inti:

- **ADR-000 — Deployment Topology** (Accepted): satu Runtime cohesive per domain (Alternative A).
- **ADR-001 — Approval Decision Model** (Accepted): Accountable Decision Framework (Alternative C) untuk Approval Coordinator.
- **ADR-002 — Capability Resolution Policy** (Accepted): exact-match-preferred dengan fallback kompatibel deterministik (C-02).

Root Candidate **C-04 — Idempotency Realization** telah dianalisis selama Discovery:

- **G0-001** — Blueprint mencatat C-04 sebagai candidate dengan trade-off "explicit idempotency keys and operation-defined semantics" (L157).
- **G1-001** — C-02 Analysis (C-04 tidak dianalisis terpisah oleh G1, tetapi G0-001 merekam trade-off-nya).
- **R1-002** — Dependency Analysis: C-04 = **root**, Independent, High Ripple (mendasari retry/reorder correctness).
- **R1-003** — Ordering Validation: C-04 genuinely independent, decidable alone.
- **R2-002** — Candidate Independence Certification: C-04 = **A — Certified** (atomic: 1 keputusan — realisasi idempotency; boundary: explicit keys vs operation-defined semantics).

Pemilihan ADR-003 sebagai ADR keempat adalah **Chief Architect Process Decision**, sesuai R1-003 (Several Equivalent = {C-02, C-03, C-04, C-06}) dan R2-003 (Selection Record). Urutan C-02 → C-04 dipilih karena C-04 tidak bergantung pada C-02 (R2-002), namun menyediakan fondasi untuk C-05 (failure propagation) yang terkait erat.

### Inti keputusan C-04 (dari G0-001 dan EXECUTION_SPEC)

EXECUTION_SPEC L167–L177 mendefinisikan idempotency secara **behavioral** — yaitu:

- Idempotency mendefinisikan **kapan** suatu Execution boleh diulang (L169).
- Suatu operasi boleh diulang ketika pengulangan menghasilkan **outcome yang sama** dengan eksekusi sekali (L173).
- Operasi **TIDAK BOLEH** diulang bila pengulangan dapat menghasilkan outcome berbeda atau tidak diinginkan (L174).
- **Completed Execution TIDAK BOLEH** dieksekusi ulang sebagai Execution baru kecuali operasi bersifat idempotent (L175).
- Idempotency adalah **properti operasi di bawah Contract-nya** (L177).
- Specification **tidak mendikte mekanisme teknis** untuk mencapai idempotency (L177).

Dengan demikian, Specification telah menetapkan **apa** yang dimaksud dengan idempotency dan **kapan** aturan berlaku, tetapi **tidak menetapkan bagaimana** sifat idempotency itu dibuat **observable** — tidak oleh Execution Scheduler, tidak oleh Audit Recorder, tidak oleh komponen arsitektur manapun.

G0-001 L157 merumuskan ruang keputusan sebagai trade-off:

> **"How an operation's idempotency property is made observable without a mandated technical mechanism — trade-off between explicit idempotency keys and operation-defined semantics."**

Ini adalah **ruang keputusan yang sengaja dibuka** oleh baseline — bukan cacat dokumen, melainkan keputusan arsitektural tentang realisasi idempotency sebagai properti **observable**.

Tanpa keputusan ini:

- Execution Scheduler tidak memiliki basis arsitektural untuk menentukan apakah suatu operasi Completed boleh diulang (D-01) — melanggar batas Execution (D-11: "does not decide, discover, or define").
- Audit Recorder tidak dapat membedakan "repeat yang sah dari operasi idempotent" dan "re-execution ilegal dari operasi non-idempotent" — mengancam traceability rantai Audit.
- Dua Runtime independen dapat mengambil keputusan berbeda tentang operasi yang sama — melanggar determinism (D-06).

---

## Problem Statement

Idempotency didefinisikan oleh EXECUTION_SPEC sebagai properti operasi di bawah Contract-nya (D-04), dengan aturan behavioral yang jelas: Completed Execution tidak boleh diulang kecuali idempotent (D-01), pengulangan harus menghasilkan outcome yang sama (D-02), dan pengulangan tidak boleh menghasilkan outcome berbeda (D-03).

Namun, Specification **tidak menetapkan**:

1. **Bagaimana** Execution Layer mengamati (observe) sifat idempotency suatu operasi — dari mana ia tahu bahwa operasi "bersifat idempotent"?
2. **Siapa** yang bertanggung jawab mendeklarasikan idempotency — apakah Execution Layer memaksakan mekanisme (explicit key) atau cukup mengamati deklarasi Contract?
3. **Bagaimana** pengulangan direalisasikan secara arsitektural — apakah melalui kunci eksplisit yang dipaksakan oleh Execution atau melalui semantik yang didefinisikan oleh operasi sendiri?

Ini adalah **ruang keputusan yang sengaja dibuka** oleh EXECUTION_SPEC L177: "This specification does not dictate a technical mechanism for achieving idempotency." Specification telah menetapkan hukum behavioral; ADR-003 menetapkan **model realisasi** — bagaimana hukum itu dibuat *observable* tanpa melanggar D-05 (tanpa mekanisme yang dimandatkan).

---

## Alternatives Considered

Alternatif yang dianalisis berasal dari trade-off yang direkam Blueprint G0-001 L157. **Tidak ada alternatif baru yang diciptakan.** Hanya alternatif yang berada dalam ruang keputusan inti C-04 (bagaimana idempotency dibuat observable) yang dipertimbangkan.

### Alternative A — Explicit Idempotency Keys (system-mandated mechanism)

**Reference:** Blueprint G0-001 L157, trade-off "explicit idempotency keys."

Execution Layer memaksakan penggunaan **kunci idempotency eksplisit** (misalnya `idempotency_key` pada Execution Request) yang dibawa oleh setiap operasi. Execution Scheduler menggunakan kunci ini untuk mengenali pengulangan — jika sebuah operasi dengan kunci yang sama telah mencapai Completed, maka pengulangan adalah sah bila dan hanya bila operasi tersebut dideklarasikan idempotent oleh Contract.

**Advantages**
- Observabilitas maksimal: Execution Scheduler memiliki mekanisme eksplisit dan seragam untuk mendeteksi pengulangan.
- Audit traceability tinggi: kunci eksplisit meninggalkan jejak yang jelas ("ini adalah pengulangan dari operasi X").
- Implementasi sederhana: Scheduler cukup membandingkan kunci, tidak perlu memahami semantik operasi.

**Disadvantages**
- **Melanggar D-05 secara langsung.** EXECUTION_SPEC L177 secara eksplisit menyatakan tidak mendikte mekanisme teknis; memaksakan kunci eksplisit justru adalah mekanisme teknis yang dimandatkan.
- **Melanggar D-04.** Idempotency didefinisikan sebagai properti operasi di bawah Contract; memaksakan mekanisme eksternal (kunci) menggeser tanggung jawab dari Contract ke Execution Layer — melanggar D-11 ("Execution does not define").
- **Melanggar D-11.** Execution "performs, does not define"; memaksakan format kunci adalah tindakan mendefinisikan, bukan menjalankan.
- Menambah beban pada setiap operasi untuk membawa dan mengelola kunci — termasuk operasi yang sudah idempotent secara inherent.

### Alternative B — Operation-Defined Semantics (contract-declared, spec-aligned)

**Reference:** Blueprint G0-001 L157, trade-off "operation-defined semantics."

Idempotency dideklarasikan oleh **Contract** — bukan oleh mekanisme yang dipaksakan Execution. Execution Layer mengamati deklarasi Contract pada saat runtime dan menggunakan informasi tersebut untuk menentukan apakah suatu Completed Execution boleh diulang. "Observability" tercapai melalui **Contract metadata** (deklarasi idempotency sebagai atribut Contract), bukan melalui mekanisme teknis (kunci, token, hash).

Execution Scheduler berperilaku:

1. Sebelum mengeksekusi ulang operasi Completed, konsultasi Contract untuk membaca deklarasi idempotency.
2. Jika Contract menyatakan operasi **idempotent**: pengulangan sah → Execution baru dibuat.
3. Jika Contract menyatakan operasi **non-idempotent** atau **tidak mendeklarasikan**: pengulangan ditolak → mengembalikan defined failure (Execution Conflict) sesuai D-03.
4. Jika operasi yang sama (Approval + Contract + Capability yang identik) di-submit ulang setelah Completed: Execution Scheduler mengenali via lifecycle state (D-08) + Contract declaration — bukan via kunci eksternal.

**Advantages**
- **Selaras penuh dengan D-05.** Tidak memaksakan mekanisme teknis apapun; Specification tetap bebas dari mandate mekanis.
- **Selaras penuh dengan D-04.** Idempotency tetap menjadi properti operasi di bawah Contract — Execution hanya mengamati (observe), bukan mendefinisikan.
- **Selaras dengan D-11.** Execution "performs" — bertindak berdasarkan informasi Contract, bukan menciptakan aturan baru.
- Contract sebagai single source of truth untuk properti idempotency — konsisten dengan prinsip Separation of Responsibility.
- Idempotency yang sudah inherent pada operasi (misalnya Discovery, D-12) tidak memerlukan mekanisme tambahan.

**Disadvantages**
- Observabilitas bergantung pada kualitas deklarasi Contract — Contract yang tidak mendeklarasikan idempotency dengan benar dapat menghasilkan false negative (operasi idempotent ditolak) atau false positive (operasi non-idempotent diulang).
- Execution Scheduler harus mampu membaca dan menginterpretasi metadata Contract — menambah sedikit kompleksitas pada Scheduler.
- Tidak ada "jejak kunci" eksplisit dalam Execution Record — traceability pengulangan mengandalkan lifecycle state + Contract reference.

---

## Decision

**DIPUTUSKAN:** Project SAM mengadopsi **Operation-Defined Semantics (Alternative B)** sebagai model realisasi idempotency — idempotency dideklarasikan oleh Contract dan diamati (observed) oleh Execution Layer, bukan dimandatkan oleh mekanisme teknis yang dipaksakan:

1. **Contract sebagai pemilik deklarasi.** Setiap Contract **SHALL** mendeklarasikan apakah operasi yang diaturnya bersifat idempotent atau non-idempotent. Deklarasi ini adalah atribut Contract — bukan mekanisme eksternal, bukan kunci, bukan token. (D-04)

2. **Execution sebagai pengamat.** Execution Scheduler **mengamati** deklarasi Contract untuk menentukan apakah pengulangan suatu Completed Execution diperbolehkan. Execution tidak mendefinisikan idempotency; ia membaca dan bertindak berdasarkan Contract. (D-11)

3. **Aturan pengulangan.** Sebelum membuat Execution baru untuk operasi yang sudah Completed:
   - Jika Contract mendeklarasikan **idempotent** → pengulangan sah (D-02), Execution baru dibuat, lifecycle baru dimulai.
   - Jika Contract mendeklarasikan **non-idempotent** atau **tidak mendeklarasikan** → pengulangan ditolak (D-03), Execution Scheduler mengembalikan defined failure (**Execution Conflict** — operasi sudah Completed dan non-idempotent).

4. **Tanpa mekanisme teknis yang dimandatkan.** Model ini tidak memaksakan format kunci, skema hashing, UUID, token, atau mekanisme deduplikasi apapun. Contract bebas menggunakan representasi apapun untuk deklarasi idempotency-nya, selama observable oleh Execution Layer. (D-05)

5. **Observabilitas via lifecycle state + Contract.** Execution Scheduler mengenali pengulangan melalui kombinasi **lifecycle state** (Completed, D-08/D-09) + **Contract reference** (Approval + Contract + Capability yang identik), bukan melalui kunci atau token eksplisit. Basis pengenalan: "apakah Approval+Contract+Capability yang sama sudah pernah mencapai Completed?" — konsisten dengan D-09 (Scheduler observes lifecycle).

6. **Alignment dengan ADR yang sudah diterima.** Keputusan ini tidak mengubah ADR-000 (topologi), ADR-001 (approval), atau ADR-002 (resolusi). ADR-003 hidup dalam ruang yang sengaja dibuka EXECUTION_SPEC L177 dan tidak membutuhkan perubahan Foundation/Specification.

**Ringkas:** Idempotency adalah **properti operasi yang dideklarasikan oleh Contract** dan **diamati oleh Execution Layer melalui lifecycle state + Contract reference** — tanpa mekanisme teknis yang dimandatkan. Execution Scheduler membedakan "pengulangan sah" dan "re-execution ilegal" berdasarkan deklarasi Contract, bukan kunci eksplisit.

---

## Architectural Rationale

1. **Spesifikasi sudah menetapkan arah (D-04, D-05).** EXECUTION_SPEC L177 menyatakan idempotency adalah properti operasi di bawah Contract dan tidak mendikte mekanisme teknis. Alternative B mengikuti arah ini secara persis — Contract sebagai pemilik, Execution sebagai pengamat. Alternative A (explicit keys) justru melawan arah spesifikasi dengan memaksakan mekanisme yang dilarang oleh D-05.

2. **Execution "performs, does not define" (D-11).** EXECUTION_SPEC L56/L66 menetapkan batas yang jelas: Execution tidak memutuskan, menemukan, atau mendefinisikan; ia menjalankan. Memaksakan mekanisme kunci (Alternative A) berarti Execution mendefinisikan format dan aturan — melampaui batas otoritasnya. Alternative B menghormati batas ini: Execution hanya membaca deklarasi Contract dan bertindak.

3. **Determinism melalui Contract (D-06).** PHILOSOPHY "Why Determinism Matters" menetapkan bahwa governance harus selalu deterministik — identical inputs → identical outcomes. Dengan Contract sebagai single source of truth untuk deklarasi idempotency, dua Execution Scheduler independen yang membaca Contract yang sama akan mengambil keputusan yang sama untuk operasi yang sama — deterministik, dapat diaudit, dapat direproduksi.

4. **Separation of Responsibility terjaga.** Contract mendeklarasikan sifat idempotency (sebagaimana ia mendefinisikan aturan komunikasi — CONTRACT_SPEC); Execution mengamati deklarasi dan menegakkan aturan behavioral (sebagaimana ia menjalankan operasi — EXECUTION_SPEC). Tidak ada tumpang-tindih otoritas. Tidak ada komponen yang melampaui batasnya.

5. **Selaras dengan idempotency Discovery (D-12).** REGISTRY_SPEC L129 sudah menetapkan Discovery sebagai idempotent secara inherent — tanpa memerlukan kunci eksplisit. Alternative B konsisten dengan preseden ini: idempotency adalah properti yang dideklarasikan (atau inherent), bukan mekanisme yang dipaksakan.

6. **Implementasi independen (per R2-002).** ADR-003 menetapkan **model arsitektural** (siapa mendeklarasikan, siapa mengamati, aturan pengulangan), bukan mekanisme penyimpanan, algoritma deteksi duplikat, skema Contract metadata, atau format deklarasi. Konsisten dengan C-04 as a Certified atomic architectural decision, dan dengan prinsip Implementation Independence.

---

## Consequences

### Positive

- **Kepatuhan penuh terhadap Specification.** Alternative B mengikuti arah EXECUTION_SPEC L167–L177 tanpa melanggar D-04, D-05, atau D-11 — tidak ada perubahan pada frozen baseline.
- **Contract sebagai single source of truth.** Deklarasi idempotency terpusat di Contract, konsisten dengan peran Contract sebagai pemilik aturan komunikasi operasi.
- **Determinisme lintas-implementasi.** Dua Execution Scheduler independen yang membaca Contract yang sama mengambil keputusan yang sama — selaras dengan D-06.
- **Separation of Responsibility.** Contract mendeklarasikan; Execution mengamati dan menegakkan. Tidak ada tumpang-tindih.
- **Fleksibilitas implementasi.** Contract bebas merepresentasikan deklarasi idempotency dengan cara apapun — tidak ada format kunci, skema token, atau algoritma yang dimandatkan.

### Negative

- **Ketergantungan pada kualitas deklarasi Contract.** Contract yang salah mendeklarasikan idempotency (false positive: menyatakan idempotent padahal tidak) dapat menyebabkan pengulangan yang menghasilkan outcome berbeda — melanggar D-02/D-03. Ini adalah risiko yang harus dimitigasi oleh Contract validation (lihat Risk Assessment).
- **Observabilitas lebih rendah dibanding kunci eksplisit.** Tanpa kunci, trace "pengulangan dari operasi X" mengandalkan lifecycle state + Contract reference — bukan jejak kunci eksplisit. Audit trail tetap tersedia (via Execution identity + lifecycle), tetapi tidak se-visual kunci eksplisit.

### Accepted Trade-offs

| Trade-off | Pilihan | Rasional |
|---|---|---|
| Observabilitas (explicit key) vs Spec-compliance (no mandated mechanism) | **Spec-compliance** (D-05) — tanpa kunci eksplisit | EXECUTION_SPEC L177 melarang mekanisme yang dimandatkan; Contract declaration tetap observable via lifecycle state |
| Mekanisme seragam vs Fleksibilitas operasi | **Fleksibilitas** — Contract bebas merepresentasikan deklarasi | D-04: idempotency adalah properti operasi, bukan properti sistem |
| Traceability eksplisit (key) vs Traceability struktural (lifecycle+Contract) | **Traceability struktural** — via Execution identity + lifecycle state | Lifecycle state (D-08) + Contract reference sudah cukup untuk rekonstruksi jejak pengulangan |

---

## Impact Analysis

| Area | Dampak |
|---|---|
| **Contract Specification** | Contract harus mendukung deklarasi idempotency sebagai atribut. Ini **bukan perubahan Specification** — Contract sudah memiliki ruang untuk atribut operasi; deklarasi idempotency adalah salah satu atribut yang diisi. |
| **Execution Scheduler** | Menerapkan logika: sebelum membuat Execution baru, cek apakah Approval+Contract+Capability sudah Completed → jika ya, konsultasi Contract untuk deklarasi idempotency → izinkan (idempotent) atau tolak dengan Execution Conflict (non-idempotent). |
| **Execution Lifecycle** | Lifecycle state (Completed) menjadi basis pengenalan pengulangan. Tidak ada state baru yang ditambahkan; Completed→Archived tetap terminal (D-10). Pengulangan yang sah membuat Execution **baru** dengan lifecycle baru (Created→...)—bukan transisi dari Completed. |
| **Audit Recorder** | Merekam Execution Conflict ketika pengulangan ditolak (non-idempotent). Merekam Execution baru dengan reference ke Contract ketika pengulangan sah (idempotent). Traceability via lifecycle state + Contract reference. |
| **Approval Coordinator** | Tidak terpengaruh secara langsung. Approval tetap bekerja pada Capability ter-resolusi (ADR-001/ADR-002); pengulangan operasi idempotent tetap memerlukan Approval baru — idempotency tidak melewati Approval gate. |
| **Registry / Discovery** | Tidak terpengaruh. Discovery sudah idempotent secara inherent (D-12). |
| **Future ADR (C-01/C-05/C-07/C-08)** | C-05 (failure propagation): Execution Conflict menjadi salah satu defined failure yang harus disurfacing ke Audit Recorder. C-01 (ordering): pengulangan operasi idempotent harus di-queue dengan semantik ordering yang konsisten. |

---

## Dependency Impact

- **C-04 tidak memiliki dependency masuk** (R2-002 Output 4, R2a/R2e: decidable alone, no hidden dependency). Terkonfirmasi: tidak bergantung pada C-01, C-02, C-03, C-05, C-06, C-07, C-08.
- **C-04 mempengaruhi keluar** (R2-002 Output 7): C-05 (failure propagation — Execution Conflict adalah failure surface baru); C-01 (ordering — pengulangan harus di-queue dengan semantik yang benar).
- **Tidak ada perubahan pada ADR-000, ADR-001, atau ADR-002.** ADR-003 hidup dalam ruang yang sengaja dibuka EXECUTION_SPEC L177 dan tidak menyentuh keputusan root lain.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation / Notes |
|---|---|---|---|
| Contract salah mendeklarasikan idempotency (false positive) | Medium | High | Contract validation sebelum deployment; Audit Recorder membandingkan outcome pengulangan dengan outcome awal (drift detection) |
| Contract tidak mendeklarasikan idempotency (missing declaration) | Medium | Medium | Default behavior = tolak pengulangan (safe default — D-03: "SHALL NOT be repeated"); operasi idempotent yang tidak dideklarasikan akan ditolak (false negative, bukan pelanggaran keamanan) |
| Execution Scheduler gagal membaca deklarasi Contract | Low | High | Contract reference adalah prasyarat Execution (D-08); Contract yang tidak dapat dibaca menghasilkan Execution Failure (Missing Contract), bukan pengulangan senyap |
| Ambiguity "operasi yang sama" untuk pengulangan | Low | Medium | Definisi: Approval + Contract + Capability yang identik; basis identitas yang sama dengan ADR-002 (Capability Identity + Version) — deterministik |
| Regresi determinism akibat perbedaan interpretasi Contract | Low | High | Contract adalah dokumen yang terikat versi; dua Scheduler dengan Contract versi sama → keputusan sama (D-06) |

**Kesimpulan risiko:** 1 risiko Medium (false positive declaration), 3 risiko Low, 1 risiko Medium (missing declaration dengan safe default). Dampak tertinggi (false positive) di-mitigasi oleh Contract validation + Audit drift detection. **Reversibel** — model realisasi idempotency dapat diubah ADR turunan tanpa mengubah Foundation/Specification.

---

## Trust Analysis

| Dimensi | Assessment |
|---|---|
| **Determinism** | Confidence **High** — Contract sebagai single source of truth; dua Scheduler dengan Contract sama → keputusan sama (D-06) |
| **Explainability** | Confidence **High** — aturan sederhana: Contract deklarasi → Scheduler amati → izinkan/tolak; dapat dijelaskan dan diaudit |
| **Traceability** | Confidence **Medium-High** — lifecycle state + Contract reference menyediakan jejak; tanpa kunci eksplisit, rekonstruksi memerlukan korelasi Contract+Approval, bukan pencarian kunci tunggal |
| **Separation of Responsibility** | Confidence **High** — Contract mendeklarasikan, Execution mengamati; batas D-11 terjaga |
| **Implementability** | Confidence **High** — menetapkan model, bukan mekanisme teknis; implementasi bebas merepresentasikan deklarasi Contract |

---

## Implementation Notes

- **Fokus implementasi:** Execution Scheduler mengimplementasikan logika konsultasi Contract untuk deklarasi idempotency sebelum membuat Execution baru untuk operasi yang sudah Completed.
- **Contract metadata:** Contract harus mendukung atribut deklarasi idempotency (`idempotent: true/false`). Format bebas — tidak dimandatkan oleh ADR ini.
- **Default safe:** jika Contract tidak mendeklarasikan idempotency → asumsikan non-idempotent → tolak pengulangan (Execution Conflict). Safe default: menolak lebih aman daripada mengizinkan tanpa deklarasi.
- **Execution Conflict:** defined failure baru (atau sub-tipe dari Execution Failure yang sudah ada di EXECUTION_SPEC L150–L163) — "operasi sudah Completed dan non-idempotent."
- **Lifecycle:** pengulangan sah membuat Execution **baru** (Created→Queued→...), bukan transisi dari Completed. Completed→Archived tetap satu arah (D-10).
- **Audit trail:** Execution Record untuk pengulangan sah menyertakan reference ke Execution awal (via Approval+Contract+Capability identity) — memungkinkan rekonstruksi rantai pengulangan.

---

## Migration Strategy

- **No breaking change pada Foundation/Specification/ADR-000/ADR-001/ADR-002.** ADR-003 mengisi ruang yang sengaja dibuka EXECUTION_SPEC L177, tidak mengubah baseline beku.
- **Adoption:** Execution Scheduler menambahkan logika konsultasi Contract untuk idempotency. Contract diperkaya dengan atribut deklarasi idempotency.
- **Verifikasi:** uji bahwa operasi idempotent yang dideklarasikan dapat diulang setelah Completed; operasi non-idempotent ditolak dengan Execution Conflict; operasi tanpa deklarasi ditolak (safe default).
- **Evolusi lanjut:** model ini dapat direvisi lewat ADR turunan tanpa menyentuh baseline.

---

## Success Criteria

1. **Kepatuhan D-05:** tidak ada mekanisme teknis (kunci, token, hash, UUID) yang dimandatkan oleh ADR ini. *Terukur: review bahwa ADR hanya menetapkan model, bukan mekanisme.*
2. **Pengulangan sah (idempotent):** operasi idempotent yang dideklarasikan Contract dapat diulang setelah Completed — menghasilkan Execution baru dengan lifecycle baru. *Terukur: uji fungsional.*
3. **Penolakan sah (non-idempotent):** operasi non-idempotent yang sudah Completed ditolak dengan Execution Conflict. *Terukur: uji fungsional.*
4. **Safe default:** operasi tanpa deklarasi idempotency ditolak (default non-idempotent). *Terukur: uji fungsional.*
5. **Determinism:** dua Execution Scheduler independen dengan Contract yang sama mengambil keputusan yang sama. *Terukur: uji lintas-implementasi.*
6. **Separation of Responsibility:** Execution tidak mendefinisikan aturan idempotency; hanya membaca Contract dan menegakkan. *Terukur: audit batas (D-11).*

---

## Future Reassessment

ADR-003 dapat ditinjau kembali bila:

- muncul bukti (dari Reference Runtime) bahwa Contract-declared idempotency tidak cukup observable untuk kebutuhan Audit/traceability — dan diperlukan mekanisme observabilitas tambahan;
- kandidat C-05 (failure propagation) mengungkap bahwa Execution Conflict sebagai defined failure memerlukan surfacing yang lebih kaya;
- pola operasi di Reference Runtime menunjukkan bahwa sebagian besar operasi bersifat idempotent secara inherent — membuka kemungkinan default-idempotent (inversi safe default);
- Contract validation di tahap implementasi mengungkap risiko false-positive yang tidak dapat dimitigasi oleh Audit drift detection.

Revisi mengikuti lifecycle yang sama (R2-001) tanpa membuka Foundation/Specification.

---

## Related Documents

| Dokumen | Keterangan |
|---|---|
| EXECUTION_SPECIFICATION | Idempotency definition (L167–L177), Lifecycle (L118–L148), Execution Identity (L70–L85), Failure Behaviour (L150–L163), Authority (L56–L66) |
| CONTRACT_SPECIFICATION | Contract sebagai pemilik aturan operasi; ruang untuk deklarasi idempotency sebagai atribut |
| PHILOSOPHY | "Why Determinism Matters" (L307–L353) — determinism sebagai fondasi governance |
| CONSTITUTION | Art. VII Risk Awareness; Art. III Capability Language; Art. IV Discover Not Assume |
| REGISTRY_SPECIFICATION | Discovery idempotency (L129) — preseden idempotency inherent tanpa mekanisme eksplisit |
| BLUEPRINT G0-001 | Candidate C-04 (L157), Execution Scheduler responsibility (L55–L56, L72) |
| R1-002 | Dependency analysis (C-04 Independent, High Ripple) |
| R1-003 | Decision Ordering Validation (C-04 genuinely independent, decidable alone) |
| R2-002 | Candidate Independence Certification (C-04 = A — Certified, atomic, boundary: keys vs semantics) |
| R2-003 | ADR First Decision Selection Record |
| ADR-000 | Deployment Topology (Accepted) |
| ADR-001 | Approval Decision Model (Accepted) |
| ADR-002 | Capability Resolution Policy (Accepted) |
| ADR_TEMPLATE | Struktur ADR (validasi 8 audit, STOP Condition) |
| DECISION_MODEL | Prinsip hierarki keputusan |
| RISK_MODEL | Framework penilaian risiko |
| TRUST_MODEL | Dimensi trust (determinism, explainability, traceability, separation, implementability) |

---

## Validation

### Audit 1 — Problem Coverage
**LULUS.** ADR-003 menjawab pertanyaan tunggal C-04: bagaimana properti idempotency operasi dibuat observable tanpa mekanisme teknis yang dimandatkan. Problem Statement menegaskan ruang keputusan yang sengaja dibuka EXECUTION_SPEC L177. Tidak melebar ke cache, retry, hashing, UUID, token, storage, transport, atau mekanisme implementasi.

### Audit 2 — Alternative Coverage
**LULUS.** Kedua alternatif (A: explicit keys, B: operation-defined semantics) berasal dari trade-off yang direkam G0-001 L157; **tidak ada alternatif baru diciptakan**. Keduanya dianalisis dengan advantages/disadvantages yang berakar pada dokumen (D-04, D-05, D-11). Alternatif mekanis/implementatif (A-01, A-02, A-03 dari G1-001 untuk C-02) tidak relevan untuk C-04 dan tidak dipertimbangkan.

### Audit 3 — Foundation Compliance
**LULUS.** Keputusan berakar pada PHILOSOPHY "Why Determinism Matters" (D-06) dan CONSTITUTION Art. III (capability language), Art. IV (discover not assume), Art. VII (risk awareness). Tidak ada perubahan Foundation; tidak ada pelanggaran prinsip.

### Audit 4 — Specification Compliance
**LULUS.** Keputusan memenuhi EXECUTION_SPEC: idempotency sebagai properti operasi di bawah Contract (D-04, L177), tidak mendikte mekanisme teknis (D-05, L177), Completed tidak di-re-execute kecuali idempotent (D-01, L175), pengulangan = same outcome (D-02, L173), bukan different outcome (D-03, L174). Selaras dengan lifecycle (D-08, D-10) dan Execution authority (D-11).

### Audit 5 — ADR-000 Consistency
**LULUS.** ADR-003 tidak mengubah ADR-000 (Deployment Topology). Model operation-defined semantics berjalan dalam single-cohesive-runtime (ADR-000) tanpa konflik topologi.

### Audit 6 — ADR-001 & ADR-002 Consistency
**LULUS.** ADR-003 tidak mengubah ADR-001 (Approval Decision Model) atau ADR-002 (Capability Resolution Policy). Idempotency tidak melewati Approval gate — pengulangan operasi idempotent tetap memerlukan Approval baru (ADR-001). Resolusi Capability (ADR-002) menyediakan target yang terikat; ADR-003 mengonsumsi hasil resolusi itu tanpa mengubahnya.

### Audit 7 — Implementation Independence
**LULUS.** ADR-003 menetapkan **model arsitektural** (siapa mendeklarasikan, siapa mengamati, aturan pengulangan), bukan mekanisme penyimpanan, algoritma deduplikasi, skema Contract metadata, format kunci, atau protokol token. Konsisten dengan C-04 as a Certified atomic architectural decision (R2-002 Output 6) dan D-05.

### Audit 8 — Final ADR Validation
**LULUS.** ADR-003: (a) menjawab tepat satu pertanyaan; (b) alternatif dari discovery, tidak ada yang diciptakan; (c) driver berakar dokumen (D-01…D-14); (d) tidak mengubah Foundation/Specification/ADR-000/ADR-001/ADR-002; (e) tidak menciptakan authority baru; (f) terdiri dari satu keputusan atomik (R2-002 Output 3: C-04 = A — Certified); (g) memenuhi ADR_TEMPLATE dan 8 audit. **Verdict: ACCEPTED.**

---

## STOP Condition

Berhenti tanpa memaksakan ADR apabila ditemukan salah satu kondisi berikut, dan **hanya laporkan bukti**:

| Trigger | Hadir? | Bukti |
|---|---|---|
| Perlu mengubah Foundation | **Tidak** | Keputusan mengisi ruang yang sengaja dibuka EXECUTION_SPEC L177; tidak menuntut ubah Constitution/Philosophy/Governance |
| Perlu mengubah Specification | **Tidak** | EXECUTION_SPEC L177 sengaja membiarkan mekanisme idempotency terbuka; ADR hanya mengisi dengan model realisasi, tidak mengubah L167–L177 |
| Perlu mengubah ADR-000 | **Tidak** | Topologi (ADR-000) tidak disentuh |
| Perlu mengubah ADR-001 | **Tidak** | Approval framework (ADR-001) tidak diubah; pengulangan tetap melalui Approval gate |
| Perlu mengubah ADR-002 | **Tidak** | Resolusi Capability (ADR-002) tidak diubah; ADR-003 mengonsumsi hasil resolusi |
| Keputusan ternyata bukan satu keputusan | **Tidak** | R2-002 Output 3: C-04 = **1** keputusan atomik (realisasi idempotency) |
| Memerlukan penyelesaian kandidat lain terlebih dahulu | **Tidak** | C-04 independent, decidable alone (R2a/R2e); tidak bergantung pada C-01/C-02/C-03/C-05/C-06/C-07/C-08 |
| Menciptakan authority baru | **Tidak** | ADR adalah kanal subordinat, bukan authority baru; tidak menambah domain/responsibility |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP tidak aktif.** ADR-003 dapat di-accept tanpa mengubah Foundation, Specification, ADR-000, ADR-001, ADR-002, atau menciptakan authority baru.

---

## Review History

| Tanggal | Revisi | Perubahan |
|---|---|---|
| 2026-08-03 | 1.0 | Penulisan awal ADR-003 (C-04 Idempotency Realization Model) |

---

## Author Checklist

- [x] Menjawab **satu** pertanyaan arsitektur (C-04)
- [x] Alternatif diambil dari discovery (G0-001 L157); tidak ada alternatif baru
- [x] Driver berakar dokumen (Foundation + Specification + Blueprint + ADR prior)
- [x] Tidak mengubah Foundation / Specification / ADR-000 / ADR-001 / ADR-002
- [x] Tidak menciptakan authority baru
- [x] Satu keputusan atomik (R2-002 A — Certified)
- [x] Menyertakan Validation (8 audit) dan STOP Condition
- [x] Struktur sesuai ADR_TEMPLATE

---

## Completion Checklist

- [x] Deliverable: `docs/adr/ADR-003_Idempotency_Realization_Model.md`
- [x] 8 audit LULUS
- [x] STOP Condition tidak aktif
- [x] Verdict: **ACCEPTED**
