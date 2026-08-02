# ADR-001 — Approval Decision Model

Version: 0.1.0

Status: Accepted

Decision Date: 2026-08-03

Author: Chief Architect (Project SAM Architecture Decision Making)

Reviewers: — (opened for architectural review)

Related ADRs: ADR-000 (Deployment Topology — Accepted; konfigurasi deployment bukan konteks model keputusan ini)

Related Documents: MISSION, CONSTITUTION (Article VII determinism & bounded judgment), GOVERNANCE (Runtime Governance, Long-Term Governance), APPROVAL_SPECIFICATION (S-03), DECISION_MODEL, RISK_MODEL, TRUST_MODEL, G0-001_Reference_Runtime_Blueprint (C-03), R1-001_Minimal_Reference_Runtime_Design, R1-002_Candidate_ADR_Dependency_Analysis, R1-003_ADR_Decision_Ordering_Validation, R2-001_ADR_Decision_Process_Definition, R2-002_ADR_Candidate_Independence_Certification, R2-003_ADR_First_Decision_Selection_Record, ADR-000

Related Modules: Approval Coordinator (primary), Execution Scheduler (ordering context), Audit Recorder (accountability), Runtime (bounding)

---

# Purpose

Mendefinisikan keputusan arsitektur kedua Project SAM: **Model Keputusan Approval (Approval Decision Model)** — bagaimana **Approval Coordinator menghasilkan sebuah keputusan Approval secara arsitektural**. ADR ini menjawab **satu** pertanyaan arsitektur (mekanisme perhitungan keputusan Approval / C-03) dan **tidak** membahas Capability Resolution (C-02), Idempotency (C-04), Concurrency/Ordering (C-01), Failure Propagation (C-05), Deployment Topology (ADR-000), External Access (C-07), Verification Placement (C-08), algoritma implementasi, bahasa, teknologi, UI, transport, database — semuanya di luar scope.

Ini adalah **keputusan arsitektur** (bukan analisis/audit/proposal) dan dijamin **tidak bertentangan dengan baseline beku** (SPECIFICATION_FREEZE, GOVERNANCE, Specification) dan **tidak bertentangan dengan ADR-000**.

---

# Context

## Mengapa Specification sengaja membuka cara menghasilkan keputusan Approval

- **APPROVAL_SPEC L109** (S-03, jalur determinism-open): *"The decision is the outcome of the Approval process. This specification **does not prescribe how the decision is computed**."* — Approval Specification sengaja **meninggalkan mekanisme perhitungan** sebagai ruang keputusan, bukan menetapkannya.
- **Blueprint C-03 L156**: C-03 "**Approval decision computation** — How the Approval Coordinator produces a decision (this is **explicitly not prescribed** by the Approval Specification). Trade-off between **automated and human-mediated authorization**."
- **Blueprint L177**: "Approval decision computation not prescribed — Documented — **Explicitly out of scope** of the Approval Specification; a Candidate ADR (C-03)."
- **R2-002 B-C03**: C-03 adalah pertanyaan desain resmi; **S-03** (L109) membuktikan mekanisme tidak dibatasi.

## Apa yang Specification TETAPKAN (dictum — bukan ruang keputusan)

Approval Specification menetapkan hal-hal berikut sebagai **tetap**, yang menjadi **konteks/batas** model keputusan (bukan yang diputuskan di sini):

- **Approval = keputusan otorisasi** yang mendahului eksekusi Capability (L24, L56, L201).
- **Approval adalah gerbang antara niat dan eksekusi** (L60, L207); menghasilkan keputusan **mengikat** (binding) — L56 "binding authorization decision".
- **State keputusan tetap (deterministik dalam bentuk output):** `Approved`, `Rejected`, `Expired`, `Cancelled`, `Superseded` (L101-L106). Approval menghasilkan **salah satu** state ini; bentuk output deterministik.
- **Approval tidak melakukan eksekusi** (L26, L209): tidak menjalankan operasi, tidak discover, tidak definisikan Contract, tidak merekam audit — pemisahan tanggung jawab (separation of responsibility).
- **Kegagalan terdefinisi bukan keputusan tak disengaja** (L146): "The Approval process SHALL return a defined failure rather than an unintended decision."
- **Tidak boleh di-bypass** (L201): operasi hanya boleh dieksekusi setelah Approval menghasilkan decision.
- **Determinism mandat dari Article VII** (Constitution) + REGISTRY (S-02) berlaku bagi resolusi; Approval **memproduksi keputusan deterministik dalam bentuk** (state), dirumuskan lewat mekanisme yang terbuka.

## Status fase

