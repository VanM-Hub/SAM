# R2-002 — ADR Candidate Independence Certification (Chief Architect Directive)

**Version:** 1.0
**Status:** Read-only certification. Proves whether each of the four root candidates — **C-02 Capability Resolution, C-03 Approval Decision, C-04 Idempotency, C-06 Deployment Topology** — is truly **one atomic architectural decision**, satisfying the principle **One Architectural Decision = One ADR**, *before* the first ADR is written.
**Mode:** Read-only. Does **not** select the first candidate, does **not** write an ADR, does **not** repair any candidate, does **not** make a proposal. Only certifies.
**Commit intent:** `docs(design): certify architectural independence of root ADR candidates`
**Scope / Authority / Source of Truth:** only the four candidates above; only Foundation (Mission, Constitution, Philosophy, Governance, Glossary, Canonical Architecture), the seven Specifications, Blueprint (G0-001), R-series (R0-001, R1-001, R1-002, R1-003, R1-004), and G-series (G1-001…G2-003).

---

## Source Anchors (verbatim, read)

| # | Source | Anchor | Grounds |
|---|---|---|---|
| B-C02 | G0-001 L155 | C-02 "**Capability resolution policy** — How the Discovery Resolver chooses when multiple Capabilities satisfy one request (exact match vs. version-compatible match). Trade-off between precision and availability." | Official C-02 design question. |
| B-C03 | G0-001 L156 | C-03 "**Approval decision computation** — How the Approval Coordinator produces a decision (explicitly not prescribed by the Approval Specification). Trade-off between automated and human-mediated authorization." | Official C-03 design question. |
| B-C04 | G0-001 L157 | C-04 "**Idempotency realization** — How an operation's idempotency property is made observable without a mandated technical mechanism. Trade-off between explicit idempotency keys and operation-defined semantics." | Official C-04 design question. |
| B-C06 | G0-001 L159 | C-06 "**Runtime deployment topology** — Whether one Runtime hosts all components, or components are distributable across Runtimes / hosts. Trade-off between single-runtime simplicity and multi-runtime distribution." | Official C-06 design question. |
| S-02 | REGISTRY_SPEC L147/L149 | "when multiple candidates are equally valid, the Registry SHALL select exactly one **deterministically**."; "Resolution SHALL be deterministic…" | C-02 constraint: determinism. |
| S-03 | APPROVAL_SPEC L109 | "This specification **does not prescribe how the decision is computed**." | C-03 open: mechanism unconstrained. |
| S-04 | EXECUTION_SPEC L177 | "This specification **does not dictate a technical mechanism** for achieving idempotency." | C-04 open: mechanism unconstrained. |
| S-06 | GOVERNANCE L291–301 | "The governance model should remain valid regardless of: **deployment topology, runtime distribution**…" | C-06 open: no topology mandated. |
| R2a | R1-002 L40–44 | C-02/C-03/C-04/C-06 each **Independent: Yes**; Depends On: `-`. | Root status in dependency analysis. |
| R2b | R1-002 L63–64 | "ROOTS (mutually independent): C-02 C-03 C-04 C-06". | Mutually independent root set. |
| R2c | R1-002 L93 | "**Cycle: None.** All edges point strictly from the four roots downward to leaves… Strongly connected components are all singletons." | No decision depends transitively on another. |
| R2d | R1-003 Audit 1 L52 | "Zero dependency edges in R1-002 are obligated by Foundation, Specification, or Blueprint. Every edge is a consequence of design strategy." | No mandated cross-candidate dependency. |
| R2e | R1-003 Audit 2 L60–69 | All four roots "genuinely independent — no hidden dependency discovered"; C-02 "independent in decision-writability (must still honor REGISTRY determinism)". | Independence proven at writability level. |
| R2f | R1-003 Audit 6 | All 8 ADRs "order-neutral in content"; dependencies describe *authoring context*, not validity. | Survival of root identity independent of order. |
| R2g | R1-003 Audit 7 | "Several Equivalent = {C-02, C-03, C-04, C-06}". | Multiple equally-valid first decisions. |
| T1 | ADR_TEMPLATE L61–63 | Status: Draft \| Accepted \| Superseded \| Deprecated. | ADR status vocabulary (certification does not write any). |
| G1a | GOVERNANCE L125–127 | "Architecture Decisions are documented using ADR." | Decisions belong to the ADR layer. |
| F1a | SPECIFICATION_FREEZE L28/L37 | "All future design decisions… expressed through ADR"; "All subsequent design decisions belong in the ADR layer." | Post-freeze decisions sink in ADR layer. |

