# ADR-005 — Execution Ordering Model (C-01)

Version: 0.1.0

Status: Accepted

Decision Date: 2026-08-03

Author: Chief Architect (Project SAM Architecture Decision Making)

Reviewers: — (opened for architectural review)

Related ADRs: ADR-000 (Deployment Topology), ADR-001 (Approval Decision Model, C-03), ADR-002 (Capability Resolution Policy, C-02), ADR-003 (Idempotency Realization Model, C-04), ADR-004 (Failure Propagation Model, C-05)

Related Documents: SPECIFICATION_FREEZE, GOVERNANCE, SAM_ARCHITECTURE, G0-001_Reference_Runtime_Blueprint, R1-001_Minimal_Reference_Runtime_Design, R2-001_ADR_Decision_Process_Definition, CONTRACT_SPECIFICATION, EXECUTION_SPECIFICATION, APPROVAL_SPECIFICATION, AUDIT_SPECIFICATION

Related Modules: Execution Scheduler (primary — ordering domain), Approval Coordinator (ordering source), Audit Recorder (ordering termination — record), Contract (ordering constraint — immutability)

---

# Purpose

Mendefinisikan keputusan arsitektur Project SAM tentang **bagaimana urutan (ordering) operasi Runtime ditentukan secara arsitektural** — sehingga perilaku tetap deterministik, dapat diaudit, dan tidak melanggar Contract immutability maupun Approval ordering, **tanpa menambahkan mekanisme implementasi**.

ADR ini menjawab **satu** pertanyaan arsitektur (Execution Ordering Model / C-01) dan **tidak** membahas Capability Resolution (ADR-002), Approval mechanism (ADR-001), Idempotency (ADR-003), Failure Propagation (ADR-004), External Access (C-07), Verification Placement (C-08), atau mekanisme implementasi — semuanya di luar scope.

Ini adalah **keputusan arsitektur** (bukan analisis/audit/proposal) dan dijamin **tidak bertentangan dengan baseline beku** (SPECIFICATION_FREEZE, GOVERNANCE, Specification) dan **tidak bertentangan dengan ADR-000, ADR-001, ADR-002, ADR-003, ADR-004**.

---

# Context

## Mengapa Execution Ordering masih terbuka oleh Specification

- **G0-001 Blueprint C-01** (L154): "Concurrency & ordering model — **How the Execution Scheduler sequences concurrent approved operations without violating Contract immutability or Approval ordering** — Trade-off between strict ordering and operational throughput." Blueprint menyatakan C-01 sebagai kandidat arsitektural terbuka yang menyangkut **bagaimana Execution Scheduler mengurutkan** operasi yang telah disetujui.
- **R1-001 Audit 4 — Runtime Invariants** (L126-L142): invariants I1, I6, I8 menetapkan urutan lintas-komponen: **I1** — "Approval always precedes Execution"; **I6** — "Execution performs only after approval"; **I8** — "Approval completes at decision; Execution begins after Approval completes." Ini menetapkan temporal ordering **antar komponen** (Approval → Execution) tetapi **tidak** menetapkan ordering **di dalam Execution** ketika ada lebih dari satu operasi yang telah disetujui. R1-001 L142: invariants menjamin "(a) authorization ordering."
- **R1-001 Audit 3 — Component Interaction** (L104): "Interaction is a **linear causality along the chain**." Chain bersifat sekuensial dan unidireksional — ini adalah fakta arsitektural yang menetapkan **arah aliran**, tetapi tidak menetapkan bagaimana banyak operasi di-queue di dalam satu komponen.
- **R1-001 Audit 2 — Runtime Responsibility** (L69-L92): R5: Approval Coordinator "produce authorization decision before execution"; R6: Execution Scheduler "apply only approved operations (idempotent)." Execution menerima operasi dari Approval yang sudah selesai — ordering terjadi di dalam Execution atas operasi yang sudah disetujui.
- **ADR-001 L198** (Approval Decision Model): "Konteks authoring untuk C-01 (ordering): scheduler menyusun operasi **yang telah 'approved'** (bentuk tetap), tanpa perlu mengetahui mekanisme perhitungan spesifik." ADR-001 menegaskan C-01 bekerja pada operasi yang sudah di-approve.
- **ADR-003 L234** (Idempotency Realization Model): "C-01 (ordering): pengulangan operasi idempotent harus di-queue dengan semantik ordering yang konsisten." ADR-003 menyatakan bahwa C-01 harus mengakomodasi pengulangan idempotent dalam model ordering.
- **EXECUTION_SPEC L27:** "Execution defines the behavior of carrying out an already-approved operation. It does not determine whether the operation is permitted." Execution bekerja pada operasi yang sudah di-approve — ordering adalah perilaku Execution, bukan Approval.
- **APPROVAL_SPEC L56/L60:** "The purpose of Approval is to produce a binding authorization decision for an operation before that operation may be executed. Approval is the gate between intent and execution." Approval = gate, bukan sequencer — ia menghasilkan keputusan per-operasi, bukan urutan multi-operasi.