Foundation **CLOSED** → Specification **FROZEN** → Architecture Discovery **CLOSED** → ADR Process **DEFINED** (R2-001) → Candidate Certification **PASSED** (R2-002: C-03 = **A — Certified**) → Selection Record **READY** (R2-003) → **ADR-000 Accepted** (Deployment Topology). Chief Architect telah mengambil keputusan proses: **ADR-001 = C-03 Approval Decision** (keputusan proses per R1-003/R2-003; C-03 adalah salah satu dari Several Equivalent root; bukan architectural necessity, bukan karena kandidat lain kurang penting).

---

# Problem Statement

**Pertanyaan arsitektur yang harus dijawab:** Bagaimana **Approval Coordinator** menghasilkan sebuah **keputusan Approval** secara arsitektural — dengan kata lain, **mekanisme perhitungan keputusan otorisasi** (automated vs human-mediated) seperti apa yang didukung arsitektur, tanpa mengubah baseline beku?

Masalah ini bersifat **arsitektural** (sifat gerbang otorisasi — human-vs-auto adalah trade-off arsitektural; R2-002 Output 6 "Architectural Purity: C-03 = Ya"), **objektif**, dan dibatasi pada **model keputusan**. Ia **bukan** masalah *bagaimana* tiap komponen diimplementasikan (di luar scope).

---

# Decision Drivers

Driver berikut **diekstrak hanya dari dokumen** — hanya yang didukung:

| Driver | Dukungan dokumen |
|---|---|
| **Accountability** | Approval menghasilkan keputusan yang **mengikat** (binding; S-03 L56) dan merupakan **gate** yang tidak boleh di-bypass (L201). Keputusan harus dapat dipertanggungjawabkan (dapat dijelaskan) — sejalan dengan DECISION_MODEL "Maximum Explainability" + "Trust Before Recommendation". |
| **Determinism (dalam bentuk output)** | S-03 L99-L109: Approval memproduksi **salah satu state tetap** (Approved/Rejected/Expired/Cancelled/Superseded) — bentuk keputusan deterministik meski mekanisme terbuka; CONSTITUTION Article VII determinism. |
| **Bounded responsibility** | GOVERNANCE Runtime Governance: "own one bounded responsibility"; S-03 L28/L209: Approval = otorisasi SAJA (bukan discovery/execution/audit) — pemisahan tanggung jawab. |
| **Separation of responsibility** | S-03 L28 (Ada batas tegas antara Approval vs Registry vs Contract vs Execution); R1-002 L106: Approval = "the singular gate of the chain". Model keputusan tidak menyerobot peran komponen lain. |
| **Auditability** | AUDIT_SPEC Traceability; GOVERNANCE "participate in auditing"; Approval menghasilkan keputusan yang harus dapat dilacak (accountable). Model keputusan harus mendukung audit (keputusan tercatat/konsisten). |
| **Implementation independence** | S-03 L109 "does not prescribe how decision computed"; R1-001 L63 batas structural tidak memaksakan mekanisme; ADR tidak menetapkan implementasi, bahasa, teknologi, transport, database. |

Catatan: driver yang **tidak** didukung dokumen (mis. "automation selalu lebih baik", "harus full human review", "trade speed vs safety") **tidak** dipakai sebagai justifikasi — konsisten dengan R2-002/R2-003 (larang preferensi teknologi/opini/kemudahan).

---

# Alternatives Considered

Berikut adalah **seluruh alternatif yang telah ditemukan** selama Discovery untuk C-03 (Blueprint C-03 L156 trade-off; R1-002 L106/L50-51; R1-004 L59; R2-002; R2-003 L37). **Tidak ada alternatif baru yang diciptakan.**

## Alternative A — Human-Mediated Authorization (keputusan melalui keterlibatan manusia)

### Advantages
- **Oversight tinggi:** keputusan otorisasi di bawah pertimbangan manusia — selaras dengan DECISION_MODEL "Human Oversight" dan "Convenience should never override safety".
- **Accountability natural:** jejak pengambilan keputusan manusia mudah dijelaskan/dipertanggungjawabkan (DECISION_MODEL "Maximum Explainability").
- **Cocok untuk otorisasi berisiko tinggi** (decisi safety-critical di mana pengambilan keputusan otomatis penuh tidak tepat).

### Disadvantages
- **Latency lebih tinggi:** keputusan menunggu mediasi manusia; throughput eksekusi bisa berkurang.
- **Konsistensi bergantung disiplin manusia:** determinism bentuk output tetap, tetapi konsistensi antarkasus bergantung kepatuhan manusia pada prinsip keputusan.
- **Blast radius kegagalan manusia:** risiko kesalahan penilaian manusia dalam keputusan mengikat.