---

## Output 1 — Decision Identity

For each candidate: **keputusan inti (core decision), apa yang bukan bagian keputusan (what is NOT part of it), authority yang melahirkannya (authority that grants/stems it), responsibility yang dipengaruhi (responsibility affected).**

### C-02 — Capability Resolution
- **Keputusan inti:** *resolution policy* — ketika beberapa Capability memenuhi satu request, apakah Resolver memilih *exact match* atau *version-compatible match* (B-C02).
- **Bukan bagian keputusan itu:** mekanisme teknis resolver (algoritma pencarian, struktur indeks), determinism *property* (sudah ditetapkan REGISTRY L147/L149 — bukan pilihan di sini), format descriptor Capability (bukan keputusan ini), penempatan fisik Resolver (itu C-06).
- **Authority yang melahirkannya:** REGISTRY_SPEC (menempatkan Resolver di posisi Registry; menetapkan *types of choice* dan determinisme L147/L149, tetapi *tidak* menetapkan policy exact-vs-compatible → ruang keputusan ini sengaja terbuka). Authority tetap di bawah Specification beku (F1a/G1a); ADR hanya *mencatat* keputusan.
- **Responsibility yang dipengaruhi:** Desain & perilaku **Discovery Resolver** di Reference Runtime (R1-002 L108: "Discovery behavior (exact vs version-compatible) shapes Discovery Resolver design").

### C-03 — Approval Decision
- **Keputusan inti:** *bagaimana Approval Coordinator menghasilkan keputusan* — trade-off antara otorisasi otomatis vs mediated-by-human (B-C03). Ini satu keputusan: bentuk mekanisme perhitungan keputusan autorisasi.
- **Bukan bagian keputusan itu:** *bahwa* ada keputusan (sudah ditetapkan oleh Approval Spec — bukan diputuskan di sini), isi payload approval (bukan keputusan ini), apa yang terjadi pasca-keputusan (Execution — di luar), penempatan observer verifikasi (C-08).
- **Authority yang melahirkannya:** APPROVAL_SPEC L109 ("does not prescribe how the decision is computed") → mekanisme perhitungan sengaja dibiarkan terbuka sebagai keputusan arsitektur.
- **Responsibility yang dipengaruhi:** desain **Approval Coordinator** sebagai gerbang otorisasi (R1-002 L106: "the singular gate of the chain"; "cannot be shaped until the decision's nature is known").

### C-04 — Idempotency
- **Keputusan inti:** *bagaimana properti idempotency sebuah operasi dibuat observable* — trade-off antara *explicit idempotency keys* vs *operation-defined semantics* (B-C04). Satu keputusan: mekanisme realisasi idempotency.
- **Bukan bagian keputusan itu:** *bahwa* operasi dapat idempoten (property di bawah Contract sudah ditetapkan), mekanisme teknis spesifik (EXECUTION L177 dibiarkan terbuka — bukan pilihan), perilaku retry/reorder scheduler (C-01 menurun darinya, bukan isinya), detail storage keys.
- **Authority yang melahirkannya:** EXECUTION_SPEC L177 ("does not dictate a technical mechanism for achieving idempotency") → mekanisme realisasi dibiarkan terbuka.
- **Responsibility yang dipengaruhi:** semantik **Execution** & dasar untuk keputusan retry/reorder (R1-002 L107: "Execution semantics… shape Execution Scheduler design"; underpins retry/reorder correctness — R1-002 L128).