Karena itu **bagaimana ordering di dalam Execution ditentukan tidak pernah ditetapkan** oleh Foundation/Specification — ia adalah salah satu dari delapan Candidate ADR (C-01) yang sengaja dibuka oleh Blueprint, kini diresmikan.

## Posisi C-01 dalam Rantai Keputusan

- **C-01 mengonsumsi dari ADR-001 dan ADR-003:** operasi yang di-queue adalah operasi "yang telah approved" (ADR-001 L198); pengulangan idempotent mengikuti semantik ordering yang konsisten (ADR-003 L234).
- **C-01 tidak mempengaruhi ADR-002/ADR-004:** Capability Resolution (ADR-002) selesai sebelum Approval; Failure Propagation (ADR-004) mengikuti chain linear setelah Execution — ordering tidak mengubah arah propagasi.
- **C-01 = ordering di dalam Execution saja** — bukan ordering lintas komponen (sudah ditetapkan oleh I1/I6/I8), bukan ordering lintas Runtime, bukan ordering lintas domain.

## Status fase

Foundation **CLOSED** → Specification **FROZEN** → Architecture Discovery **CLOSED** → ADR Process **DEFINED** (R2-001) → Root ADR-000..004 **ACCEPTED** → **ADR-005: In Progress**.

---

# Problem Statement

**Pertanyaan arsitektur yang harus dijawab:** Bagaimana Runtime menentukan urutan konseptual operasi di dalam Execution Scheduler sehingga perilaku tetap deterministik, dapat diaudit, dan tidak melanggar Contract immutability maupun Approval ordering?

Trade-off (dari G0-001 Blueprint C-01) adalah antara **strict ordering** (deterministik, tertelusur, throughput terbatas) dan **operational throughput** (lebih banyak operasi paralel, potensi non-deterministik). Masalah ini **objektif** dan dibatasi pada **ordering konseptual**; ia bukan masalah mekanisme (scheduler/thread/queue/locking), bukan masalah concurrency runtime, bukan masalah optimasi performa.

---

# Decision Drivers

Driver berikut **diekstrak dari Foundation/Specification/Blueprint** — hanya yang didukung dokumen:

| Driver | Dukungan dokumen |
|---|---|
| **Determinism** | REGISTRY_SPEC L147/L149: resolusi "SHALL be deterministic." GOVERNANCE Long-Term Governance: governance valid regardless of topology. Urutan operasi harus deterministik — input approval yang sama menghasilkan urutan eksekusi yang sama. |
| **Traceability** | AUDIT_SPEC L124-L133: "Every Audit Record SHALL be traceable back to its originating objects." Urutan operasi harus tertelusur — Audit Record harus dapat merekonstruksi urutan eksekusi. |
| **Auditability** | AUDIT_SPEC L66/L72/L86: "Audit records, in a conceptual form, the operational events that have occurred, so that they can be followed back to their origin." GOVERNANCE: "participate in auditing." Urutan yang telah ditentukan harus dapat diaudit — tidak boleh ambigu. |
| **Bounded responsibility** | GOVERNANCE Runtime Governance: "own one bounded responsibility"; R1-001 L75: tiap responsibility punya satu owner. Ordering adalah tanggung jawab Execution Scheduler (R6); Approval tidak menentukan urutan (gate, bukan sequencer); Contract tidak menentukan urutan (defines structure only, I7). |
| **Runtime integrity** | R1-001 L118: "No additional interaction is invented." R1-001 L142: invariants menjamin "authorization ordering." Ordering tidak menciptakan interaction/jalur baru — ia adalah properti internal Execution Scheduler. |
| **Predictability** | SAM_ARCHITECTURE Approved Execution Flow: linear dan sekuensial. GOVERNANCE: "governance should remain valid regardless of deployment topology." Urutan harus dapat diprediksi dari kondisi awal — bukan hasil proses stokastik/internal yang tidak transparan. |
| **Separation of responsibility** | I1/I6/I8: Approval → Execution terpisah; Approval = gate, Execution = execute; GOVERNANCE "own one bounded responsibility." Ordering tidak menyerobot tanggung jawab Approval (gate) atau Audit (record). |
| **Survivability** | GOVERNANCE Long-Term Governance: valid "regardless of deployment topology, runtime distribution." Ordering model harus bertahan terhadap perubahan deployment/distribusi tanpa mengubah keputusan dasar. |
| **Implementation independence** | R1-001 L63: batas Runtime "imposes no topology." ADR tidak boleh menuntut mekanisme implementasi. |

Catatan: driver yang **tidak** didukung dokumen (mis. "ordering harus dioptimasi untuk throughput", "ordering harus support paralelisme", "ordering harus berbasis timestamp") **tidak** dipakai sebagai justifikasi.

---

# Alternatives Considered

Alternatif berikut adalah **seluruh alternatif yang dapat didukung oleh dokumen sumber** — dievaluasi terhadap bukti aktual (bukan diciptakan).