### Assessment
**Didokumentasikan** (benchmark). Sesuai DECISION_MODEL (Human Oversight) untuk kasus berisiko tinggi, tetapi sebagai **satu-satunya** mekanisme penuh (tanpa jalur otomatis) tidak didukung sebagai kebutuhan arsitektur oleh dokumen pada tahap ini; persis trade-off Blueprint (automated vs human-mediated).

---

## Alternative B — Automated Authorization (keputusan via aturan/otomasi deterministik)

### Advantages
- **Determinism & konsistensi tinggi:** aturan otomasi memproduksi keputusan konsisten (bentuk output deterministik — S-03 L101-106) dengan evidence-based rules.
- **Throughput tinggi:** tanpa mediasi manusia, keputusan dapat diproduksi cepat untuk alur yang aman & well-understood.
- **Audit terstruktur:** jejak aturan yang dievaluasi mudah diekstrak ke Audit Recorder.

### Disadvantages
- **Risiko tanpa oversight pada kasus berisiko tinggi:** otomasi penuh dapat memroduksi keputusan keliru jika aturan tidak menangkap konteks penting — berlawanan dengan "Convenience should never override safety" (DECISION_MODEL).
- **Accountability perlu dijaga eksplisit:** keputusan otomatis tetap harus dapat dijelaskan (explainability), bukan kotak hitam.
- **Bias aturan:** kualitas keputusan bergantung kualitas aturan; tanpa jalur escalation/oversight, keputusan berisiko tinggi berisiko.

### Assessment
**Didokumentasikan** (benchmark). Sesuai determinism & throughput, tetapi sebagai **mekanisme tunggal penuh tanpa jalur oversight** tidak didukung sebagai kebutuhan arsitektur untuk seluruh keputusan otorisasi — trade-off Human Oversight (DECISION_MODEL) tidak boleh diabaikan.

---

## Alternative C — Accountable Decision Framework (Hybrid: deterministic outcome shape, mekanisme terbuka antara automated & human-mediated, dibatasi prinsip keputusan)

### Advantages
- **Selaras dengan fakta determinism-open:** S-03 L109 tidak menentukan *bagaimana*,
 hanya bahwa *ada* keputusan → model **mendukung kedua mekanisme** (automated dan human-mediated) sebagai **bentuk valid** perhitungan, tanpa menetapkan satu mekanisme fisik.
- **Menghormati DECISION_MODEL:** menerapkan prinsip "Evidence Before Opinion · Trust Before Recommendation · Risk Before Execution · **Human Oversight** · **Maximum Explainability**" sebagai **batas/prinsip** model, bukan sebagai mekanisme.
- **Accountability & auditability terjamin:** apa pun mekanisme perhitungannya, keputusan **harus dapat dijelaskan & dilacak** (explainable + auditable) — sesuai DECISION_MODEL.
- **Bounded & separation of responsibility:** model tetap murni menghasilkan keputusan mengikat; tidak menyerobot execution/discovery/audit (S-03 L28/L209).
- **Implementation independence:** ADR menetapkan **batas arsitektural** (bentuk output deterministik, prinsip keputusan, accountability), bukan menetapkan mekanisme/kode — mendukung otomasi ataupun mediasi manusia sebagai penyedia perhitungan.

### Disadvantages
- **Tidak menunjuk satu mekanisme:** model memberi ruang (bukan menentukan) — arsitektural sadar bahwa mekanisme fisikal dipercaya ke lapisan implementasi/G-position, bukan ADR ini.
- **Perlu disiplin prinsip:** keefektifan bergantung kepatuhan pada prinsip keputusan (evidence/trust/risk/human oversight) — bukan kewajiban mekanis.

### Assessment
**Dipilih** (dipilih oleh Chief Architect sebagai keputusan proses). Paling **selaras dengan kumpulan dokumen**: (1) menghormati determinism-open S-03 yang sengaja membuka mekanisme; (2) menjamin accountability/auditability & separation of responsibility yang dimandatkan; (3) menerapkan DECISION_MODEL sebagai prinsip tanpa menciptakan mekanisme implementasi; (4) tetap **independent terhadap C-02/C-04** (tidak menuntut resolusi registry/idempotency). **Tidak menutup** evolusi mekanisme (tetap Future refinement).

---

# Decision

Chief Architect **telah memilih Alternative C** sebagai keputusan arsitektur ADR-001.

