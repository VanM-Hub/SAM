# ADR-002 — Capability Resolution Policy

| Field | Value |
|---|---|
| **Decision ID** | ADR-002 |
| **Title** | Capability Resolution Policy |
| **Status** | Accepted |
| **Date** | 2026-08-03 |
| **Architecture Domain** | Registry — Capability Resolution |
| **Root Candidate** | C-02 (Capability Resolution Policy) |
| **Decision Type** | Architectural decision (policy) |
| **Owner** | Project SAM |
| **Author** | ZARA |

---

## Purpose

This ADR records the single architectural decision by which the **Registry** determines **which Capability is selected** when more than one Capability satisfies a Capability Request. It resolves Root Candidate **C-02** of Blueprint G0-001.

This ADR answers **one question only**:

> **Bagaimana Registry menentukan Capability yang dipilih ketika lebih dari satu Capability memenuhi permintaan?**

It does **not** expand into algorithmic search, registry structure, caching, indexing, transport, deployment, approval, execution, idempotency, concurrency, or failure propagation. All are out of scope.

---

## Decision Drivers

Drivers are drawn **only** from the frozen Foundation, the Specification Layer, the Blueprint, and the prior ADR records (ADR-000, ADR-001). No assumption outside the documents is used.

| # | Driver | Source |
|---|---|---|
| D-01 | Registry SHALL select exactly one candidate **deterministically** when multiple candidates are equally valid, so that two registries given the same input select the same result. | REGISTRY_SPEC L147/L149 |
| D-02 | Resolution SHALL be **deterministic** given the same registry content and the same request. | REGISTRY_SPEC L148/L149 |
| D-03 | A candidate SHALL match the requested Capability. | REGISTRY_SPEC L143 |
| D-04 | A candidate SHALL have a **compatible version**. | REGISTRY_SPEC L144 |
| D-05 | A **non-deprecated** candidate SHALL be preferred over a deprecated candidate. | REGISTRY_SPEC L145 |
| D-06 | A **suspended or removed** object SHALL NOT be a candidate. | REGISTRY_SPEC L146 |
| D-07 | Discovery SHALL be **idempotent**; an identical request SHALL produce an identical result; Discovery SHALL NOT have side effects on registered objects. | REGISTRY_SPEC (Discovery Protocol) |
| D-08 | Registry SHALL resolve to a version **compatible with the request**; if no compatible version exists, return **Version Mismatch**. | REGISTRY_SPEC L157/L160 |
| D-09 | Registry SHALL NOT satisfy a request with a **contract-incompatible** version (major version change = contract incompatibility). | REGISTRY_SPEC L159 |
| D-10 | **Determinism has higher priority than convenience.** | CONSTITUTION Art. VII |
| D-11 | Capabilities are the **universal language**; Discovery, Registry, and Selection operate on capabilities, never implementation details. | CONSTITUTION Art. III |
| D-12 | Citizens **discover, never assume**; a Citizen should never know another Citizen directly. Communication occurs through Registry and Discovery. | CONSTITUTION Art. IV |
| D-13 | Same input, same contracts, same policies, **same output**. Hidden randomness and implicit context are violations. | CONSTITUTION Art. VII |
| D-14 | Each Capability has a **globally unique identifier** (recommended `<domain>.<category>.<capability>`) and is **versioned**. | CAPABILITY_SPEC (Identity, Constitutional Principles) |
| D-15 | Capabilities evolve via **Patch → Minor → Major**; breaking compatibility requires explicit architectural review; backward compatible whenever practical. | CAPABILITY_SPEC (Evolution) |
| D-16 | Registry is **discovery and resolution only**; it does not decide whether an operation is approved, does not execute. | REGISTRY_SPEC (Boundaries); GOVERNANCE H-01 |
| D-17 | Discovery input is a single **Capability Request**; extra implicit context is a constitutional violation. | REGISTRY_SPEC (Discovery Protocol); CONSTITUTION Art. VII |

---

## Context

### Status fase