## Alternative A — Strict Linear Ordering (urutan berdasarkan kedatangan Approval)

Deskripsi: Operasi di dalam Execution Scheduler dieksekusi dalam **urutan ketat sesuai urutan Approval** — yaitu urutan kedatangan operasi dari Approval Coordinator (Approval-arrival order). Operasi pertama yang selesai di-approve adalah operasi pertama yang dieksekusi. Setiap operasi dieksekusi sampai selesai sebelum operasi berikutnya dimulai.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| I1 (R1-001 L132) | "Approval always precedes Execution — Execution begins after Approval completes." | **SUPPORTS A.** Temporal sequence Approval adalah prekondisi Execution; urutan Approval secara alami menjadi urutan Execution. |
| I6 (R1-001 L136) | "Execution performs only after approval — Execution does not determine whether the operation is permitted." | **SUPPORTS A.** Execution memproses apa yang sudah di-approve; ordering adalah properti internal Execution atas operasi yang sudah ada, bukan properti Approval. |
| I8 (R1-001 L138) | "Approval completes at decision; Execution begins after Approval completes." | **SUPPORTS A.** Satu operasi = satu siklus Approval→Execution; operasi berikutnya menunggu Approval baru. |
| R1-001 L104 | "Interaction is a linear causality along the chain." | **SUPPORTS A.** Linear causality — aliran tunggal, sekuensial. |
| SAM_ARCHITECTURE Approved Execution Flow | `Mission → Governance check → Approval → Execution → Verification → Audit` — linear, satu arah. | **SUPPORTS A.** Flow linier tanpa percabangan — ordering mengikuti aliran alami. |
| R1-001 L142 | Invariants guarantee "(a) authorization ordering." | **SUPPORTS A.** Authorization ordering adalah jaminan yang sudah ada; Strict Linear mewujudkan jaminan ini. |
| APPROVAL_SPEC L60 | "Approval is the gate between intent and execution." | **SUPPORTS A.** Gate = satu pintu — operasi masuk satu per satu, urutan kedatangan di gate menentukan urutan di execution. |
| ADR-001 L198 | "Scheduler menyusun operasi yang telah approved." | **SUPPORTS A.** Scheduler menyusun (bukan memilih ulang) — urutan sudah diberikan oleh Approval. |
| ADR-003 L234 | "Pengulangan operasi idempotent harus di-queue dengan semantik ordering yang konsisten." | **SUPPORTS A.** Queue adalah struktur FIFO — konsisten dengan Approval-arrival order. |
| G0-001 C-01 L154 | "without violating Contract immutability or Approval ordering" | **SUPPORTS A.** Strict Linear inherently respects Approval ordering; Contract immutability tidak terganggu karena Contract tidak berubah di antara operasi. |

### Advantages
- **Determinism maksimal:** urutan Approval adalah urutan Execution — tidak ada kemungkinan urutan berbeda dari input yang sama.
- **Traceability sempurna:** urutan Execution adalah salinan eksak urutan Approval — traceability mundur (dari Audit kembali ke Approval) bersifat linear dan langsung.
- **Bounded responsibility:** murni milik Execution Scheduler — tidak menyerobot Approval (yang hanya gate) atau Contract (yang hanya struktur).
- **Separation of responsibility:** Approval memutuskan, Execution mengeksekusi dalam urutan yang sama — tidak ada overlap wewenang.
- **Runtime integrity:** tidak menciptakan interaksi/jalur baru — memanfaatkan chain linear yang sudah ada.
- **Predictability:** urutan dapat diprediksi dari urutan Approval — tidak ada faktor internal yang mengubah urutan.
- **Implementation independence:** prinsip ordering, bukan mekanisme — implementasi bebas menggunakan struktur data apapun untuk mempertahankan urutan.
- **Architectural survivability:** model valid regardless of deployment topology.

### Disadvantages
- **Throughput terbatas** secara konseptual — model tidak mengakomodasi eksekusi paralel di tingkat arsitektur. Namun operational throughput adalah **mekanisme implementasi** yang berada di luar scope ADR arsitektural; optimasi throughput dapat diwujudkan di lapisan implementasi sepanjang jaminan deterministik dipertahankan.

### Assessment
**Dipilih** (dipilih oleh Chief Architect sebagai keputusan proses). Paling **selaras dengan kumpulan dokumen**: Strict Linear Ordering mewujudkan invariants I1/I6/I8, memanfaatkan linear causality chain (R1-001 L104), menghormati Approval sebagai gate (APPROVAL_SPEC L60), dan memberikan determinisme-predictability-traceability maksimal. **Tidak menciptakan mekanisme, scheduler, atau authority baru.** Satu-satunya trade-off (throughput) adalah implikasi implementasi, bukan arsitektural.

---

## Alternative B — Dependency-driven Ordering (urutan berdasarkan dependensi antar operasi)