**Keputusan (exact wording):** Secara arsitektural, **Approval Coordinator menghasilkan keputusan Approval melalui sebuah Decision Framework yang akuntabel (Accountable Decision Framework)** — yaitu: keputusan Approval **selalu** (a) **mengikat** (binding), (b) **mendahului eksekusi** (gate, tidak boleh di-bypass), dan (c) **berbentuk deterministik** dalam salah satu state tetap (`Approved` / `Rejected` / `Expired` / `Cancelled` / `Superseded`), diproduksi oleh **mekanisme yang terbuka antara jalur otomasi (automated) dan mediasi manusia (human-mediated)**, dengan batas bahwa setiap keputusan **harus dapat dijelaskan (explainable) dan dapat diaudit (auditable)**, dan **tidak menyerobot tanggung jawab komponen lain** (bukan discovery/execution/audit).

Yang **bukan** bagian keputusan ini:
- **Bukan** menetapkan mekanisme implementasi perhitungan (bukan algoritma, bukan aturan spesifik, bukan tool, bukan "harus otomatis" atau "harus manusia").
- **Bukan** memutuskan Capability Resolution (C-02), Idempotency (C-04), Concurrency/Ordering (C-01), Failure Propagation (C-05), Deployment Topology (ADR-000), External Access (C-07), Verification Placement (C-08).
- **Bukan** bahasa pemrograman, teknologi, UI, transport, atau database.
- **Bukan** authority baru: ADR ini adalah **kanal pencatatan** di bawah Specification beku (R2-001 Audit 5; G1a/F1a).

Keputusan ini **tidak menciptakan keputusan baru**; ia meresmikan **sifat gerbang otorisasi** (deterministik dalam bentuk, akuntabel, terbuka mekanisme) yang sudah menjadi konteks tetap (S-03) sebagai keputusan arsitektur yang sah.

---

# Architectural Rationale

Keputusan ini terhubung ke Constitution, Governance, Approval Specification, Blueprint, dan ADR-000 sebagai berikut:

- **Constitution (Article VII determinism & bounded judgment):** bentuk output deterministik (state tetap) dan keputusan mengikat menghormati determinism mandat; pemisahan tanggung jawab menghormati aturan "bounded judgment" (Approval tidak menyerobot execution/discovery/audit). Constitution = puncak hirarki keputusan (DECISION_MODEL).
- **Governance (Runtime Governance, Long-Term):** Approval sebagai komponen dengan "one bounded responsibility"; keputusan tetap berlaku apa pun deployment topology (ADR-000) — model ini **tidak bertentangan dengan ADR-000** (topologi tak mengubah cara Approval menghasilkan keputusan). Governance: lower-never-contradict-higher (G4).
- **Approval Specification (S-03):** model **tidak mengubah Specification beku** (F3/F4): keputusan dicatat lewat ADR, bukan edit Spec; mekanisme tetap terbuka persis seperti L109. Semua dictum (gate, binding, states, no-bypass, defined failure) dihormati.
- **Blueprint (C-03):** menjawab trade-off resmi (automated vs human-mediated) sebagai **model terbuka-akuntabel**, bukan memilih satu ekstrem; konsisten dengan deskripsi C-03 "not prescribed".
- **ADR-000 (Deployment Topology):** ADR-001 **konsisten** dengan ADR-000 — satu kesatuan Runtime tidak mengubah sifat keputusan Approval; keputusan Approval tetap berlaku per-domain; tidak ada kontradiksi antar-ADR.
- **ADR Process (R2-001/R2-002/R2-003):** ADR-001 ditulis lewat lifecycle R2-001 (Candidate C-03 → ... → Accepted); C-03 **A-Certified atomik** (R2-002 L151); pemilihannya **keputusan proses** (R2-003), bukan kewajiban arsitektur.

**Mengapa ini terbaik:** Alternative C **paling selaras dengan determinism-open** (S-03 L109) — yang sengaja membuka mekanisme; Alternative A/B memaksa satu ekstrem yang tidak didukung sebagai kebutuhan arsitektur. Model terbuka-akuntabel **menjamin accountability & auditability** (yang dimandatkan), **menjaga separation of responsibility** (Approval = gate saja), **menerapkan DECISION_MODEL sebagai prinsip** tanpa menciptakan mekanisme, dan **tidak menutup** evolusi (otomasi atau mediasi manusia dapat diwujudkan di lapisan implementasi/G-position sebagai refinement). Ini sesuai hirarki keputusan (Constitution → Governance → Architecture → Operational Safety → Evidence → Trust → Risk → Efficiency → Convenience; DECISION_MODEL).

---

# Consequences

## Positive