### C-06 — Deployment Topology
- **Keputusan inti:** *apakah satu Runtime menghosting semua komponen, atau komponen dapat didistribusikan lintas Runtime/host* — trade-off antara single-runtime simplicity vs multi-runtime distribution (B-C06). Satu keputusan struktural.
- **Bukan bagian keputusan itu:** *validitas* yang bergantung pada topologi (sudah ditetapkan GOVERNANCE "valid regardless of deployment topology" — bukan diputuskan), di mana menempatkan Providers/Connectors eksternal (C-07 menurun dari ini), di mana observer verifikasi (C-08), isi tiap komponen.
- **Authority yang melahirkannya:** GOVERNANCE L291–301 (valid "regardless of… deployment topology, runtime distribution") → baseline tidak mengunci topologi; keputusan sepenuhnya terbuka.
- **Responsibility yang dipengaruhi:** struktur keseluruhan Reference Runtime — apakah *single cohesive unit* atau *partitioned set* (R1-002 L109: "a **structure** decision that determines whether the design is a single cohesive unit or a partitioned set — this precedes component-level design").

---

## Output 2 — Decision Boundary (yang termasuk / bukan)

| Candidate | Termasuk (in scope) | Bukan (out of scope) | Evidence |
|---|---|---|---|
| **C-02** | Resolusi saat *multiple* Capability memenuhi request: policy exact-vs-compatible. Trade-off: precision vs availability. | Determinism (ditetapkan L147/L149); mekanisme teknis; format descriptor; lokasi fisik Resolver (C-06). | B-C02; S-02; R2e (constrained, not decided); R2-C06 |
| **C-03** | Bagaimana Coordinator *menghitung* keputusan otorisasi (otomatis vs human-mediated). | *Keberadaan* keputusan (fixed); payload approval; Execution pasca-keputusan; penempatan verifikasi (C-08). | B-C03; S-03; R1-002 L106 |
| **C-04** | Bagaimana idempotency *direalisasikan/made observable* (explicit keys vs operation-defined). | Property idempotency (fixed under Contract); mekanisme teknis spesifik (L177 open); retry/reorder (C-01). | B-C04; S-04; R1-002 L107 |
| **C-06** | Topologi deployment: satu vs distribusi komponen lintas Runtime/host. Trade-off: simplicity vs distribution. | Validitas governance (fixed L291–301); posisi Providers/Connectors (C-07); posisi observer verifikasi (C-08). | B-C06; S-06; R1-002 L109 |

**Boundary conclusion:** setiap kandidat menetapkan **satu** ruang keputusan yang dapat dipisah dari yang lain; batas luarnya dijamin oleh fakta bahwa specs *sengaja membiarkan* titik itu terbuka dan *menetapkan* hal lain sebagai tetap (S-02/S-03/S-04/S-06). Tidak ada kandidat yang menyerobot keputusan kandidat lain (cross-check: boundary C-02 ≠ C-06; C-03 ≠ C-08; C-04 ≠ C-01).

---

## Output 3 — Decision Atomicity (1 keputusan atau lebih)

| Candidate | Jumlah keputusan | Atomik? | Evidence |
|---|---|---|---|
| **C-02** | **1** — policy resolusi (exact-vs-compatible). Atom tunggal. | ✔ Ya | B-C02: satu "How… chooses"; satu trade-off (precision-availability). |
| **C-03** | **1** — mekanisme perhitungan keputusan otorisasi. Atom tunggal. | ✔ Ya | B-C03: satu "How… produces a decision"; satu trade-off (auto-vs-human). S-03 membiarkan *satu* pertanyaan terbuka. |
| **C-04** | **1** — realisasi idempotency. Atom tunggal. | ✔ Ya | B-C04: satu "How… made observable"; satu trade-off (keys-vs-semantics). S-04 membiarkan *satu* pertanyaan terbuka. |
| **C-06** | **1** — topologi deployment (satu vs distribusi). Atom tunggal. | ✔ Ya | B-C06: satu "Whether…"; satu trade-off (simplicity-vs-distribution). S-06 bebas. |