Deskripsi: Urutan operasi ditentukan oleh dependensi antar operasi — operasi pada Contract yang sama diurutkan secara ketat, sedangkan operasi pada Contract berbeda dapat independen.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| G0-001 C-01 L154 | "without violating Contract immutability" — Contract immutability adalah constraint. | **WEAK SUPPORT.** Contract immutability adalah properti Contract, bukan dependency antar operasi. Operasi pada Contract yang immutable tidak menciptakan dependensi — Contract tidak berubah. |
| I7 (R1-001 L137) | "Contract defines structure only — does not define who runs it, who approves it, who discovers it, or who executes it." | **CONTRADICTS B.** Contract tidak mendefinisikan ordering, execution, atau hubungan antar operasi. |
| CONTRACT_SPEC | Contract mendefinisikan struktur dan aturan kompatibilitas — bukan hubungan dependensi antar operasi. | **NO EVIDENCE.** Contract tidak menyediakan mekanisme dependensi. |
| ADR-003 | Idempotency dideklarasikan oleh Contract — properti per-operasi, bukan hubungan antar operasi. | **NO EVIDENCE.** Idempotency = properti pengulangan operasi yang sama, bukan dependensi antar operasi berbeda. |

### Assessment
**TIDAK dipilih.** Tidak ada bukti di dokumen Federation yang mendefinisikan "dependensi antar operasi." Contract mendefinisikan struktur (I7) — bukan hubungan dependensi. Contract immutability justru menghilangkan potensi dependensi (Contract tidak berubah, sehingga operasi pada Contract yang sama tidak saling mempengaruhi). Alternative B menciptakan konsep "dependensi" yang tidak ada di dokumen sumber.

---

## Alternative C — Scheduler-defined Ordering (Scheduler sendiri yang menentukan urutan)

Deskripsi: Execution Scheduler diberikan otoritas untuk menentukan urutan eksekusi sendiri — ordering adalah kebijakan internal Scheduler.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| G0-001 C-01 L154 | "How the Execution Scheduler sequences..." — ini adalah pertanyaan, bukan jawaban. | **NO EVIDENCE.** Blueprint membuka pertanyaan — tidak memberikan otoritas kepada Scheduler untuk menentukan sendiri. |
| R1-001 L104 | "Linear causality along the chain." | **CONTRADICTS C.** Linear causality mengimplikasikan urutan deterministik; Scheduler-defined membuka kemungkinan non-deterministik. |
| GOVERNANCE Runtime Governance | "own one bounded responsibility." Responsibility = ordering, tapi ordering policy harus didasarkan dokumen, bukan kebijakan internal tanpa anchor. | **WEAK SUPPORT.** Memberi Scheduler otoritas tanpa anchor dokumen = authority baru. |

### Assessment
**TIDAK dipilih.** Tidak ada bukti yang memberikan Scheduler otoritas untuk menentukan urutan secara internal. Blueprint C-01 adalah pertanyaan yang harus dijawab oleh ADR, bukan delegasi ke Scheduler. Scheduler-defined ordering bertentangan dengan determinism (REGISTRY_SPEC L147/L149) dan predictability (SAM_ARCHITECTURE linear flow).

---

## Alternative D — Contract-defined Ordering (Contract mendefinisikan urutan)

Deskripsi: Urutan operasi ditentukan oleh Contract — Contract menyediakan aturan urutan bagi operasi yang mereferensikannya.

### Evidence Evaluation

| Evidence | What it says | Verdict |
|---|---|---|
| I7 (R1-001 L137) | "Contract defines structure only — does not define who runs it, who approves it, who discovers it, or who executes it." | **CONTRADICTS D.** Contract secara eksplisit tidak mendefinisikan execution. |
| CONTRACT_SPEC | Contract mendefinisikan struktur, aturan kompatibilitas, dan deklarasi idempotency (via ADR-003) — bukan urutan eksekusi. | **NO EVIDENCE.** Contract tidak memiliki konsep urutan. |
| ADR-001 L198 | Scheduler menyusun operasi yang telah approved — bukan operasi yang diurutkan oleh Contract. | **NO EVIDENCE.** |

### Assessment
**TIDAK dipilih.** Contract mendefinisikan struktur (I7), bukan urutan. Tidak ada bukti di dokumen Federation yang memberikan Contract otoritas atau mekanisme untuk mendefinisikan urutan operasi.

---

# Decision

Chief Architect **telah memilih Alternative A** sebagai keputusan arsitektur ADR-005.

**Keputusan (exact wording):** Secara arsitektural, **urutan eksekusi operasi di dalam Execution Scheduler mengikuti Strict Linear Ordering berdasarkan urutan Approval (Approval-arrival order)** — yaitu: operasi dieksekusi dalam urutan ketat sesuai urutan ia selesai di-approve oleh Approval Coordinator. Setiap operasi dieksekusi sampai mencapai state terminal (Completed / Failed / Cancelled — sebagaimana didefinisikan EXECUTION_SPEC lifecycle) sebelum operasi berikutnya dimulai. Urutan ini bersifat deterministik (satu Approval sequence = satu Execution sequence), tertelusur (dapat direkonstruksi mundur dari Audit), dan **tidak melanggar Contract immutability** (Contract tidak berubah antar operasi) maupun **Approval ordering** (urutan Approval adalah urutan Execution).