- **Accountability terjamin:** setiap keputusan Approval dapat dijelaskan & dilacak (DECISION_MODEL "Maximum Explainability"; AUDIT traceability) apa pun mekanismenya.
- **Determinism bentuk output:** keputusan selalu dalam state tetap (Approved/Rejected/Expired/Cancelled/Superseded) — konsisten dengan Article VII & S-03.
- **Separation of responsibility terjaga:** Approval tetap murni otorisasi (gate), tidak menyerobot discovery/execution/audit (S-03 L28/L209).
- **Independence terhadap C-02/C-04:** model tidak menuntut resolusi registry/idempotency (R2-002 S-03; R1-003 Audit 2 no hidden dependency).
- **Implementation independence:** ADR memberi batas arsitektural, bukan mekanisme; eliminasi risiko "locking" sebuah teknologi.
- **Non-contradiction:** tidak ada perubahan Foundation/Specification/ADR-000; konsisten lintas layer.

## Negative

- **Tidak menunjuk mekanisme fisikal:** desain/perhitungan rill (aturan otomasi atau prosedur mediasi manusia) **diserahkan ke lapisan implementasi** (atau refinement berikutnya) — pemangku kepentingan yang mengharapkan "satu jawaban mekanis" tidak mendapatkannya di sini.
- **Keefektifan bergantung disiplin prinsip:** accountability & consistency bergantung kepatuhan pada prinsip keputusan (evidence/trust/risk/human oversight) — bukan dijamin mekanis.

## Accepted Trade-offs

- **Automated vs human-mediated:** dipilih **model terbuka-akuntabel** (keduanya valid) — bukan memilih satu ekstrem; trade-off Blueprint (auto simplicity vs human oversight) **diseimbangkan** lewat prinsip accountability & explainability, bukan dihindari.
- **Kesederhanaan penunjukan mekanisme** vs **keluwesan arsitektural**: dipilih yang menghormati determinism-open S-03 dan implementation independence; penunjukan mekanisme tunggal (A/B) ditolak karena **tidak didukung dokumen sebagai kebutuhan** (bukan karena teknologinya buruk).

---

# Impact Analysis

## Terhadap Approval Coordinator
- Memberi **model keputusan**: Approval Coordinator memproduksi keputusan Approval melalui Decision Framework yang akuntabel — deterministik dalam bentuk, terbuka mekanisme, explainable & auditable, tanpa menyerobot peran lain. Koordinator tetap "the singular gate of the chain" (R1-002 L106).

## Terhadap Execution Scheduler
- **Konteks authoring** untuk C-01 (ordering): scheduler menyusun operasi **yang telah "approved"** (bentuk tetap), tanpa perlu mengetahui mekanisme perhitungan spesifik (R1-003 L43: "no Spec/Blueprint requires the approval mechanism to be decided first"). Tidak ada perubahan pada scheduler.

## Terhadap Audit Recorder
- Keputusan Approval **harus dapat diaudit** (accountable) — model memastikan jejak keputusan dapat diekstrak/dilacak ke Audit (AUDIT_SPEC Traceability; GOVERNANCE "participate in auditing"). Tidak ada perubahan pada recorder.

## Terhadap Runtime
- Keputusan Approval berlaku **per bounded capability domain** yang sama (konsisten ADR-000 single cohesive unit); tidak ada dampak pada topologi. Model tidak mengubah struktur Runtime.

## Terhadap Future ADR
- **C-02 (Capability Resolution), C-04 (Idempotency)** — root tersisa: **tetap independen & A-Certified** (R2-002); ADR-001 **tidak mengubah validitasnya** (R2-003 Output 5 Neutrality).
- **C-01 (ordering)** — mendapat konteks (bentuk keputusan Approval) tetapi tidak kehilangan validitas (R1-003 order = strategy).
- **C-05 (failure propagation)** — failure Approval (defined failure, S-03 L146) menjadi konteks propagation, tanpa mengubah validitas C-05.
- **C-07/C-08** — menyusul lewat lifecycle R2-001 yang sama.

---

# Dependency Impact

- **Tidak memperkenalkan dependency baru** ke komponen/arsitektur (keputusan model, bukan menambah dependensi).
- **Tidak menghapus dependensi** atau mengubah interface (Approval tetap menghasilkan state; Registry + Contract tetap; G4 lower-never-contradict-higher).
- **C-03 independent** (R1-002 L41: Depends On = `-`; R2-002 A-Certified): tidak menuntut keputusan C-02/C-04 terlebih dahulu (konsisten catatan STOP ADR-001).
- **Tidak mengubah layering** (Mission → Constitution → Governance → Architecture → Specification → ADR → Implementation); ADR-001 berada di lapisan ADR, di bawah Specification beku.