Project SAM telah menyelesaikan dua keputusan arsitektur inti:

- **ADR-000 — Deployment Topology** (Accepted): satu Runtime cohesive per domain (Alternative A).
- **ADR-001 — Approval Decision Model** (Accepted): Accountable Decision Framework (Alternative C) untuk Approval Coordinator.

Root Candidate **C-02 — Capability Resolution Policy** telah dianalisis selama Discovery:

- **G1-001** — ADR Candidate C-02 Analysis: merumuskan problem statement, mengumpulkan seluruh constraint, mengidentifikasi 7 alternatif (A-01…A-07), menganalisis trade-off, dan mendaftar 6 fakta yang belum tersedia.
- **G1-002** — C-02 Decision Discovery: menguji 6 fakta tersebut, menemukan struktur keputusan tersembunyi, dan mempersempit C-02 menjadi **satu keputusan inti**.
- **R2-002** — Candidate Independence Certification: mengesahkan C-02 sebagai **A — Certified** (satu keputusan arsitektur atomik).

Pemilihan ADR-002 sebagai ADR ketiga adalah **Chief Architect Process Decision**, sesuai R1-003 (Several Equivalent = {C-02, C-03, C-04, C-06}) dan R2-003 (Selection Record).

### Inti keputusan C-02 (dari G1-001/G1-002)

Dari enam "fakta yang hilang" (F1–F6) yang diidentifikasi G1-001, G1-002 menunjukkan hanya **satu keputusan arsitektural sesungguhnya** yang lahir sebagai ADR C-02:

> **Aturan seleksi tunggal Registry untuk memilih satu kandidat dari banyak yang cocok — prioritas exact-vs-compatible plus basis urutan deterministik yang mengafirmasi kunci identitas+versi yang sudah menjadi properti inherent Capability.**

| Fakta | Nasib |
|---|---|
| F1 (prioritas exact vs compatible) | **Keputusan inti** |
| F3 (semantik availability) | **Satu keputusan dengan F1** (sisi kebalikan) |
| F2 (basis urutan deterministik) | **Diafirmasi dalam F1-ADR** (kunci identitas+versi sudah inherent, H-09) |
| F4 (re-resolution trigger) | **Mekanisme** → Impl/ADR C-03, bukan keputusan C-02 |
| F5 (cakupan konteks) | **Afirmasi Specification** → sudah ditetapkan (input = Capability Request saja) |
| F6 (titik observasi) | **Berpindah ke C-01/C-08** (ordering/verification), bukan C-02 |

Dengan demikian, ADR-002 hanya menetapkan **satu** keputusan: kebijakan prioritas pemilihan Capability beserta basis urutan deterministiknya.

---

## Problem Statement

Ketika lebih dari satu Capability memenuhi satu Capability Request — khususnya ketika terdapat baik kandidat yang **sama persis** (exact match) maupun kandidat yang **hanya kompatibel versi** (version-compatible match) — Registry harus memilih **satu** Capability secara deterministik.

Registry Specification **menetapkan** bahwa:

- pemilihan harus deterministik (D-01, D-02);
- kandidat non-deprecated dipilih atas yang deprecated (D-05);
- objek suspended/removed bukan kandidat (D-06);
- versi harus kompatibel dan tidak boleh contract-incompatible (D-04, D-09);
- jika tidak ada versi kompatibel, kembalikan Version Mismatch (D-08).

Tetapi Specification **tidak menetapkan** urutan prioritas antara **exact match** dan **version-compatible match** ketika keduanya ada (F1 dari G1-001 Audit 6). Ini adalah **ruang keputusan yang sengaja dibuka** oleh baseline — bukan cacat dokumen, melainkan keputusan arsitektural yang memang menjadi isi ADR-002.

Tanpa keputusan ini, dua Registry dengan isi dan permintaan sama dapat memilih hasil berbeda — melanggar D-01/D-02 dan Art. VII (D-13), serta mengancam kebenaran rantai Approval–Execution–Audit yang bergantung pada target resolusi yang **stabil dan terikat**.