Yang **bukan** bagian keputusan ini:
- **Bukan** mendefinisikan mekanisme implementasi: bukan scheduler, bukan thread, bukan async, bukan queue, bukan locking, bukan event bus, bukan workflow engine, bukan aktor, bukan transport, bukan RPC.
- **Bukan** mendefinisikan concurrency model, synchronization model, atau retry model — semuanya di luar scope arsitektural.
- **Bukan** mendefinisikan bagaimana Approval mengurutkan operasi — Approval adalah gate per-operasi (APPROVAL_SPEC L60), urutan di Approval adalah fakta temporal (operasi mana yang sampai lebih dulu), bukan kebijakan arsitektural.
- **Bukan** mendefinisikan topologi, deployment, scaling, atau optimasi throughput.
- **Bukan** mendefinisikan timeout, circuit breaker, atau operational resilience.
- **Bukan** authority baru: ADR ini adalah **kanal pencatatan** di bawah Specification beku (R2-001 Audit 5; G1a/F1a).
- **Bukan** lifecycle baru — ordering menggunakan lifecycle state EXECUTION_SPEC yang sudah ada (Completed, Failed, Cancelled).

Keputusan ini **tidak menciptakan satu pun komponen, authority, scheduler, atau interaksi baru.** Ia hanya menetapkan **prinsip ordering** di dalam Execution Scheduler, mengikuti urutan yang sudah diberikan oleh chain linear.

---

# Architectural Rationale

Keputusan ini terhubung ke Constitutional/Governance/Specification/Blueprint sebagai berikut:

- **Constitution (determinism & bounded responsibility):** Strict Linear Ordering mewujudkan determinism (REGISTRY_SPEC L147/L149) — urutan deterministik dari input yang deterministik. Tidak menciptakan authority baru — ordering tetap berada di dalam Execution Scheduler (R6).
- **Governance (lower never contradict higher):** Ordering model tidak mengubah GOVERNANCE Runtime Governance — setiap komponen tetap "own one bounded responsibility." GOVERNANCE Long-Term Governance menyatakan governance valid "regardless of deployment topology" — model linear valid regardless of topology.
- **Invariants (I1/I6/I8):** Strict Linear Ordering **mewujudkan** invariants yang sudah ada — I1 (Approval→Execution sequential), I6 (Execution performs only after approval), I8 (Approval completes → Execution begins). Ordering adalah **konsekuensi arsitektural** dari invariants ini — bukan keputusan independen.
- **APPROVAL_SPEC (gate, not sequencer):** Approval adalah gate per-operasi (L56/L60). Strict Linear mengambil urutan temporal Approval apa adanya — tidak menuntut Approval menjadi sequencer, tidak menambah tanggung jawab Approval.
- **EXECUTION_SPEC (lifecycle):** Operasi dieksekusi sampai state terminal (Completed/Failed/Cancelled) sebelum operasi berikutnya — konsisten dengan EXECUTION_SPEC lifecycle states. Completion boundary didefinisikan oleh spec, bukan oleh ADR.
- **Blueprint (C-01):** Konsisten dengan C-01 *"How the Execution Scheduler sequences concurrent approved operations without violating Contract immutability or Approval ordering"* — Strict Linear menjawab "how" (Approval-arrival order), memenuhi "Approval ordering" (urutan Approval = urutan Execution), dan "Contract immutability" terjaga (Contract tidak berubah).
- **ADR-001 (Approval Decision Model):** "Scheduler menyusun operasi yang telah approved" (L198) — Strict Linear adalah "menyusun" dalam arti mempertahankan urutan yang sudah diberikan Approval. Tidak perlu mengetahui mekanisme perhitungan Approval.
- **ADR-003 (Idempotency Realization):** "Pengulangan operasi idempotent harus di-queue dengan semantik ordering yang konsisten" (L234) — Strict Linear memenuhi ini: pengulangan di-queue pada posisi Approval-nya, deterministik dan tertelusur.
- **ADR-004 (Failure Propagation):** Strict Linear tidak mengubah model propagasi — failure tetap mengikuti chain linear ke Audit Recorder (termination). Urutan operasi tidak menciptakan jalur propagasi baru.

**Mengapa ini terbaik:** Alternative A **paling selaras dengan kumpulan dokumen** — Strict Linear Ordering adalah perpanjangan alami dari invariants I1/I6/I8 dan linear causality chain (R1-001 L104). Ia tidak menuntut konsep baru (dependensi, otoritas Scheduler, atau Contract ordering). Ia memberikan determinisme-predictability-traceability maksimal dengan trade-off minimal (throughput — yang merupakan domain implementasi, bukan arsitektur). Alternative B/C/D tidak didukung evidence atau bertentangan dengan invariants.

---

# Consequences

## Positive