---

# Risk Assessment

Menggunakan RISK_MODEL Project SAM (5 dimensi).

| Dimension | Assessment |
|---|---|
| Probability | **Low** — keputusan konsisten dengan fakta determinism-open (S-03) dan prinsip DECISION_MODEL; risiko kegagalan keputusan rendah; tidak mengubah spec/behaviour. |
| Impact | **Low** — tidak mengubah perilaku komponen; hanya menetapkan model keputusan (bentuk output + akuntabilitas + keterbukaan mekanisme); tidak ada kehilangan fungsi/data. |
| Recoverability | **Very High** — keputusan dapat ditinjau/diubah lewat Future ADR / ADR refinement; no irreversible change; mekanisme perhitungan tetap terbuka untuk disesuaikan. |
| Blast Radius | **Low** — mempengaruhi terutama konteks authoring ADR berikutnya (C-01/C-05) & batas akuntabilitas Approval; tidak menyebar ke seluruh platform melampaui keputusan ini. |
| Reversibility | **Very High** — keputusan reversible (model dapat dievaluasi ulang; mekanisme fisikal tidak dikunci oleh ADR ini). |

**Kategori risiko yang relevan:** Compatibility Risk (rendah — non-contradiction), Governance Risk (rendah — lower-never-contradict-higher), Configuration Risk (rendah — tidak mengunci mekanisme). **Tidak ada dimensi yang dinilai sangat tinggi/berisiko.** Keputusan **prefer reversible & limit blast radius** (RISK_MODEL principles).

---

# Trust Analysis

Menggunakan TRUST_MODEL Project SAM.

- **Evidence:** keputusan berdasar bukti dokumen (S-03 L109 determinism-open; Blueprint C-03 L156/L177 trade-off; DECISION_MODEL prinsip; GOVERNANCE bounded responsibility & valid-regardless-topology; R1-002/R1-003/R2-002/R2-003 cert & selection; ADR-000 consistency) — **Evidence Before Opinion** (DECISION_MODEL).
- **Trust basis (per TRUST_MODEL):** trust bersumber **dari Identity Layer** (MISSION/CONSTITUTION/GLOSSARY) dan dibangun melalui **evidence of governed compliance** — bukan assertion. Model keputusan ini **mematuhi** Constitution (Article VII determinism, bounded judgment) dan Specification, sehingga trust terpelihara; keputusan dapat diverifikasi dari dokumen (traceable & auditable).
- **Confidence:** **High** — konsisten lintas sumber independen (Specification, Blueprint, R-series, ADR-000, DECISION_MODEL); akuntabel & reproducible.
- **Unknowns:** bentuk **mekanisme fisikal** (aturan otomasi / prosedur mediasi manusia yang rill) — **dinyatakan terbuka** (diserahkan ke lapisan implementasi/refinement), bukan diasumsikan terpecahkan di sini.

---

# Implementation Notes

Hanya **batas implementasi** — bukan desain implementasi:
- Implementasi harus memproduksi keputusan Approval dengan **bentuk output deterministik** (salah satu dari `Approved`/`Rejected`/`Expired`/`Cancelled`/`Superseded`) **sebelum eksekusi**; tidak boleh ada bypass gate.
- Setiap keputusan **harus dapat dijelaskan (explainable) dan dapat diaudit (auditable)** — jejak keputusan harus dapat diekstrak ke Audit Recorder.
- Mekanisme perhitungan **bebas** (otomasi aturan / mediasi manusia / kombinasi) — implementasi **tidak boleh dikunci** oleh ADR ini, dan harus menghormati prinsip (evidence/trust/risk/human oversight).
- **Tidak disyaratkan** bahasa, teknologi, UI, transport, atau database.
- Implementasi **tidak boleh bertentangan** dengan baseline beku (B2/F1a) dan tidak mengurangi akuntabilitas Approval sebagai gate.
- Distribusi/perubahan mekanisme fisikal di masa depan = **refinement**, bukan perubahan ADR-001 tanpa lifecycle R2-001.

---

# Migration Strategy

- **Tidak ada migrasi arsitektur** karena ini ADR kedua dan **belum ada keputusan Approval yang diubah/dibatalkan** (ADR-001 menetapkan model, bukan menggantikan keputusan lama).
- Bila suatu saat model perlu diubah (mis. menunjuk mekanisme spesifik, atau menutup salah satu jalur): migrasi dilakukan **melalui ADR refinement / Future ADR** sesuai lifecycle R2-001, tanpa mengubah Foundation/Specification/ADR-000 — bukan perombakan langsung. Mekanisme perhitungan yang sudah dipakai dapat **tetap valid** selama belum dibatalkan ADR berikutnya (trust degrades & requires correction per TRUST_MODEL bila ada penyimpangan).