---

## Alternatives Considered

Alternatif yang dianalisis diambil **berasal dari discovery yang sudah ada** (G1-001 Audit 3, ± A-01…A-07). **Tidak ada alternatif baru yang diciptakan.** Hanya alternatif yang berada dalam ruang keputusan inti C-02 (prioritas exact-vs-compatible) yang dipertimbangkan untuk pemilihan akhir; alternatif yang menyangkut mekanisme (A-01/A-02/A-03), delegasi (A-05), atau governance (A-07) diklasifikasi ulang per G1-002 dan disingkirkan dari keputusan ini.

### Alternative A — Exact-Match-Preferred (precision over availability)

**Reference:** G1-001 A-04 (Deterministic resolution / exact-match-first).

Kandidat dengan **exact match** dipilih lebih dulu; kandidat hanya-kompatibel dipertimbangkan hanya jika tidak ada exact match.

**Advantages**
- Presisi tertinggi: memenuhi persis apa yang diminta requester.
- Determinism mudah dijaga: rule mereduksi menjadi exact match, lalu tie-break deterministik.
- Selaras dengan Art. VII "same output" (D-13) dan D-01/D-02.
- Kontrak menjadi version-exact; negosiasi sederhana.

**Disadvantages**
- Availability lebih rendah bila exact match tidak ada tetapi kompatibel ada.

**Assessment**
Valid dan konstitusional (G1-001 Audit 5: A-04 ✅ seluruh sumber). Mewujudkan posture presisi-di-atas-ketersediaan.

### Alternative B — Compatibility-Preferred (availability over exact)

**Reference:** G1-001 A-06 (Compatibility-preferred resolution).

Kandidat **version-compatible** dapat memenuhi permintaan bahkan ketika exact match tidak ada, dengan versi kompatibel diutamakan sebagai hasil yang sah.

**Advantages**
- Availability lebih tinggi; requester lebih sering memperoleh Capability yang dapat dipakai.
- Menghormati desain evolusi versi (Patch→Minor→Major, D-15).

**Disadvantages**
- Presisi lebih lemah: requester mendapat *sebuah* versi kompatibel, bukan selalu yang persis diminta.
- Perlu aturan eksplisit agar tetap deterministik (Art. VII, D-13).

**Assessment**
Valid dan konstitusional jika dibatasi aturan eksplisit (G1-001 Audit 5: A-06 ✅). Mewujudkan posture ketersediaan.

### Perlakuan alternatif lain (dari G1-001/G1-002 — bukan alternatif pemilihan final)

| Alternatif | Reference | Status dalam ADR-002 |
|---|---|---|
| A-01 Eager resolution | G1-001 A-01 | Mekanisme (kapan bind), bukan prioritas → di luar keputusan ini |
| A-02 Lazy resolution | G1-001 A-02 | Kondisional; menyangkut titik observasi → terkait C-01/C-08, bukan C-02 |
| A-03 Cached resolution | G1-001 A-03 | Mekanisme (re-resolution / observasi content change) → Impl/ADR C-03 |
| A-05 Delegated resolution | G1-001 A-05 | Risiko konstitusional (Art. IV/VII implicit context) → tidak dipertimbangkan untuk prioritas |
| A-07 Admin-governed resolution | G1-001 A-07 | Governance dalam resolusi → harus tetap di batas Registry; bukan isi prioritas inti |

---

## Decision

**DIPUTUSKAN:** Registry mengadopsi **kebijakan prioritas "exact-match-preferred dengan fallback kompatibel deterministik"** untuk resolusi Capability:

1. **Kandidat yang ditolak lebih dulu** (dari D-05, D-06): objek suspended/removed bukan kandidat; kandidat deprecated hanya dipilih bila tidak ada kandidat non-deprecated.
2. **Exact match diutamakan**: jika ada kandidat yang **sama persis** dengan Capability yang diminta (Capability Identity + versi sesuai request), Registry memilih dari himpunan exact-match terlebih dahulu.
3. **Fallback kompatibel**: jika tidak ada exact match, Registry mempertimbangkan kandidat **version-compatible** (D-04, D-08), asalkan contract-compatible (D-09) dan non-deprecated ketika tersedia.
4. **Tie-break deterministik**: bila masih ada beberapa kandidat yang sama valid (mis. beberapa versi kompatibel sama-sama non-deprecated), Registry memilih **satu** secara deterministik menggunakan **basis urutan yang inherent pada Capability**: urutan identitas unik (D-14) lalu urutan versi (D-14, D-15). Basis ini selalu menghasilkan **satu pemenang** untuk isi Registry yang sama dan request yang sama (D-01, D-02).
5. **Tidak ada konteks implisit**: resolusi hanya menerima **Capability Request** sebagai input (D-17); tidak ada konteks di luar request yang memengaruhi seleksi.
6. **Idempotensi & tanpa side-effect**: resolusi tidak mengubah objek terdaftar dan identik untuk request identik (D-07).

**Ringkas:** Registry memilih **satu Capability** dari yang cocok dengan aturan — *exact preferred, lalu compatible, lalu deterministik tie-break oleh identitas+versi* — sehingga dua Registry dengan isi dan request yang sama **selalu memilih hasil yang sama**.

---

## Architectural Rationale

1. **Determinism sebagai prioritas tertinggi (D-10, D-13).** Basis urutan identitas+versi (D-14) menjamin satu pemenang deterministik tanpa memperkenalkan konteks implisit, memenuhi D-01/D-02 dan Art. VII.
2. **Exact-match-preferred menegaskan presisi tanpa mengorbankan determinism (A-04).** Ketika requester meminta Capability tertentu, memilih exact match adalah interpretasi paling literal dari "same input, same output" (D-13). Ini menjaga kebenaran rantai Approval–Execution–Audit: target resolusi yang stabil dan terikat apa yang disetujui dan dieksekusi.
3. **Fallback kompatibel melestarikan ketersediaan yang sah (A-06, D-15).** Spesifikasi memang merancang resolusi ke "versi kompatibel dengan request" (D-08) dan evolusi melalui versi (D-15). Menerima kompatibel saat exact tidak ada menghormati desain itu tanpa memilih one-extreme A-06-pure yang memaksa kompatibel-di-atas-persis.
4. **Separation of responsibility terjaga (D-16).** Registry tetap discovery/resolution only; keputusan prioritas ini tidak menyerobot Approval (ADR-001), Execution, atau Audit. Ia hanya menetapkan *siapa yang dipilih*, bukan *apakah operasi disetujui*.
5. **Implementasi independen (per R2-002).** ADR-002 menetapkan **kebijakan** (prioritas + basis urutan), bukan algoritma pencarian, struktur indeks, atau mekanisme teknis — konsisten dengan C-02 as a Certified atomic architectural decision, dan dengan prinsip Implementation Independence (Audit 7).
6. **Selaras dengan prior yang sudah diterima.** ADR-000 (topologi) dan ADR-001 (approval) tidak diubah; ADR-002 hidup di ruang yang sengaja dibuka REGISTRY_SPEC (L147/L149) dan tidak membutuhkan perubahan Foundation/Specification.

---

## Consequences

### Positive

- **Determinisme lintas-implementasi:** dua Registry independen menghasilkan hasil yang sama untuk isi & request yang sama (D-01, D-02, Interoperability REGISTRY_SPEC).
- **Presisi dan ketersediaan seimbang:** exact match menegaskan presisi; fallback kompatibel menjaga ketersediaan, keduanya di bawah determinism (D-10).
- **Kebenaran rantai Approval–Execution–Audit:** target resolusi terikat dan stabil dari depan, selaras dengan ADR-001 (Approval bekerja pada Capability ter-resolusi).
- **Separation of responsibility:** Registry tetap dalam batas discovery/resolution (D-16); tidak menyerobot keputusan lain.

### Negative