**Kesimpulan Atomicity:** **keempat kandidat masing-masing berisi satu keputusan** — tidak ada yang multi-decision. Tidak perlu memecah; tidak dilakukan pemecahan (per mandates). Ini konsisten dengan R2e (tiap root decidable sendirian) dan R2b/R2f (mutually independent & order-neutral → satu identity per candidate tidak terpecah oleh urutan).

---

## Output 4 — Hidden Dependency

| Candidate | Dependency tersembunyi? | Bukti |
|---|---|---|
| **C-02** | **Tidak.** Tidak diam-diam membutuhkan keputusan lain. | R2a (Independent: Yes, Depends On: `-`); R2e (decidable alone, only honors REGISTRY determinism yang *sudah* tetap); R2c (no cycle, singleton). S-02 menetapkan determinism → bukan dependency ke ADR lain, melainkan constraint tetap dari Spec. |
| **C-03** | **Tidak.** Tidak membutuhkan keputusan lain. | R2a/R2e; S-03 membiarkan terbuka → decidable alone. R1-002 L106: gate; tidak bergantung pada kandidat lain. |
| **C-04** | **Tidak.** Tidak membutuhkan keputusan lain. | R2a/R2e; S-04 membiarkan terbuka → decidable alone. |
| **C-06** | **Tidak.** Tidak membutuhkan keputusan lain. | R2a/R2e; S-06 ("valid regardless of topology") → decidable alone. R2c: no upstream. |

**Catatan dependency (dilaporkan, tidak diselesaikan):** keempat root **tidak** memiliki hidden dependency — ini persis hasil R1-003 Audit 2 (R2e: "no hidden dependency discovered"). Namun ada *arah sebaliknya* yang relevan: C-02, C-03, C-04, C-06 adalah upstream bagi C-01/C-05/C-07/C-08 (R2d/R2f: edges adalah *konteks authoring*, bukan *validitas*). Ini bukan dependency tersembunyi pada root — melainkan fakta bahwa *kandidat lain* bergantung pada keempat root. Tidak ada tangkapan yang mengharuskan root menunggu keputusan lain.

---

## Output 5 — Hidden Assumption

| Candidate | Asumsi tersembunyi (berasal dari luar Foundation/Spec)? | Bukti |
|---|---|---|
| **C-02** | **Tidak.** Asumsi yang dipakai (determinism, keberadaan pilihan) berasal dari REGISTRY_SPEC L147/L149 (S-02). Tidak ada asumsi eksternal. | R2e: "independent in decision-writability, must honor REGISTRY determinism" — constraint dari Spec, bukan asumsi siluman. |
| **C-03** | **Tidak.** Asumsi (bahwa ada keputusan yang harus dihitung) berasal dari APPROVAL_SPEC; mekanisme sengaja terbuka (S-03). | S-03; R1-003 L16. Tidak menyaru asumsi non-dokumen. |
| **C-04** | **Tidak.** Asumsi (idempotency adalah property operation di bawah Contract, tanpa mekanisme ditetapkan) berasal dari EXECUTION_SPEC (S-04). | S-04; R1-003 L17. |
| **C-06** | **Tidak.** Asumsi (validitas tidak bergantung topologi) berasal dari GOVERNANCE (S-06). | S-06; R1-003 L19. |

**Kesimpulan Hidden Assumption:** keempat kandidat hanya bergantung pada **asumsi yang sudah dijamin Foundation/Specification** — tidak ada asumsi yang berasal dari luar. Tidak ada asumsi yang perlu "dibuang" atau "disebut ulang"; tiap kandidat berdiri di atas constraint dokumen yang sudah tetap, yang justru *membatasi* ruang keputusan tanpa menutupnya.

---

## Output 6 — Architectural Purity