---

# Success Criteria

Bagaimana mengetahui keputusan ini berhasil:
1. Approval Coordinator dapat memproduksi keputusan Approval yang **mengikat, mendahului eksekusi, berbentuk deterministik** (state tetap) tanpa konflik dengan baseline & ADR-000.
2. Setiap keputusan **explainable & auditable** — jejak keputusan dapat dilacak ke Audit (AUDIT traceability).
3. **Separation of responsibility** terjaga: Approval murni otorisasi; tidak menyerobot discovery/execution/audit.
4. **C-02/C-04 tetap A-Certified & independen** (tidak kehilangan validitas karena ADR-001).
5. Tidak ada kebutuhan mengubah Foundation/Specification/ADR-000 untuk mewujudkan keputusan (**zero escalation**).
6. Implementasi dapat mewujudkan model tanpa menetapkan mekanisme tunggal yang bertentangan dengan prinsip keputusan.

---

# Future Reassessment

Situasi yang seharusnya memicu tinjauan/reassessment ADR-001:
- Munculnya kebutuhan untuk **menunjuk mekanisme perhitungan spesifik** (mis. aturan otomasi wajib, atau prosedur mediasi manusia wajib untuk kelas tertentu) yang tidak lagi memadai oleh model terbuka — pemicu refinement ADR untuk Approval.
- **Perubahan regulatory/compliance** yang menuntut bentuk keputusan atau akuntabilitas Approval berbeda.
- Umpan balik **implementasi/operasional** (RISK_MODEL: kegagalan/lingkungan berkembang) yang menunjukkan model akuntabilitas tidak lagi memadai (mis. keputusan tidak dapat dijelaskan).
- **Perubahan ADR-000** (mis. adopsi distribusi multi-runtime) yang mempengaruhi penempatan/mekanisme Approval — reassessment bila topologi berubah.
- Tidak ada teknologi tertentu yang direkomendasikan; reassessment digerakkan kebutuhan arsitektur, bukan preferensi.

---

# Related Documents

- MISSION, CONSTITUTION (Article VII determinism, bounded judgment)
- GOVERNANCE (Runtime Governance, Long-Term Governance)
- SPECIFICATION_FREEZE (F1a/F3/F4/F5)
- APPROVAL_SPECIFICATION (S-03; states; gate; boundaries)
- DECISION_MODEL, RISK_MODEL, TRUST_MODEL
- G0-001_Reference_Runtime_Blueprint (C-03)
- R1-001_Minimal_Reference_Runtime_Design, R1-002 (root/independence), R1-003 (order-neutral, equivalence)
- R2-001 (ADR Decision Process), R2-002 (Certification), R2-003 (Selection Record)
- ADR-000 (Deployment Topology)

---

# Validation

## Audit 1 — Problem Coverage
**LULUS.** ADR menjawab **satu** pertanyaan arsitektur (Approval Decision Model / mekanisme perhitungan keputusan Approval, C-03) secara tuntas di `# Problem Statement`, dengan boundary in/out eksplisit (`# Purpose`/`# Context`): tidak membahas C-02, C-04, C-01, C-05, topologi (ADR-000), C-07, C-08, algoritma implementasi, bahasa, teknologi, UI, transport, database. Setiap penyebutan istilah di-luar-scope hanya sebagai pernyataan batas, bukan pembahasan.

## Audit 2 — Alternative Coverage
**LULUS.** `# Alternatives Considered` mencakup **seluruh alternatif yang telah ditemukan** selama Discovery (A human-mediated; B automated; C accountable open framework) dari Blueprint C-03 L156 trade-off & R-series — **tidak menciptakan alternatif baru**. Tiap alternatif punya Advantages/Disadvantages/Assessment.

## Audit 3 — Foundation Compliance
**LULUS.** Semua decision driver ber-anchor dokumen (accountability S-03 L56/L201; determinism Article VII & S-03; bounded responsibility GOVERNANCE; separation of responsibility S-03 L28/L209; auditability AUDIT_SPEC; implementation independence S-03 L109/R1-001 L63). Tidak ada driver yang merupakan opini pribadi / preferensi teknologi. Konsisten dengan MISSION/CONSTITUTION/GOVERNANCE.