- **Determinism:** urutan Approval = urutan Execution — reproducible, predictable, verifiable.
- **Traceability:** urutan Execution identik dengan urutan Approval — mundur dari Audit ke Approval bersifat linear dan langsung.
- **Auditability:** urutan yang ketat dan linear memungkinkan Audit merekonstruksi urutan operasi tanpa ambiguitas.
- **Bounded & separation of responsibility:** ordering milik Execution Scheduler — tidak menyerobot Approval (gate), Contract (struktur), atau Audit (record).
- **Runtime integrity:** tidak menciptakan interaction/jalur baru — memanfaatkan chain yang sudah ada.
- **Implementation independence:** prinsip ordering, bukan mekanisme — implementasi bebas memilih struktur data internal.
- **Architectural survivability:** valid regardless of deployment topology.

## Negative

- **Throughput terbatas secara konseptual:** model tidak menyediakan ordering non-linear atau paralel di tingkat arsitektur. Namun throughput adalah domain implementasi — bukan tanggung jawab keputusan arsitektural.
- **Tidak mengakomodasi prioritas operasi:** semua operasi diperlakukan setara dalam urutan kedatangan. Namun prioritas adalah mekanisme implementasi yang dapat ditambahkan di lapisan bawah tanpa mengubah prinsip arsitektural.

## Accepted Trade-offs

- **Strict ordering** vs **operational throughput:** dipilih strict ordering pada tingkat arsitektural. Throughput dibuka sebagai domain implementasi.
- **Simplicity** vs **flexibility:** dipilih simplicity (satu aturan universal). Flexibility (dependency-driven, prioritas) diserahkan ke implementasi sepanjang determinisme terjaga.

---

# Impact Analysis

## Terhadap Runtime
- Menetapkan prinsip ordering di dalam Execution Scheduler: Approval-arrival order, satu operasi selesai sebelum berikutnya dimulai.
- Tidak menambah komponen Runtime atau mengubah tanggung jawab komponen eksisting.

## Terhadap Komponen Spesifik

| Komponen | Dampak |
|---|---|
| Execution Scheduler | **Primary:** mengadopsi Strict Linear Ordering — operasi dieksekusi dalam urutan Approval-arrival, satu per satu sampai state terminal. |
| Approval Coordinator | **Tidak berubah:** tetap gate per-operasi — tidak menjadi sequencer. Urutan temporal Approval adalah konsekuensi alami, bukan kebijakan baru. |
| Audit Recorder | **Tidak berubah:** tetap mencatat — urutan Execution yang linear memudahkan traceability mundur ke Approval. |
| Contract | **Tidak berubah:** Contract immutability terjaga — Contract tidak berubah antar operasi. |

## Terhadap Future ADR
- **C-07 (External Access Boundaries):** ordering tidak mempengaruhi placement Provider/Connector — ordering adalah internal Execution.
- **C-08 (Verification Point Placement):** ordering internal Execution tidak mempengaruhi penempatan Verification — Verification terjadi setelah Execution (SAM_ARCHITECTURE flow).
- **C-06 (Deployment Topology):** ordering model valid regardless of topology.
- **Tidak mengubah validitas ADR-000..004** (non-contradiction).

## Terhadap Implementation
- Implementasi harus mempertahankan urutan Approval-arrival di dalam Execution Scheduler.
- Implementasi harus menyelesaikan satu operasi (mencapai state terminal) sebelum memulai operasi berikutnya.
- Implementasi harus memastikan traceability urutan ke Audit Recorder.
- Mekanisme implementasi (queue, FIFO buffer, event loop, thread) **tidak diatur** oleh ADR ini.

---

# Dependency Impact

- **Tidak memperkenalkan dependency baru** — ordering adalah properti internal Execution Scheduler, menggunakan chain yang sudah ada.
- **Tidak menghapus dependensi** atau mengubah interface.
- **Tidak mengubah layering** (Mission → Constitution → Governance → Architecture → Specification → ADR → Implementation; R1-004).
- **Konsisten** dengan aturan dependensi: ordering adalah keputusan internal Scheduler yang tidak mempengaruhi komponen hulu (Approval/Registry/Contract) atau hilir (Audit).

---

# Risk Assessment

Menggunakan RISK_MODEL Project SAM (5 dimensi).

| Dimension | Assessment |
|---|---|
| Probability | **Very Low** — keputusan prinsip sederhana (urutan Approval = urutan Execution); risiko kegagalan keputusan sangat rendah; tidak mengubah spec/behaviour komponen. |
| Impact | **Very Low** — tidak mengubah perilaku komponen; hanya menetapkan prinsip ordering; tidak ada kehilangan fungsi/data. |
| Recoverability | **Very High** — keputusan dapat ditinjau/diubah lewat Future ADR atau ADR Superseded; no irreversible change. |
| Blast Radius | **Low** — mempengaruhi terutama internal Execution Scheduler & konteks authoring ADR berikutnya; tidak menyebar ke seluruh platform. |
| Reversibility | **Very High** — keputusan reversible (prinsip ordering dapat dievaluasi ulang sebagai Future ADR tanpa mengubah Foundation). |