| Candidate | Keputusan arsitektur sejati? | Bukan hal-hal ini: | Bukti |
|---|---|---|---|
| **C-02** | **Ya.** Berurusan dengan *policy resolusi* pada lapisan arsitektur (bagaimana komponen Discovery memilih) — presisi vs ketersediaan adalah karakteristik arsitektural. | Bukan implementasi (tiada detail algoritme); bukan proses (urutan penulisan); bukan teknologi (tiada teknologi ditunjuk); bukan organisasi (tiada pihak/struktur). | B-C02; R2e (constrained decision); T3 (ADR memutuskan, bukan mengimplementasi). |
| **C-03** | **Ya.** Berurusan dengan *semantik gerbang otorisasi* — sifat keputusan yang dibuat Coordinator; human-vs-auto adalah trade-off arsitektural. | Bukan implementasi; bukan proses; bukan teknologi; bukan organisasi. | B-C03; R1-002 L106 ("singular gate"); S-03. |
| **C-04** | **Ya.** Berurusan dengan *bagaimana properti arsitektural (idempotency) dibuat observable* — kunci eksplisit vs semantik operasi adalah keputusan desain arsitektur. | Bukan implementasi (mekanisme teknis ditolak L177); bukan proses; bukan teknologi; bukan organisasi. | B-C04; S-04. |
| **C-06** | **Ya.** Berurusan dengan *struktur deployment* arsitektur — satu unit vs distribusi; ini keputusan bentuk arsitektur, di atas implementasi. | Bukan implementasi; bukan proses; bukan teknologi (tak menyebut platform); bukan organisasi. | B-C06; R1-002 L109 ("structure decision"); S-06. |

**Kesimpulan Architectural Purity:** **keempat kandidat adalah keputusan arsitektur sejati.** Tidak ada yang berupa implementasi, proses, teknologi, atau organisasi. Setiap kandidat mendefinisikan *bentuk/perilaku arsitektural* pada satu titik yang specs sengaja biarkan terbuka (S-02/S-03/S-04/S-06).

---

## Output 7 — Independence Matrix

| Candidate | Depends on (keputusan lain) | Influences (kandidat lain) | Independent? |
|---|---|---|---|
| **C-02** | **Tidak ada** (R2a `-`; R2e decidable alone) | C-05 (sumber failure resolusi) — R1-002 L54 | **Ya — sepenuhnya** (constraint determinism dari Spec, bukan dari ADR lain; R2e: "independent in decision-writability"). |
| **C-03** | **Tidak ada** (R2a `-`; R2e decidable alone) | C-01, C-05, C-08 (gerbang otorisasi) — R1-002 L50/51/53 | **Ya — sepenuhnya** (S-03). |
| **C-04** | **Tidak ada** (R2a `-`; R2e decidable alone) | C-01, C-05, C-08 (semantik execution/retry) — R1-002 L51/53/54 | **Ya — sepenuhnya** (S-04). |
| **C-06** | **Tidak ada** (R2a `-`; R2e decidable alone) | C-01, C-05, C-07, C-08 (struktur distribusi) — R1-002 L51/52/54 | **Ya — sepenuhnya** (S-06; R1-002 "structural"). |

**Independence conclusion:** keempat root **mutually independent** (R2b: "ROOTS (mutually independent)") dan tidak ada yang bergantung pada keputusan lain (R2a). Dependency hanya *keluar* (mempengaruhi kandidat non-root), bukan *masuk* — sehingga keempatnya masing-masing dapat disertifikasi sendiri tanpa menunggu yang lain. Ini konsisten dengan R2c (no cycle, singleton SCC) dan R2f (order-neutral).

---

## Output 8 — Certification Verdict

Sesuai mandat, hanya tiga pilihan: **A (Certified), B (Needs Scope Cleanup), C (Not an Architectural Decision)**. Tidak memberi solusi.