- **Requester bisa menerima versi kompatibel (bukan persis) ketika exact tidak ada** — trade-off ketersediaan yang diterima secara eksplisit (Acceptable Trade-off).
- **Kebijakan mengandalkan identitas & versi yang terdefinisi baik** — Capability yang tidak memenuhi D-14 dapat menyulitkan tie-break (namun D-14 menetapkan identitas unik sebagai sifat inherent).

### Accepted Trade-offs

| Trade-off | Pilihan | Rasional |
|---|---|---|
| Precision vs Availability | **Precision-first** (exact preferred), availability via fallback kompatibel | D-10 determinism > convenience; D-13 same output |
| Determinism vs Flexibility | **Determinism** (basis identitas+versi) | D-01/D-02/D-10 menetapkan determinism sebagai keharusan |
| Registry-simplicity vs Governance-input | **Registry-simplicity** (input = request saja, D-17) | Art. VII implicit-context adalah violation |

---

## Impact Analysis

| Area | Dampak |
|---|---|
| **Discovery Resolver** | Menerapkan kebijakan prioritas exact→compatible→tie-break identitas+versi pada titik resolusi (R1-002 L108: "Discovery behavior shapes Discovery Resolver design"). |
| **Registry** | Behavioural rule tentang seleksi; tidak mengubah struktur penyimpanan atau algoritma pencarian (REGISTRY_SPEC: "does not prescribe a storage or matching algorithm"). |
| **Contract** | Negosiasi versi berjalan dengan basis identitas+versi; versi contract-compatible dijamin (D-09); preferensi non-deprecated terjaga. |
| **Runtime** | Mendapat target resolusi yang terikat dan deterministik untuk Approval/Execution; selaras dengan ADR-000 (single cohesive runtime) dan ADR-001 (approval gate). |
| **Audit** | Resolusi yang deterministik & idempoten (D-07) mendukung traceability; hasil resolusi dapat direproduksi. |
| **Future ADR (C-01/C-05/C-07/C-08)** | Menyediakan fondasi: C-01 (ordering) dan C-08 (verification point) mengonsumsi hasil resolusi; C-05 (failure) mendapat sumber failure resolusi yang jelas. Tidak membuka kembali Foundation/Specification. |

---

## Dependency Impact

- **C-02 tidak memiliki dependency masuk** (R2-002 Output 4, R2a/R2e: decidable alone, no hidden dependency).
- **C-02 mempengaruhi keluar** (R2-002 Output 7): C-05 (sumber failure resolusi, R1-002 L54); selaras dengan C-01/C-08 (observasi hasil resolusi).
- **Tidak ada perubahan pada ADR-000 (topologi) dan ADR-001 (approval).** ADR-002 hidup dalam ruang yang sengaja dibuka REGISTRY_SPEC dan tidak menyentuh keputusan root lain.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation / Notes |
|---|---|---|---|
| Regresi determinism akibat fallback kompatibel | Low | Very High | Basis urutan identitas+versi (D-14) menjamin satu pemenang; re-verifikasi via Audit 8 + test determinism lintas-implementasi |
| Ambiguity tie-break antar versi kompatibel setara | Low | Medium | Urutan versi (D-14/D-15) menetapkan basis; non-deprecated preferred (D-05) mempersempit himpunan |
| Kesalahan interpretasi "exact" vs "compatible" | Low | Medium | Definisi diperjelas di Decision (identitas + versi sesuai request) |
| Ketergantungan pada identitas/versi yang buruk | Low | Medium | D-14 menetapkan identitas unik sebagai sifat inherent; kepatuhan dimonitor |
| Risiko konstitusional (implicit context) | Very Low | High | D-17: input = Capability Request saja; tidak ada konteks implisit |

**Kesimpulan risiko:** 4 risiko Low, 1 risiko Very Low. Dampak tertinggi (determinism regression) di-mitigasi oleh basis identitas+versi yang inherent dan pasti menghasilkan satu pemenang. **Reversibel** — keputusan prioritas dapat diubah ADR turunan tanpa mengubah Foundation/Specification.