**Kategori risiko yang relevan:** Architectural Risk (Very Low). **Tidak ada dimensi yang dinilai tinggi/berisiko.**

---

# Trust Assessment

- **Evidence:** keputusan berdasar bukti dokumen (I1/I6/I8 dari R1-001 L126-L142; R1-001 L104 linear causality; APPROVAL_SPEC L56/L60 gate; ADR-001 L198 approved operations; ADR-003 L234 ordering semantik; SAM_ARCHITECTURE Approved Execution Flow; Blueprint C-01 L154) — **Evidence Before Opinion** (DECISION_MODEL).
- **Confidence:** **High** — keputusan adalah konsekuensi alami dari invariants yang sudah ada (I1/I6/I8); konsisten lintas sumber independen; tidak memerlukan konsep baru.
- **Unknowns:** mekanisme implementasi (queue, prioritas, throughput) — **dinyatakan out of scope**, bukan diasumsikan terpecahkan.

---

# Implementation Notes

Hanya **batas implementasi** — bukan desain implementasi:
- Implementasi harus mempertahankan urutan operasi sesuai urutan Approval (Approval-arrival order).
- Implementasi harus menyelesaikan satu operasi (mencapai state terminal: Completed / Failed / Cancelled) sebelum memulai operasi berikutnya.
- Implementasi harus memastikan urutan Execution tercatat di Audit Recorder untuk traceability.
- Implementasi harus **tidak bertentangan** dengan baseline beku (B2/F1a).
- Mekanisme (FIFO queue, event loop, data structure) **tidak diatur** — bebas implementasi.

---

# Migration Strategy

- **Tidak ada migrasi arsitektur** — Reference Runtime belum memiliki ordering yang ditetapkan; ADR-005 mendefinisikan ordering untuk pertama kali.
- Bila suatu saat model berubah (mis. adopsi dependency-driven ordering di tingkat arsitektural): migrasi dilakukan melalui ADR Superseded / Future ADR sesuai lifecycle R2-001, tanpa mengubah Foundation/Specification.

---

# Success Criteria

Bagaimana mengetahui keputusan ini berhasil:
1. Reference Runtime mengimplementasikan urutan Approval-arrival di dalam Execution Scheduler — tanpa menciptakan mekanisme ordering baru yang melanggar invariants.
2. Urutan Execution identik dengan urutan Approval — dapat diverifikasi oleh Audit Recorder.
3. Traceability mundur (Audit → Execution → Approval) bersifat linear — setiap operasi di Audit dapat dilacak ke posisinya di Approval.
4. **Bounded responsibility:** ordering adalah milik Execution Scheduler — tidak menyerobot Approval atau Contract.
5. Tidak ada kebutuhan mengubah Foundation/Specification untuk mewujudkan ordering (**zero escalation**).
6. Dokumentasi keputusan terbaca jelas oleh implementer & reviewer.

---

# Future Reassessment

Situasi yang seharusnya memicu tinjauan/reassessment ADR-005:
- Kebutuhan **operational throughput di tingkat arsitektural** (bukan hanya mekanisme implementasi) — mis. model distribusi yang menuntut ordering non-linear atau paralel.
- Kebutuhan **prioritas operasi di tingkat arsitektural** (bukan hanya di lapisan implementasi).
- Model pengulangan idempotent (ADR-003) yang berevolusi dan menuntut semantik ordering berbeda.
- Umpan balik implementasi/operasional yang menunjukkan Strict Linear Ordering tidak lagi memadai.

---

# Related Documents

- GOVERNANCE (Runtime Governance, Long-Term Governance)
- SPECIFICATION_FREEZE (F1a/F3/F4/F5)
- SAM_ARCHITECTURE (Approved Execution Flow, Responsibility Matrix)
- G0-001_Reference_Runtime_Blueprint (C-01, L154)
- R1-001_Minimal_Reference_Runtime_Design (Audit 3 Component Interaction L98-L118; Audit 4 Invariants I1-I9 L126-L142)
- R2-001_ADR_Decision_Process_Definition
- EXECUTION_SPECIFICATION (L27, lifecycle states)
- APPROVAL_SPECIFICATION (L56, L60)
- CONTRACT_SPECIFICATION (structure, immutability)
- AUDIT_SPECIFICATION (Traceability Rules)
- ADR-001 (Approval Decision Model — L198 konteks C-01)
- ADR-003 (Idempotency Realization Model — L234 konteks C-01)
- ADR-004 (Failure Propagation Model)

---

# Validation

## Audit 1 — Problem Coverage
**LULUS.** ADR menjawab **satu** pertanyaan arsitektur (Execution Ordering Model / C-01) secara tuntas di `# Problem Statement`, dengan boundary in/out eksplisit (`# Purpose`/`# Context`: tidak membahas mekanisme concurrency, scheduler, thread, queue, retry, timeout). Setiap penyebutan istilah di-luar-scope hanya sebagai pernyataan batas.