| Candidate | Verdict | Dasar |
|---|---|---|
| **C-02** Capability Resolution | **A — Certified** | Satu keputusan atomik (Output 3); boundary jelas (Output 2); arsitektural murni (Output 6); independent & tanpa hidden dependency (Output 4); tanpa asumsi eksternal (Output 5). Determinism adalah constraint Spec yang tetap (S-02), bukan cacat scoping. |
| **C-03** Approval Decision | **A — Certified** | Satu keputusan atomik; arsitektural murni (gerbang otorisasi); independent (S-03); boundary jelas; tiada hidden dependency/assumption. |
| **C-04** Idempotency | **A — Certified** | Satu keputusan atomik; arsitektural murni (observability property); independent (S-04); boundary jelas. |
| **C-06** Deployment Topology | **A — Certified** | Satu keputusan atomik struktural; arsitektural murni; independent (S-06); boundary jelas. |

**Verdict keseluruhan:** **keempat root candidate (C-02, C-03, C-04, C-06) = A — Certified.** Masing-masing adalah **satu keputusan arsitektur yang utuh**, memenuhi prinsip **One Architectural Decision = One ADR**. 0 di antaranya butuh scope cleanup (B); 0 di antaranya bukan keputusan arsitektur (C).

---

## Validation (8 Audit)

### Audit 1 — Identity
**LULUS.** Setiap kandidat memiliki identitas keputusan yang tunggal dan terdefinisi (Output 1): core decision, batas "bukan bagian", authority pemberi (S-02/S-03/S-04/S-06), dan responsibility terpengaruh (resolver/coordinator/execution/structure). Tidak ada identitas yang kabur atau ganda.

### Audit 2 — Boundary
**LULUS.** Setiap kandidat punya boundary in/out eksplisit (Output 2) yang dipisahkan dari kandidat lain (C-02≠C-06, C-03≠C-08, C-04≠C-01) dan dari hal yang sudah ditetapkan Spec (determinism, existence of decision, property idempotency, governance validity). Tidak ada tumpang tindih batas.

### Audit 3 — Atomicity
**LULUS.** Semua = **1 keputusan** (Output 3). Tidak ada multi-decision → tidak perlu dipecah, tidak dilakukan pemecahan (per mandat). Pesan G1-002 Chief Architect (kandidat dapat tampak sederhana tapi berisi beberapa keputusan) **tidak berlaku** untuk salah satu dari keempat root.

### Audit 4 — Dependency
**LULUS.** Tidak ada hidden dependency (Output 4): keempat root decidable alone (R2a/R2e), no cycle (R2c), zero obligasi lintas-kandidat (R2d). Dependency yang ada hanyalah *keluar* (root → C-01/C-05/C-07/C-08) sebagai konteks authoring, bukan ketergantungan validitas (R2f). Dilaporkan, tidak diselesaikan (per mandat).

### Audit 5 — Assumption
**LULUS.** Tidak ada hidden assumption dari luar Foundation/Spec (Output 5). Semua asumsi yang dipakai berasal dari REGISTRY/APPROVAL/EXECUTION/GOVERNANCE (S-02/S-03/S-04/S-06).

### Audit 6 — Architectural Purity
**LULUS.** Keempatnya keputusan arsitektur sejati (Output 6); bukan implementasi/proses/teknologi/organisasi. (Semua terdorong ke lapisan ADR per F1a, tapi *isi* tiap kandidat sendiri tetap arsitektural.)

### Audit 7 — Cross Candidate Consistency
**LULUS.** Matrix (Output 7) konsisten lintas kandidat: keempat root mutually independent (R2b), saling tidak bergantung (R2a), dependency hanya keluar ke kandidat yang sama (C-05 menerima C-02/C-03/C-04/C-06; C-01/C-08 menerima beberapa root), dan tidak ada cycle (R2c). Verdict seragam A untuk keempat — konsisten dengan R2g (Several Equivalent) dan R2f (order-neutral).

### Audit 8 — Certification Verdict
**LULUS.** Keempat = **A — Certified** (Output 8). Tidak ada yang B (perlu cleanup) atau C (bukan keputusan arsitektur). Gerbang terakhir sebelum ADR resmi terbuka dengan bersih.