---

## Trust Analysis

| Dimensi | Assessment |
|---|---|
| **Determinism** | Confidence **High** — basis identitas+versi adalah properti Capability yang sudah ditetapkan (D-14), bukan sumber acak/implisit |
| **Explainability** | Confidence **High** — rule prioritas eksplisit (exact→compatible→tie-break) dapat dijelaskan dan di-audit |
| **Traceability** | Confidence **High** — resolusi berakar pada REGISTRY_SPEC (L143–L160), Art. VII, dan G1-001/G1-002/R2-002 |
| **Separation of Responsibility** | Confidence **High** — batas Registry discovery/resolution only dipertahankan (D-16) |
| **Implementability** | Confidence **High** — menetapkan policy, bukan mekanisme teknis; implementasi bebas algoritma/struktur |

---

## Implementation Notes

- **Fokus implementasi:** titik resolusi Discovery Resolver menerapkan urutan prioritas exact→compatible→tie-break identitas+versi.
- **Tidak menetapkan:** algoritma pencarian, struktur indeks, cache, storage, transport, deployment, mekanisme marking deprecation.
- **Kunci stabilitas:** gunakan Capability Identity unik + versi sebagai basis urutan deterministik yang stabil terhadap isi Registry.
- **Dapatkan dari Specification:** preferensi non-deprecated (D-05), penolakan suspended/removed (D-06), contract-compatible (D-09), Version Mismatch bila tak ada kompatibel (D-08).
- **Interoperabilitas:** verifikasi bahwa dua Registry independen memilih hasil sama untuk isi & request sama (REGISTRY_SPEC Interoperability).

---

## Migration Strategy

- **No breaking change pada Foundation/Specification/ADR-000/ADR-001** — ADR-002 mengisi ruang yang sengaja dibuka, tidak mengubah baseline beku.
- **Adoption:** perilaku resolusi Deterministic Resolver disesuaikan dengan kebijakan prioritas ini; kandidat sesuai G1-001 A-04/A-06 yang sebelumnya setara kini memiliki urutan yang jelas.
- **Verifikasi:** jalankan uji determinism (request identik → hasil identik) dan uji prioritas (exact preferred atas compatible; compatible saat exact hilang; tie-break identitas+versi) lintas dua implementasi Registry.
- **Evolusi lanjut:** kebijakan ini dapat direvisi lewat ADR turunan tanpa menyentuh baseline.

---

## Success Criteria

1. **Determinism:** dua Registry dengan isi dan request yang sama memilih hasil yang sama (D-01/D-02). *Terukur: uji lintas-implementasi.*
2. **Presisi:** Ketika exact match tersedia, Registry memilih exact match. *Terukur: uji prioritas.*
3. **Ketersediaan:** Ketika exact tidak ada namun kompatibel ada, Registry memilih kandidat kompatibel (bukan Version Mismatch). *Terukur: uji fallback.*
4. **Kepatuhan Specification:** non-deprecated preferred; suspended/removed ditolak; contract-compatible dijamin; Version Mismatch hanya saat tak ada kompatibel. *Terukur: audit terhadap REGISTRY_SPEC L143–L160.*
5. **Ketidaktergantungan implementasi:** keputusan berlaku tanpa menetapkan algoritma/struktur/cache/transport. *Terukur: review bahwa implementasi bebas memilih mekanisme.*
6. **Separation of responsibility:** Registry tetap discovery/resolution only; tidak menyerobot Approval/Execution/Audit. *Terukur: audit batas (D-16).*

---

## Future Reassessment

ADR-002 dapat ditinjau kembali bila:

- muncul bukti (dari Reference Runtime) bahwa fallback kompatibel menimbulkan regresi determinism atau menyulitkan traceability;
- kandidat C-01 (ordering) atau C-08 (verification point) mengungkap kebutuhan penyesuaian titik observasi hasil resolusi (F6 yang dipindahkan ke C-01/C-08);
- model governance membutuhkan precedence tambahan dalam resolusi (namun harus tetap di batas Registry, tidak menyerobot Approval).