## Audit 2 — Alternative Coverage
**LULUS.** `# Alternatives Considered` mencakup **seluruh alternatif yang dapat didukung oleh evidence** (A: Strict Linear, B: Dependency-driven, C: Scheduler-defined, D: Contract-defined) — **tidak menciptakan alternatif tanpa evidence**. Tiap alternatif dievaluasi terhadap evidence aktual (Evidence Evaluation table).

## Audit 3 — Foundation Compliance
**LULUS.** Semua decision driver ber-anchor dokumen (I1/I6/I8, R1-001 L104, APPROVAL_SPEC L56/L60, SAM_ARCHITECTURE Approved Execution Flow, GOVERNANCE). Tidak ada driver yang merupakan opini pribadi / preferensi teknologi.

## Audit 4 — Specification Compliance
**LULUS.** Keputusan **tidak bertentangan** dengan Specification beku: tidak mengubah EXECUTION/APPROVAL/CONTRACT/AUDIT Specification. Ordering adalah properti internal Execution Scheduler yang tidak mengubah spec behavior. B2 non-contradiction terhadap baseline beku.

## Audit 5 — Root ADR Consistency
**LULUS.** Keputusan **tidak bertentangan** dengan ADR-000..004:
- **ADR-000 (Deployment Topology):** ordering adalah internal Scheduler — tidak bergantung pada topology.
- **ADR-001 (Approval Decision):** tidak mengubah Approval mekanisme — ordering hanya mengonsumsi urutan temporal Approval.
- **ADR-002 (Capability Resolution):** ordering terjadi setelah resolusi dan approval — tidak mempengaruhi resolusi.
- **ADR-003 (Idempotency):** pengulangan idempotent di-queue dalam urutan Approval — konsisten dengan L234.
- **ADR-004 (Failure Propagation):** ordering tidak mengubah arah propagasi — failure tetap ke depan sepanjang chain.

## Audit 6 — Runtime Consistency
**LULUS.** Keputusan **tidak bertentangan** dengan invariants R1-001 (I1-I9). Strict Linear Ordering **mewujudkan** I1/I6/I8, bukan melanggarnya. Tidak menciptakan jalur interaksi baru (R1-001 L118). Bounded responsibility terjaga (R1-001 Audit 2).

## Audit 7 — Implementation Independence
**LULUS.** ADR memberi **batas implementasi**, bukan desain: `# Implementation Notes` hanya batas (Approval-arrival order, satu operasi selesai sebelum berikutnya, traceability). Tidak menetapkan mekanisme queue/scheduler/thread/locking.

## Audit 8 — Final ADR Validation
**LULUS.** ADR lengkap menurut ADR_TEMPLATE, metadata terisi, risiko (RISK_MODEL) & trust (TRUST_MODEL) dinilai, trade-off jujur, non-contradiction, STOP tidak aktif. **Siap dipublikasikan** (Status: Accepted).

---

# STOP Condition

STOP apabila ditemukan salah satu kondisi berikut → jangan memaksakan ADR, jangan mengubah dokumen lain; hanya lapor.

| Trigger | Hadir? | Bukti |
|---|---|---|
| **Perlu mengubah Foundation** | **Tidak** | ADR tidak menyentuh MISSION/CONSTITUTION; keputusan berada di lapisan ADR (R1-004). |
| **Perlu mengubah Specification** | **Tidak** | ADR mencatat keputusan tanpa mengubah 7 Specification. EXECUTION_SPEC lifecycle states digunakan sebagaimana adanya. |
| **Perlu mengubah ADR sebelumnya** | **Tidak** | ADR-000..004 tidak berubah — C-01 mengonsumsi dari ADR-001/ADR-003, tidak mengubahnya. |
| **Perlu concurrency model** | **Tidak** | Ordering adalah prinsip arsitektural — bukan model concurrency. Tidak ada thread, lock, async, atau synchronization yang ditetapkan. |
| **Perlu scheduler model** | **Tidak** | Ordering adalah bagaimana Scheduler mengurutkan — bukan menciptakan Scheduler (sudah ada sebagai komponen Runtime). |
| **Perlu topology baru** | **Tidak** | Ordering internal Scheduler — valid regardless of topology (ADR-000). |
| **Perlu authority baru** | **Tidak** | ADR = kanal pencatatan subordinat, bukan authority (R2-001 Audit 5). Tidak menambah komponen/domain. |
| **Kontradiksi struktural** | **Tidak** | Semua audit lulus — tidak ada kontradiksi dengan Foundation/Specification/ADR lain. |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP TIDAK AKTIF.** ADR-005 sah untuk dipublikasikan sebagai keputusan arsitektur (Accepted).

---

# Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-03 | Chief Architect | Accepted (draft → Accepted) — dibuka untuk review arsitektur. |

---

# Author Checklist

- [x] Problem clearly defined
- [x] Alternatives documented (A/B/C/D; tidak menciptakan tanpa evidence)
- [x] Decision justified (Alternative A, keputusan proses)
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