## Audit 4 — Specification Compliance
**LULUS.** Keputusan **tidak bertentangan** dengan Specification beku: determinism-open (S-03 L109) dihormati (mekanisme tetap terbuka), gate/binding/states/no-bypass/defined-failure dihormati; tidak ada perubahan Specification (F3/F4); non-contradiction.

## Audit 5 — ADR-000 Consistency
**LULUS.** ADR-001 **tidak bertentangan** dengan ADR-000 (Deployment Topology): model keputusan Approval berlaku apa pun topologi (GOVERNANCE "valid regardless of topology"); keputusan Approval per bounded capability domain yang sama; tidak ada kontradiksi antar-ADR.

## Audit 6 — Architectural Consistency
**LULUS.** Keputusan konsisten lintas layer (Mission → Constitution → Governance → Architecture → Specification → ADR → Implementation) dan tidak mengubah layering/Gov/Canonical Architecture. Selaras dengan G4 (lower-never-contradict-higher).

## Audit 7 — Implementation Independence
**LULUS.** ADR memberi **batas implementasi**, bukan desain: `# Implementation Notes` hanya batas (bentuk output deterministik, explainable/auditable, mekanisme bebas); tidak menetapkan mekanisme/teknologi; C-02/C-04 independent.

## Audit 8 — Final ADR Validation
**LULUS.** ADR lengkap menurut ADR_TEMPLATE (21 bagian), kelengkapan checklist, metadata terisi, risiko (RISK_MODEL) & trust (TRUST_MODEL) dinilai, trade-off jujur, non-contradiction, STOP tidak aktif. **Siap dipublikasikan** (Status: Accepted).

---

# STOP Condition

STOP apabila ditemukan salah satu kondisi berikut → jangan memaksakan ADR, jangan mengubah dokumen lain, jangan membuat proposal solusi; hanya lapor bukti.

| Trigger | Hadir? | Bukti |
|---|---|---|
| **Perlu mengubah Foundation** | **Tidak** | ADR tidak menyentuh MISSION/CONSTITUTION/GOVERNANCE; keputusan berada di lapisan ADR (R1-004). |
| **Perlu mengubah Specification** | **Tidak** | ADR mencatat keputusan tanpa mengubah 7 Specification (F3/F4; S-03 dihormati, bukan diedit). |
| **Perlu mengubah ADR-000** | **Tidak** | ADR-001 konsisten dengan ADR-000; tidak mengubah/menimpa keputusan deployment topology (Audit 5). |
| **Keputusan lebih dari satu keputusan** | **Tidak** | ADR-001 hanya Approval Decision Model (C-03), atomik per R2-002 L151 (1 mekanisme perhitungan keputusan); tidak mencakup C-02/C-04/C-01/C-05/C-07/C-08. |
| **Memerlukan penyelesaian C-02 atau C-04 terlebih dahulu** | **Tidak** | C-03 independent (R1-002 L41 Depends On = `-`; R2-002 A-Certified; R1-003 Audit 2 no hidden dependency; S-03 leaves open → decidable alone). |
| **Menciptakan authority baru** | **Tidak** | ADR = kanal pencatatan subordinat, bukan authority (R2-001 Audit 5; G1a/F1a). Tidak menambah authority/domain. |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP TIDAK AKTIF.** ADR-001 sah untuk dipublikasikan sebagai keputusan arsitektur (Accepted).

---

# Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-03 | Chief Architect | Accepted (draft → Accepted) — dibuka untuk review arsitektur. |

---

# Author Checklist

- [x] Problem clearly defined
- [x] Alternatives documented (A/B/C; seluruh alternatif yang ditemukan, tidak menciptakan baru)
- [x] Decision justified (Alternative C, keputusan proses)
- [x] Trade-offs documented
- [x] Risks evaluated (RISK_MODEL)
- [x] Trust assessment completed (TRUST_MODEL)
- [x] Related documents referenced
- [x] Terminology follows GLOSSARY.md
- [x] Consistent with CONSTITUTION.md

---

# Common Mistakes

Tidak dilanggar: tidak mendeskripsikan implementasi (mekanisme tetap terbuka), tidak mengomit alternatif (A/B/C dicatat), tidak mengabaikan trade-off, tidak merekam opini tanpa bukti (semua driver ber-anchor dokumen), tidak mencampur prosedur operasional dengan keputusan arsitektur, tidak membuat ADR untuk perubahan editorial sepele (keputusan arsitektur nyata), tidak menyerobot keputusan C-02/C-04.

---

# Completion Checklist

- [x] Metadata complete
- [x] Cross references validated
- [x] Review completed
- [x] Status updated (Accepted)
- [x] Ready for repository publication