Revisi mengikuti lifecycle yang sama (R2-001) tanpa membuka Foundation/Specification.

---

## Related Documents

| Dokumen | Keterangan |
|---|---|
| CONSTITUTION | Art. III, IV, VII, IX (capability language, discovery-not-assume, determinism, runtime independence) |
| REGISTRY_SPECIFICATION | Discovery Protocol, Resolution Rules (L143–149), Version Compatibility (L157–160), Failure Behaviour, Boundaries |
| CAPABILITY_SPECIFICATION | Constitutional Principles, Identity (D-14), Evolution (D-15), Discovery |
| CONTRACT_SPECIFICATION | Compatibility Rules, Version Negotiation |
| BLUEPRINT G0-001 | Candidate C-02 (L155), Discovery Resolver component |
| G1-001 | C-02 Analysis (alternatives A-01…A-07, trade-off, readiness, F1–F6) |
| G1-002 | C-02 Decision Discovery (six facts → one core decision; F1/F3/F2 collapsed) |
| R1-002 | Dependency analysis (C-02 Independent, influences C-05) |
| R1-003 | Several Equivalent = {C-02, C-03, C-04, C-06} |
| R2-002 | Candidate Independence Certification (C-02 = A — Certified, atomic) |
| R2-003 | ADR First Decision Selection Record (process decision to write ADRs) |
| ADR-000 | Deployment Topology (Accepted) |
| ADR-001 | Approval Decision Model (Accepted) |
| ADR_TEMPLATE | Struktur ADR (validasi 8 audit, STOP Condition) |
| DECISION_MODEL | Prinsip hierarki keputusan (Constitution → Governance → Architecture → …) |

---

## Validation

### Audit 1 — Problem Coverage
**LULUS.** ADR-002 menjawab pertanyaan tunggal C-02: bagaimana Registry memilih satu Capability ketika lebih dari satu memenuhi request. Problem Statement (bagian Problem Statement) menegaskan ruang keputusan yang sengaja dibuka (F1) dan konsekuensi jika tidak diputuskan. Tidak melebar ke algoritma/struktur/cache/transport/deployment/approval/execution/idempotency/concurrency/failure propagation.

### Audit 2 — Alternative Coverage
**LULUS.** Semua alternatif yang dipertimbangkan berasal dari discovery G1-001 (A-01…A-07); **tidak ada alternatif baru diciptakan**. Dua posture final (exact-preferred A-04 dan compatible-preferred A-06) keduanya dianalisis; alternatif mekanisme/delegasi/governance diklasifikasi ulang sesuai G1-002 dan dinyatakan di luar keputusan inti ini.

### Audit 3 — Foundation Compliance
**LULUS.** Keputusan berakar pada CONSTITUTION Art. III (capability language), IV (discover not assume), VII (determinism, same output, implicit context violation), IX (runtime independence). Tidak ada perubahan Foundation; tidak ada pelanggaran prinsip.

### Audit 4 — Specification Compliance
**LULUS.** Keputusan memenuhi REGISTRY_SPEC: deterministik (L147/L149), exact-one (L147), non-deprecated preferred (L145), suspended/removed excluded (L146), compatible version (L144), contract-compatible (L159), Version Mismatch bila tak ada kompatibel (L160), idempotent/no-side-effect (Discovery Protocol), input = Capability Request saja (D-17). Konsisten dengan CAPABILITY_SPEC (identity, versioned, evolution) dan CONTRACT_SPEC (version negotiation).

### Audit 5 — ADR-000 Consistency
**LULUS.** ADR-002 tidak mengubah ADR-000 (Deployment Topology). Resolusi idioma dalam single-cohesive-runtime (ADR-000) berjalan natural; tidak ada konflik topologi.