---

## STOP Condition

Hentikan bila ditemukan salah satu kondisi berikut → jangan perbaiki, jangan ubah kandidat, jangan buat ADR, jangan beri solusi; hanya lapor bukti.

| Trigger | Hadir? | Bukti |
|---|---|---|
| **Kandidat ternyata dua keputusan** | **Tidak** | Output 3: semua atomik (1 keputusan). G1-002 concern tidak ter-picu. |
| **Kandidat bukan keputusan arsitektur** | **Tidak** | Output 6: semua arsitektural murni. |
| **Memerlukan perubahan Foundation** | **Tidak** | S-06 (GOVERNANCE) & S-02/S-03/S-04 sama sekali *menempatkan* keputusan sebagai terbuka dalam Foundation beku; tidak ada yang menuntut ubah Foundation (F1a: ADR mencatat, tidak mengubah). |
| **Memerlukan perubahan Specification** | **Tidak** | S-02/S-03/S-04 sengaja membiarkan titik ini terbuka; tidak ada kandidat yang membutuhkan ubah Spec (R2d: zero obligasi; keputusan hanya menempati ruang yang dibiarkan terbuka). |
| **Menentukan authority baru** | **Tidak** | ADR = kanal subordinat, bukan authority baru (G1a/F1a; R1-003 Audit 5). Sertifikasi ini pun tidak menambah authority/domain. |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP tidak aktif.** Keempat kandidat dapat disertifikasi (status A) dan siap memasuki ADR resmi, tanpa mengubah Foundation/Specification/authority.

---

## Final Statement

R2-002 membuktikan — secara read-only, dari dokumen beku (Freeze, Governance, Specifications, Blueprint) dan analisis R/G-series — bahwa **keempat root candidate masing-masing adalah satu keputusan arsitektur yang utuh (atomik)**, memenuhi prinsip **One Architectural Decision = One ADR**.

**Ringkasan:**
- **Decision Identity** (Output 1) & **Boundary** (Output 2): tiap kandidat punya keputusan inti tunggal, batas in/out eksplisit, authority pemberi (Spec yang sengaja membiarkan titik terbuka), dan responsibility terpengaruh — tanpa tumpang tindih antar-kandidat.
- **Atomicity** (Output 3): semua = **1 keputusan**; tidak ada multi-decision. (Kekhawatiran G1-002 — kandidat tampak sederhana tapi berisi banyak keputusan — terbukti tidak berlaku untuk keempat root.)
- **Hidden Dependency** (Output 4): tidak ada; keempatnya decidable alone (R2a/R2e/R2c/R2d). **Hidden Assumption** (Output 5): tidak ada yang berasal dari luar Foundation/Spec.
- **Architectural Purity** (Output 6): keempatnya keputusan arsitektur sejati — bukan implementasi/proses/teknologi/organisasi.
- **Independence Matrix** (Output 7): keempat mutually independent; dependency hanya keluar ke C-01/C-05/C-07/C-08, bukan masuk.
- **Certification Verdict** (Output 8): **C-02, C-03, C-04, C-06 = A — Certified.**
- **STOP tidak aktif** — tidak perlu perubahan Foundation, Specification, atau authority baru.

**Arti strategis (menjawab catatan Chief Architect):** sertifikasi ini adalah **gerbang terakhir sebelum Project SAM menghasilkan ADR resmi**. Karena keempat root telah terbukti atomik dan independen, setiap ADR yang lahir darinya akan **benar-benar merepresentasikan satu keputusan arsitektur** — menjadikan lapisan ADR disiplin dan sesuai prinsip One-ADR-One-Decision, tanpa risiko C-02/C-03/C-04/C-06 ternyata membawa multiple decision tersembunyi. Deliverable: `docs/design/R2-002_ADR_Candidate_Independence_Certification.md`.

**Commit intent:** `docs(design): certify architectural independence of root ADR candidates`