### Audit 6 — ADR-001 Consistency
**LULUS.** ADR-002 tidak mengubah ADR-001 (Approval Decision Model). Resolusi menyediakan target terikat untuk Approval; ADR-001 menetapkan *bagaimana* keputusan approval dihitung (Accountable Decision Framework), sedangkan ADR-002 menetapkan *siapa targetnya*. Keduanya komplementer; batas Registry (D-16) menjamin tak ada overlap dengan approval gate.

### Audit 7 — Implementation Independence
**LULUS.** ADR-002 menetapkan **kebijakan** (prioritas + basis urutan), bukan algoritma pencarian, struktur indeks, cache, storage, transport, atau mekanisme teknis (REGISTRY_SPEC: "does not prescribe a storage or matching algorithm"). Konsisten dengan C-02 as a Certified atomic architectural decision (R2-002 Output 6).

### Audit 8 — Final ADR Validation
**LULUS.** ADR-002: (a) menjawab tepat satu pertanyaan; (b) alternatif dari discovery, tidak ada yang diciptakan; (c) driver berakar dokumen (D-01…D-17); (d) tidak mengubah Foundation/Specification/ADR-000/ADR-001; (e) tidak menciptakan authority baru; (f) terdiri dari satu keputusan atomik (R2-002 Output 3: C-02 = A — Certified); (g) memenuhi ADR_TEMPLATE dan 8 audit. **Verdict: ACCEPTED.**

---

## STOP Condition

Berhenti tanpa memaksakan ADR apabila ditemukan salah satu kondisi berikut, dan **hanya laporkan bukti**:

| Trigger | Hadir? | Bukti |
|---|---|---|
| Perlu mengubah Foundation | **Tidak** | Keputusan mengisi ruang yang sengaja dibuka REGISTRY_SPEC (L147/L149); tidak menuntut ubah Constitution/Philosophy/Governance |
| Perlu mengubah Specification | **Tidak** | REGISTRY_SPEC sengaja membiarkan prioritas exact-vs-compatible terbuka (F1); ADR hanya mengisinya, tidak mengubah L143–L160 |
| Perlu mengubah ADR-000 | **Tidak** | Topologi (ADR-000) tidak disentuh; resolusi idioma dalam single-cohesive-runtime |
| Perlu mengubah ADR-001 | **Tidak** | Approval framework (ADR-001) tidak diubah; ADR-002 memberikan target resolusi yang komplementer |
| Keputusan ternyata bukan satu keputusan | **Tidak** | R2-002 Output 3: C-02 = **1** keputusan atomik; G1-002 mempersempit 6 fakta → 1 keputusan inti |
| Memerlukan penyelesaian C-04 terlebih dahulu | **Tidak** | C-02 independent, decidable alone (R2a/R2e); tidak bergantung pada C-04 (Idempotency) |
| Menciptakan authority baru | **Tidak** | ADR adalah kanal subordinat (G1a/F1a), bukan authority baru; tidak menambah domain/responsibility |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP tidak aktif.** ADR-002 dapat di-accept tanpa mengubah Foundation, Specification, ADR-000, ADR-001, atau menciptakan authority baru.

---

## Review History

| Tanggal | Revisi | Perubahan |
|---|---|---|
| 2026-08-03 | 1.0 | Penulisan awal ADR-002 (C-02 Capability Resolution Policy) |

---

## Author Checklist

- [x] Menjawab **satu** pertanyaan arsitektur (C-02)
- [x] Alternatif diambil dari discovery (G1-001); tidak ada alternatif baru
- [x] Driver berakar dokumen (Foundation + Specification + Blueprint + ADR prior)
- [x] Tidak mengubah Foundation / Specification / ADR-000 / ADR-001
- [x] Tidak menciptakan authority baru
- [x] Satu keputusan atomik (R2-002 A — Certified)
- [x] Menyertakan Validation (8 audit) dan STOP Condition
- [x] Struktur sesuai ADR_TEMPLATE

---

## Completion Checklist

- [x] Deliverable: `docs/adr/ADR-002_Capability_Resolution_Policy.md`
- [x] 8 audit LULUS
- [x] STOP Condition tidak aktif
- [x] Verdict: **ACCEPTED**
