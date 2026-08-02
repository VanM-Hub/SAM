# ADR-006 — External Access Boundaries

Version: 0.1.0

Status: Accepted

Decision Date: 2026-08-03

Author: Chief Architect (Project SAM Architecture Decision Making)

Related ADRs: ADR-000, ADR-001, ADR-002, ADR-003, ADR-004, ADR-005

Related Documents: CONSTITUTION, GOVERNANCE, SAM_ARCHITECTURE, SPECIFICATION_FREEZE, CITIZEN_SPECIFICATION, CONTRACT_SPECIFICATION, REGISTRY_SPECIFICATION, G0-001_Reference_Runtime_Blueprint

Lifecycle: R2-001 — Architecture decision process

---

# Purpose

Menjawab C-07 dari Blueprint G0-001 — mendefinisikan batas akses antara Reference Runtime dan entitas di luar Runtime secara arsitektural.

Satu keputusan arsitektur: **Bagaimana seluruh akses dari dan menuju Runtime dibatasi sehingga seluruh Citizen tetap berinteraksi melalui mekanisme arsitektural yang sama.**

---

# Context

C-07 dari G0-001 Blueprint (L160): "Where the Runtime positions Providers / Connectors (external access) relative to the chain — Trade-off between isolation and integration ease."

Framework mendefinisikan tiga kategori Citizen yang relevan:

- **Runtime** (CITIZEN_SPEC L55): "Every Runtime is a Citizen" — govern satu bounded capability domain (SAM_ARCHITECTURE)
- **Provider** (CITIZEN_SPEC L145): constitutional Citizen — implement external access
- **Connector** (CITIZEN_SPEC L149): constitutional Citizen — implement external access/communication

Ketiganya adalah Citizens setara. CITIZEN_SPEC L859: "No Citizen possesses constitutional privilege." CITIZEN_SPEC L863: "Runtime is not superior to Provider." CITIZEN_SPEC L875: "All Citizens obey identical constitutional rules."

Minimal Reference Runtime (R1-001) menetapkan:

- Runtime = realisasi tujuh konsep Specification Layer untuk satu bounded capability domain (R1-001 L24)
- External access berada di LUAR Runtime (R1-001 L51, L65, L196)
- Permukaan Runtime = Contracts + Registry (R1-001 L58, L65)
- Hanya dua mekanisme cross-boundary: Contracts dan Registry-based Capability discovery (R1-001 L58)
- Interaksi linear sepanjang chain: Citizen → Capability → Registry → Contract → Approval → Execution → Audit (R1-001 L104)

CITIZEN_SPECIFICATION (L639/L643/L647): "Citizens SHALL NOT discover each other directly" / "SHALL publish themselves to Registry" / "Discovery SHALL occur through Registry."

CONTRACT_SPEC (L55): "A Contract makes the boundary between Citizens explicit."

Keputusan ini diperlukan sekarang karena: (a) Runtime boundary sudah didefinisikan oleh R1-001, (b) posisi Provider/Connector relatif terhadap chain adalah satu keputusan arsitektur yang dapat diputuskan tanpa dependensi pada ADR lain (R2-002/R2-003: konteks authoring, bukan validitas), (c) seluruh root ADR (ADR-000/001/002) sudah Accepted — konteks authoring cukup.

---

# Problem Statement

Bagaimana seluruh akses dari dan menuju Runtime dibatasi sehingga seluruh Citizen tetap berinteraksi melalui mekanisme arsitektural yang sama?

Pertanyaan ini muncul dari tiga fakta arsitektural yang harus dikoordinasikan:

1. **Runtime adalah Citizen, bukan seluruh sistem.** R1-001 menetapkan Runtime = realization of Specification Layer untuk SATU bounded capability domain. Runtime bukan satu-satunya Citizen — Provider dan Connector adalah Citizens terpisah (CITIZEN_SPEC Citizen Hierarchy).

2. **External access harus ada.** Provider dan Connector adalah constitutional Citizens yang TUGAS-NYA adalah external access (SAM_ARCHITECTURE L103). Runtime TIDAK mengimplementasikan external access (R1-001 L51). External access adalah fakta arsitektural yang harus ditempatkan.

3. **Semua Citizen harus tetap setara.** CITIZEN_SPEC L859/L863/L875 menetapkan kesetaraan konstitusional — tidak ada Citizen yang punya privilege, Runtime tidak superior terhadap Provider.

Tantangan arsitekturnya: bagaimana menempatkan external access (Provider/Connector) relatif terhadap chain Runtime tanpa melanggar kesetaraan Citizen, tanpa menciptakan mekanisme akses baru, dan tanpa mengubah boundary Runtime yang sudah didefinisikan.

---

# Decision Drivers

| # | Driver | Definisi | Anchor |
|---|---|---|---|
| D-1 | **Citizen Universality** | Seluruh entitas arsitektural — Runtime, Provider, Connector — adalah Citizen. Tidak ada entitas di luar model Citizen. | CITIZEN_SPEC L145, L149, L55: "Every Runtime is a Citizen"; L859: "No Citizen possesses constitutional privilege"; L875: "All Citizens obey identical constitutional rules." |
| D-2 | **Separation of Responsibility** | Runtime meng-govern bounded capability domain. Provider/Connector mengimplementasikan external access. Tanggung jawab tidak bercampur. | SAM_ARCHITECTURE L103: Provider/Connector "Implement external access / communication; Exercise governance" (MUST NOT); R1-001 L51: "Runtime does not implement external access." |
| D-3 | **Bounded Runtime** | Runtime adalah realisasi Specification Layer untuk satu domain. External access, strategic decision, presentation, governance/authority creation berada di luar. | R1-001 L65: "inside = 7 Specification-realizing containers; outside = strategic decision, external access, presentation, governance/authority creation." |
| D-4 | **Contract Integrity** | Contract = boundary antar Citizens. Setiap interaksi antar Citizens harus melalui Contract — bukan akses langsung. | CONTRACT_SPEC L55: "A Contract makes the boundary between Citizens explicit." |
| D-5 | **Registry Universality** | Registry = satu-satunya mekanisme discovery. Citizens tidak discover langsung. Registry berlaku universal — untuk semua Citizens, bukan hanya Runtime. | CITIZEN_SPEC L639: "SHALL NOT discover each other directly"; L643: "SHALL publish themselves to Registry"; L647: "Discovery SHALL occur through Registry." |
| D-6 | **Determinism** | Boundary harus deterministik — posisi external access tidak boleh bergantung pada kondisi runtime, konfigurasi, atau implementasi spesifik. | ADR-005 (Approval-arrival ordering deterministik); R1-001 L65: boundary struktural, bukan kondisional. |
| D-7 | **Interoperability** | Boundary harus memungkinkan interoperasi antar Citizen — Runtime dapat berinteraksi dengan Provider/Connector, dan sebaliknya, melalui mekanisme yang universal. | GOVERNANCE L283: "Does it maintain provider independence?"; CITIZEN_SPEC: "Citizens communicate through Capabilities" (L79). |
| D-8 | **Runtime Independence** | Keputusan boundary tidak boleh membuat Provider/Connector bergantung pada implementasi atau internal Runtime. | SAM_ARCHITECTURE L127: "Providers are replaceable implementations"; GOVERNANCE: "valid regardless of deployment topology." |
| D-9 | **Survivability** | Boundary harus bertahan terhadap perubahan eksternal. Provider diganti, Connector diperbarui — boundary tetap berlaku tanpa perubahan ADR. | CITIZEN_SPEC L83: "Citizens never depend on implementation"; SAM_ARCHITECTURE evolution model. |
| D-10 | **Implementation Independence** | ADR tidak menetapkan mekanisme teknis — protokol, transport, API, SDK, authentication. Boundary adalah konsep arsitektural, bukan implementasi. | SPECIFICATION_FREEZE L28: "Evolution through ADR" — ADR adalah decision sink, bukan implementation spec. |

---

# Alternatives Considered

## Alternative A — Runtime Boundary via Registry + Contract (Universal Citizen Boundary)

**Deskripsi:** Seluruh akses dari dan menuju Runtime melalui Contracts + Registry — dua mekanisme cross-boundary yang sudah ditetapkan oleh baseline beku. Runtime tidak menambahkan mekanisme akses baru. Provider/Connector adalah Citizens di luar chain Runtime yang berinteraksi dengan Runtime melalui mekanisme universal yang sama dengan seluruh interaksi antar-Citizen: Contract + Registry-based discovery.

### Advantages

- Menghormati kesetaraan Citizen (CITIZEN_SPEC L859/L863/L875) — tidak ada Citizen yang menjadi "gerbang" bagi Citizen lain
- Konsisten dengan R1-001 L58/L65: "the two and only two mechanisms"
- Konsisten dengan CONTRACT_SPEC L55: "Contract makes the boundary between Citizens explicit"
- Konsisten dengan CITIZEN_SPEC L639/L643/L647: discovery universal melalui Registry
- Tidak menciptakan mekanisme akses baru (R1-001 L118: "No additional interaction is invented")
- Semua akses melalui chain yang sama yang mencakup Approval (GOVERNANCE L198: "Execution affecting the external world should require governance approval")
- Provider independence (SAM_ARCHITECTURE L127: "replaceable implementations") — Provider mengganti tanpa mempengaruhi boundary

### Disadvantages

- Tidak ada mekanisme "privilej" bagi akses yang sangat frequent — semua melalui Contract + Registry yang sama
- Potensi overhead konseptual: setiap interaksi (bahkan internal-to-internal Citizen) melalui Contract + Registry
- Tidak menyediakan posisi khusus untuk high-throughput access patterns (tapi ini di luar scope C-07)

### Evidence

| Evidence | What It Says | Assessment |
|---|---|---|
| R1-001 L58 | "The boundary between the Runtime and everything else is the two and only two mechanisms: Contracts and Registry-based Capability discovery." | **DEFINES** the boundary mechanism |
| R1-001 L65 | "Outer surface is Contracts + Registry; everything else (strategic decision, external access, presentation, governance/authority creation) is outside." | **POSITIONS** external access outside with Contracts+Registry as surface |
| R1-001 L116 | "(All components) → Registry on every external interaction — the only permitted discovery mechanism." | **REQUIRES** Registry for all external interaction |
| R1-001 L118 | "No additional interaction is invented." | **PROHIBITS** creating additional access mechanisms |
| CITIZEN_SPEC L639 | "Citizens SHALL NOT discover each other directly." | **REQUIRES** Registry as universal discovery |
| CITIZEN_SPEC L643 | "Citizens SHALL publish themselves to Registry." | **REQUIRES** all Citizens to use Registry |
| CITIZEN_SPEC L647 | "Discovery SHALL occur through Registry." | **REQUIRES** Registry as the sole discovery path |
| CITIZEN_SPEC L79 | "Citizens communicate through Capabilities." | **REQUIRES** Capability-based communication |
| CITIZEN_SPEC L859 | "No Citizen possesses constitutional privilege." | **PROHIBITS** creating privilege for any Citizen type |
| CITIZEN_SPEC L863 | "Runtime is not superior to Provider." | **PROHIBITS** Runtime as "gateway" over Provider |
| CITIZEN_SPEC L875 | "All Citizens obey identical constitutional rules." | **REQUIRES** uniform boundary rules for all Citizens |
| CONTRACT_SPEC L55 | "A Contract makes the boundary between Citizens explicit." | **DEFINES** Contract as the citizen-to-citizen boundary |
| SAM_ARCHITECTURE L103 | "Provider / Connector — Implement external access / communication — Exercise governance" (MUST NOT) | **SEPARATES** responsibility: Provider implements access, does not govern |
| SAM_ARCHITECTURE L127 | "Providers (including AI providers) are replaceable implementations." | **REQUIRES** provider independence |
| R1-001 L51 | "External access — Providers/Connectors implement external access; Runtime does not." | **CONFIRMS** external access responsibility |
| R1-001 L196 | "External-access / communication failures → Provider/Connector layer (outside Runtime)." | **POSITIONS** failure boundary at Provider/Connector |
| GOVERNANCE L198 | "Execution affecting the external world should require governance approval." | **REQUIRES** Approval gate for external-world execution |

---

## Alternative B — Komponen Runtime Berkomunikasi Langsung dengan Entitas Eksternal

**Deskripsi:** Komponen individual dalam Runtime (Execution Scheduler, Approval Coordinator, dsb.) diizinkan mengakses Provider/Connector secara langsung tanpa melalui chain Runtime. Komponen yang membutuhkan akses eksternal membuat koneksi langsung.

### Advantages

- Potensi throughput lebih tinggi — tidak melalui chain penuh untuk akses sederhana
- Komponen spesifik bisa punya integrasi langsung dengan Provider yang relevan

### Disadvantages

- Melanggar "no additional interaction" (R1-001 L118)
- Melanggar "the two and only two mechanisms" (R1-001 L58)
- Melanggar "Citizens SHALL NOT discover each other directly" (CITIZEN_SPEC L639)
- Menciptakan boundary yang tidak seragam — beberapa akses melalui chain, beberapa lewat langsung
- External access bisa melewati Approval (bertentangan dengan GOVERNANCE L198)
- Melanggar linear causality sepanjang chain (R1-001 L104)
- Internal Runtime menjadi tergantung pada Provider spesifik

### Evidence

| Evidence | What It Says | Assessment |
|---|---|---|
| R1-001 L58 | "The two and only two mechanisms." | **CONTRADICTS.** Direct = third mechanism. |
| R1-001 L65 | "Outer surface is Contracts + Registry." | **CONTRADICTS.** Direct = no outer surface. |
| R1-001 L104 | "Interaction is a linear causality along the chain." | **CONTRADICTS.** Direct = non-linear, outside chain. |
| R1-001 L118 | "No additional interaction is invented." | **CONTRADICTS.** Direct = additional interaction. |
| CITIZEN_SPEC L639 | "Citizens SHALL NOT discover each other directly." | **CONTRADICTS.** Direct = discovery without Registry. |
| GOVERNANCE L198 | "Execution affecting the external world should require governance approval." | **CONTRADICTS.** Direct could bypass Approval gate. |
| R1-001 I5 | "Discovery only through Registry." | **CONTRADICTS.** Direct violates invariant. |

### Assessment

**TIDAK DIDUKUNG — DITOLAK.** Tidak ada satupun evidence dari 11 dokumen otorisasi yang mendukung Alternative B. Seluruh boundary documents secara konsisten menetapkan Contracts + Registry sebagai satu-satunya mekanisme cross-boundary. Alternative B melanggar minimal lima invariant/requirement arsitektural.

---

## Alternative C — Provider/Connector Menjadi Bagian Internal Runtime

**Deskripsi:** Provider dan Connector menjadi komponen internal Runtime — ditempatkan di dalam chain Runtime sebagai komponen tambahan. Runtime diperluas untuk mencakup external access sebagai internal capability.

### Advantages

- Satu model internal yang terintegrasi — tidak ada "outside" untuk di-manage
- Semua akses melalui chain internal Runtime

### Disadvantages

- Runtime yang tadinya 7 komponen (1:1 ke Specification Layer) menjadi lebih dari 7 — melanggar R1-001 L24
- Runtime kini mengimplementasikan external access — bertentangan dengan R1-001 L51: "Runtime does not implement external access"
- Provider/Connector kehilangan identitas sebagai Citizen terpisah — bertentangan dengan CITIZEN_SPEC Citizen Hierarchy (Runtime, Provider, Connector adalah branch terpisah)
- Melanggar separation of responsibility (SAM_ARCHITECTURE L103: Provider tidak meng-exercise governance)
- Runtime menjadi "superior" — memiliki Provider di dalamnya — bertentangan dengan CITIZEN_SPEC L863
- Provider/Connector sekarang terikat ke siklus hidup Runtime — bertentangan dengan "replaceable implementations" (SAM_ARCHITECTURE L127)
- External access failures kini menjadi Runtime failure — memperluas failure responsibility Runtime (R1-001 L196)

### Evidence

| Evidence | What It Says | Assessment |
|---|---|---|
| R1-001 L24 | "7 komponen memetakan 1:1 ke 7 konsep Specification Layer." | **CONTRADICTS.** Menambah Provider/Connector = lebih dari 7 komponen. |
| R1-001 L51 | "External access — Providers/Connectors implement external access; Runtime does not." | **CONTRADICTS.** Jika Provider di dalam Runtime, Runtime implement external access. |
| R1-001 L65 | "External access is outside." | **CONTRADICTS.** External access tidak bisa sekaligus "di luar" dan "di dalam." |
| R1-001 L196 | "External-access failures → Provider/Connector layer (OUTSIDE Runtime)." | **CONTRADICTS.** Failure boundary tidak bisa di luar Runtime jika Provider di dalam Runtime. |
| SAM_ARCHITECTURE L103 | "Provider/Connector — Implement external access; Exercise governance" (MUST NOT). | **CONTRADICTS.** Jika di dalam Runtime, Provider dikenai governance Runtime. |
| CITIZEN_SPEC L863 | "Runtime is not superior to Provider." | **CONTRADICTS.** Provider inside Runtime = Runtime superior. |
| CITIZEN_SPEC L947-L957 | Citizen Hierarchy: Runtime, Agent, Provider, Connector sebagai branch TERPISAH. | **CONTRADICTS.** Provider tidak bisa menjadi sub-branch Runtime. |
| SAM_ARCHITECTURE L127 | "Providers are replaceable implementations." | **CONTRADICTS.** Provider internal Runtime tidak replaceable tanpa perubahan Runtime. |

### Assessment

**TIDAK DIDUKUNG — DITOLAK.** Alternative C melanggar (a) pemetaan 1:1 Specification Layer (R1-001 L24), (b) separation of responsibility (R1-001 L51/L65/L196, SAM_ARCHITECTURE L103), (c) kesetaraan Citizen (CITIZEN_SPEC L863, L947-L957), dan (d) provider independence (SAM_ARCHITECTURE L127). Provider dan Connector adalah branch terpisah di bawah Citizen dalam Citizen Hierarchy — bukan sub-branch dari Runtime.

---

# Decision

**Alternative A dipilih: Runtime Boundary via Contracts + Registry (Universal Citizen Boundary).**

Seluruh akses dari dan menuju Runtime dibatasi melalui Contracts + Registry — dua mekanisme cross-boundary yang ditetapkan oleh baseline beku. Tidak ada mekanisme akses ketiga. Provider dan Connector adalah Citizens di luar chain Runtime yang berinteraksi dengan Runtime melalui mekanisme universal yang sama dengan seluruh interaksi antar-Citizen.

## Konsep Arsitektur Boundary

### External Boundary

External boundary Runtime didefinisikan oleh **Contracts + Registry**. Kedua mekanisme ini membentuk permukaan (surface) Runtime — titik di mana domain internal Runtime berhenti dan dunia Citizen lainnya dimulai. Apa pun di luar permukaan ini (Provider, Connector, Runtime lain, Agent, Citizen masa depan) berinteraksi dengan Runtime hanya melalui Contracts + Registry. External boundary bersifat **struktural** — didefinisikan oleh tipe interaksi (publish/discover/contract), bukan oleh lokasi fisik, jaringan, atau deployment.

Anchor: R1-001 L58 ("The boundary between the Runtime and everything else is the two and only two mechanisms"), R1-001 L65 ("outer surface is Contracts + Registry"), R1-001 L299 ("Boundary bersih: permukaan = Contracts + Registry").

### Interaction Boundary

Setiap interaksi antara Runtime dan Citizen eksternal mengikuti alur: **Registry discovery → Contract → chain Runtime** (atau sebaliknya, chain Runtime → Contract → Registry → eksternal Citizen). Interaksi tidak pernah melewati (bypass) chain Runtime — Approval, Execution, dan Audit tetap berlaku untuk seluruh operasi yang melintasi boundary. Linear causality (R1-001 L104) dipertahankan: aliran interaksi adalah satu arah sepanjang chain; tidak ada jalur samping (side channel).

Anchor: CITIZEN_SPEC L639/L643/L647 (discovery universal melalui Registry), R1-001 L104 (linear causality), R1-001 L116 ("every external interaction goes through Registry"), R1-001 L118 ("No additional interaction is invented").

### Ownership Boundary

**Runtime** memiliki bounded capability domain-nya — governance, processing, verification atas operasi. **Provider/Connector** memiliki external access — komunikasi dengan sistem luar, implementasi transport dan integrasi. Tidak ada tumpang tindih kepemilikan. Runtime tidak memiliki, mengelola, atau mengatur implementasi Provider/Connector. Provider/Connector tidak memiliki kewenangan governance atas operasi Runtime.

Anchor: SAM_ARCHITECTURE L103 (Provider/Connector implement access, NOT exercise governance), R1-001 L51 ("Runtime does not implement external access"), GOVERNANCE L198 ("governance approval" untuk execution affecting external world).

### Runtime Responsibility

Runtime bertanggung jawab untuk:

1. **Govern bounded capability domain** (SAM_ARCHITECTURE) — satu domain, satu Runtime
2. **Menampilkan (expose) Contracts + Registry** sebagai permukaan untuk seluruh interaksi eksternal
3. **Memproses seluruh operasi yang melintasi boundary melalui chain** — Registry → Approval → Execution → Audit — tanpa shortcut

Runtime TIDAK bertanggung jawab untuk: mengimplementasikan external access, mengelola lifecycle Provider/Connector, memverifikasi implementasi Provider/Connector, atau menyediakan SDK/API/protocol untuk integrasi eksternal.

Anchor: R1-001 R1-R10 (10 responsibilities — tidak termasuk external access), SAM_ARCHITECTURE (govern bounded domain), R1-001 L65 (inside vs outside), GOVERNANCE L283 ("provider independence").

### Citizen Responsibility

Seluruh Citizen — Runtime, Provider, Connector, Agent, dan Citizen masa depan — tunduk pada aturan konstitusional yang identik:

- Setiap Citizen **mempublikasikan capability** ke Registry (CITIZEN_SPEC L643)
- Setiap Citizen **menemukan (discover) Citizen lain melalui Registry** saja (CITIZEN_SPEC L647)
- Setiap Citizen **berkomunikasi melalui Contract** (CONTRACT_SPEC L55)
- Setiap Citizen **tunduk pada aturan konstitusional yang sama** (CITIZEN_SPEC L875)
- **Tidak ada Citizen yang memiliki privilej konstitusional** (CITIZEN_SPEC L859)

Ini berarti: Provider berinteraksi dengan Runtime melalui Registry + Contract, sama seperti Runtime berinteraksi dengan Provider. ONE universal mechanism for ALL Citizens.

Anchor: CITIZEN_SPEC L79/L639/L643/L647/L859/L863/L875, CONTRACT_SPEC L55.

### Termination Boundary

Kegagalan tidak merambat melintasi boundary ownership:

- **Kegagalan internal Runtime** (Registry gagal, Approval gagal, Execution gagal, Audit gagal) → merambat secara linear melalui chain Runtime → berakhir di Audit Recorder (ADR-004: Audit Recorder = titik terminasi)
- **Kegagalan external access/communication** → berakhir di layer Provider/Connector (R1-001 L196), TIDAK merambat masuk ke chain internal Runtime
- **Kegagalan interaksi antar Citizen** → dikelola sebagai kegagalan Contract/Registry, bukan sebagai kegagalan Runtime atau kegagalan Provider

Termination boundary mengikuti ownership boundary: setiap Citizen bertanggung jawab atas kegagalan di domain-nya sendiri. Tidak ada "failure leakage" antar Citizen.

Anchor: ADR-004 (linear propagation, Audit Recorder = termination point), R1-001 L196, R1-001 Audit 6 (Runtime Failure Boundary).

---

# Architectural Rationale

Alternative A dipilih karena merupakan **satu-satunya alternatif yang muncul dari evidence baseline beku** — bukan diciptakan. Setiap aspek keputusan ini memiliki anchor eksplisit di dokumen otorisasi.

### Mengapa bukan Alternative B atau C?

Alternative B (direct component access) dan Alternative C (Provider inside Runtime) keduanya membutuhkan perubahan pada Foundation (menambah mekanisme akses baru atau menambah komponen Runtime), Specification (mengubah boundary CITIZEN_SPEC atau CONTRACT_SPEC), atau Canonical Architecture (mengubah tanggung jawab SAM_ARCHITECTURE). Alternative A TIDAK mengubah apapun — ia MENGAKUI apa yang sudah ditetapkan oleh baseline beku.

### Kesetaraan Citizen sebagai prinsip pemersatu

CITIZEN_SPEC L859/L863/L875 secara eksplisit menetapkan kesetaraan konstitusional seluruh Citizen. Prinsip ini adalah load-bearing fact: jika Runtime adalah "gerbang" (Alternative A yang tidak dikoreksi) atau Provider adalah "subordinat Runtime" (Alternative C), maka kesetaraan dilanggar. Alternative A yang dikoreksi (boundary universal — berlaku sama untuk seluruh Citizen) adalah SATU-SATUNYA model yang menghormati kesetaraan.

### Non-Ekspansi — tidak menciptakan mekanisme baru

R1-001 L118: "No additional interaction is invented." ADR ini mematuhi prinsip non-ekspansi: ia tidak menciptakan mekanisme boundary baru, tidak menambah komponen Runtime, tidak menciptakan lifecycle baru. Ia hanya menyatakan bahwa mekanisme yang sudah ada (Contracts + Registry) adalah mekanisme yang berlaku — tidak ada yang lain.

### Posisi, bukan mekanisme

C-07 bertanya "DI MANA," bukan "BAGAIMANA." Keputusan ini menjawab posisi: external access (Provider/Connector) berada di LUAR chain Runtime. Mekanisme interaksi (Contracts + Registry) sudah didefinisikan oleh baseline beku — ADR ini tidak menciptakan atau mengubah mekanisme tersebut.

---

# Consequences

## Positive

- Satu boundary universal untuk seluruh Citizen — tidak ada boundary khusus per kategori Citizen
- Kesetaraan konstitusional dihormati — Runtime = Citizen, Provider = Citizen, boundary = identik
- Runtime tetap 7 komponen — tidak ada penambahan
- Provider independence — Provider dapat diganti tanpa mempengaruhi chain Runtime
- Chain Runtime (termasuk Approval gate) berlaku untuk seluruh akses eksternal yang mempengaruhi dunia luar
- Boundary tidak bergantung pada deployment topology (konsisten dengan ADR-000)
- Tidak ada mekanisme akses baru — hanya Contracts + Registry yang sudah ditetapkan

## Negative

- Tidak ada "fast path" atau "privileged access" — seluruh interaksi melalui Contract + Registry yang sama
- Discovery overhead untuk setiap interaksi Citizen-to-Citizen (tanpa cache atau optimasi — di luar scope C-07)
- Model "semua Citizen setara" membatasi optimasi arsitektural untuk high-throughput patterns (di luar scope)
- Seluruh interaksi harus mampu diekspresikan sebagai Capability + Contract — interaksi yang tidak cocok dengan model ini tidak didukung oleh arsitektur

## Accepted Trade-offs

- **Isolation over throughput:** seluruh akses melalui Contracts + Registry — boundary yang ketat, overhead konseptual yang seragam
- **Universality over specialization:** tidak ada mekanisme khusus untuk akses frequent / bulk / streaming (di luar scope)
- **Equality over hierarchy:** Runtime tidak punya posisi privilej terhadap Provider — model flat, bukan bertingkat

---

# Impact Analysis

| Area | Impact |
|---|---|
| **Framework** | Tidak ada perubahan. Contracts + Registry sudah menjadi bagian Specification Layer. |
| **Modules** | Tidak ada modul baru. Runtime tetap 7 komponen. Provider/Connector adalah Citizen terpisah — tidak menjadi modul Runtime. |
| **Documentation** | ADR-006 terdaftar sebagai root ADR berikutnya. GLOSSARY: tambah definisi "External Boundary" jika belum ada. |
| **Tooling** | Tidak ada perubahan. |
| **Repository** | Tidak ada perubahan struktur. |
| **Future Development** | Menetapkan posisi arsitektural yang jelas — setiap komponen masa depan yang berinteraksi dengan Runtime melakukannya melalui Contracts + Registry. |

---

# Dependency Impact

| Dependensi | Status |
|---|---|
| **Ke ADR-000** (Deployment Topology) | External boundary tidak mengubah cohesive Runtime unit. Boundary = struktural, tidak bergantung pada deployment. |
| **Ke ADR-001** (Approval Decision) | Setiap akses eksternal melalui chain Runtime yang mencakup Approval — external access tidak melewati Approval gate. |
| **Ke ADR-002** (Capability Resolution) | Discovery melalui Registry — kebijakan resolusi ADR-002 berlaku seragam untuk seluruh Citizen. |
| **Ke ADR-003** (Idempotency) | Tidak ada perubahan semantik operasi — boundary tidak mempengaruhi properti idempotency. |
| **Ke ADR-004** (Failure Propagation) | Propagation tetap linear sampai Audit — external access failures berakhir di Provider layer. Tidak ada jalur propagasi baru. |
| **Ke ADR-005** (Execution Ordering) | Boundary tidak mengubah urutan eksekusi — ordering adalah internal Execution Scheduler. |

ADR ini tidak memperkenalkan dependensi baru pada modul, package, atau layer. Tidak ada dependency cycle yang tercipta.

---

# Risk Assessment

| Dimension | Assessment |
|---|---|
| Probability | **Low.** Keputusan ini mengakui fakta yang sudah ada di baseline beku — risiko kesalahan minimal. |
| Impact | **High** (jika salah). Boundary yang salah akan melanggar R1-001, CITIZEN_SPEC, atau membutuhkan mekanisme akses baru. |
| Recoverability | **High.** ADR ini adalah decision — dapat di-supersede oleh ADR baru jika model Citizen berubah. |
| Blast Radius | **Low.** Hanya mempengaruhi konsep posisi arsitektural — tidak ada kode, tidak ada modul. |
| Reversibility | **High.** Reversible dengan ADR superseding tanpa perubahan kode. |

---

# Trust Assessment

**Evidence:** 17 kutipan verbatim dari 6 dokumen otorisasi secara konsisten mendukung Alternative A (R1-001 L58/L65/L116/L118/L51/L196/L299; CITIZEN_SPEC L79/L639/L643/L647/L859/L863/L875; CONTRACT_SPEC L55; SAM_ARCHITECTURE L103/L127; GOVERNANCE L198). Tidak ada satupun evidence yang mendukung Alternative B atau C.

**Confidence:** High. Model Citizen universal adalah pondasi CITIZEN_SPECIFICATION — bukan konstruksi baru. Keputusan ini adalah pengakuan arsitektural, bukan penciptaan.

**Unknowns:** Kinerja operasional (throughput, latency) untuk high-frequency Citizen-to-Citizen interaction — tetapi ini adalah masalah implementasi, bukan arsitektur. Di luar scope C-07.

---

# Implementation Notes

**Bukan implementasi.** ADR ini adalah keputusan arsitektural — tidak menetapkan:

- Protokol komunikasi (REST, gRPC, IPC, message queue)
- Format data (JSON, Protobuf, serialization)
- Mekanisme keamanan (authentication, authorization, encryption, TLS)
- SDK atau library untuk Provider/Connector
- Lifecycle management untuk Provider/Connector
- Discovery algorithm (di luar scope — milik ADR-002)
- Contract format atau version negotiation (di luar scope)

Implementasi Runtime, Provider, atau Connector adalah tanggung jawab development — di luar ADR ini.

---

# Migration Strategy

Tidak ada migrasi. ADR ini menetapkan posisi arsitektural untuk Reference Runtime — bukan mengubah arsitektur yang sudah ada. Tidak ada kode yang perlu dimigrasikan.

---

# Success Criteria

- Seluruh interaksi antara Runtime dan Citizen eksternal di masa depan mengikuti model Contracts + Registry
- Tidak ada shortcut atau mekanisme akses ketiga yang muncul di arsitektur implementasi
- Provider/Connector yang dikembangkan di masa depan adalah Citizens yang berdiri sendiri — bukan modul Runtime
- External access failures tetap di layer Provider/Connector — tidak masuk ke chain Runtime

---

# Future Reassessment

| Trigger | Kondisi |
|---|---|
| **Citizen model berubah** | Jika CITIZEN_SPECIFICATION mengubah definisi Citizen atau menambah kategori yang tidak cocok dengan model Contract-based boundary |
| **Kebutuhan akses real-time / streaming** | Jika SAM membutuhkan akses yang tidak bisa dimodelkan sebagai Capability + Contract |
| **Multi-Runtime interop** | Jika interaksi antara banyak Runtime membutuhkan mekanisme boundary tambahan |
| **Performance-critical patterns** | Jika overhead Contracts + Registry menjadi bottleneck arsitektural yang terverifikasi |

---

# Related Documents

- CONSTITUTION (docs/core/CONSTITUTION.md)
- GOVERNANCE (GOVERNANCE.md)
- SAM_ARCHITECTURE (docs/architecture/SAM_ARCHITECTURE.md)
- SPECIFICATION_FREEZE (docs/SPECIFICATION_FREEZE.md)
- CITIZEN_SPECIFICATION (docs/CITIZEN_SPECIFICATION.md)
- CONTRACT_SPECIFICATION (docs/specifications/CONTRACT_SPECIFICATION.md)
- REGISTRY_SPECIFICATION (docs/specifications/REGISTRY_SPECIFICATION.md)
- G0-001_Reference_Runtime_Blueprint (docs/design/G0-001_Reference_Runtime_Blueprint.md)
- R1-001_Minimal_Reference_Runtime_Design (docs/design/R1-001_Minimal_Reference_Runtime_Design.md)
- R2-002_ADR_Candidate_Independence_Certification (docs/design/R2-002_ADR_Candidate_Independence_Certification.md)
- R2-003_ADR_First_Decision_Selection_Record (docs/design/R2-003_ADR_First_Decision_Selection_Record.md)
- ADR-000_Deployment_Topology (docs/adr/ADR-000_Deployment_Topology.md)
- ADR-001_Approval_Decision_Model (docs/adr/ADR-001_Approval_Decision_Model.md)
- ADR-002_Capability_Resolution_Policy (docs/adr/ADR-002_Capability_Resolution_Policy.md)
- ADR-003_Idempotency_Realization_Model (docs/adr/ADR-003_Idempotency_Realization_Model.md)
- ADR-004_Failure_Propagation_Model (docs/adr/ADR-004_Failure_Propagation_Model.md)
- ADR-005_Execution_Ordering_Model (docs/adr/ADR-005_Execution_Ordering_Model.md)

---

# Explicit Consistency Verification

## ADR-000 — Deployment Topology

| Aspek | Status | Bukti |
|---|---|---|
| External boundary tidak mengubah cohesive Runtime unit | ✓ KONSISTEN | Boundary bersifat struktural — Contracts + Registry — tidak bergantung pada jumlah host, lokasi, atau distribusi. ADR-000 L155/L175: C-07 "mendapat konteks authoring yang jelas (posisi relative to one Runtime) — tanpa mengubah validitasnya." |
| Boundary valid regardless of deployment | ✓ KONSISTEN | GOVERNANCE: "should remain valid regardless of deployment topology." Contracts + Registry adalah konsep arsitektural, bukan deployment. |
| Tidak ada topologi baru | ✓ KONSISTEN | ADR ini tidak mengubah atau menambah topologi — tidak memperkenalkan deployment model baru. |

## ADR-001 — Approval Decision

| Aspek | Status | Bukti |
|---|---|---|
| External access tidak melewati Approval | ✓ KONSISTEN | Seluruh interaksi melalui chain Runtime — yang mencakup Approval. GOVERNANCE L198: "Execution affecting the external world should require governance approval." Alternative A memastikan akses eksternal melalui Approval gate. |
| Approval tetap dalam chain | ✓ KONSISTEN | R1-001 L104: chain linear Registry → Contract → Approval → Execution → Audit. External access tidak menambah atau mengurangi langkah chain. |

## ADR-002 — Capability Resolution

| Aspek | Status | Bukti |
|---|---|---|
| Discovery tetap melalui Registry | ✓ KONSISTEN | CITIZEN_SPEC L639/L643/L647 menetapkan Registry sebagai satu-satunya mekanisme discovery — berlaku untuk seluruh Citizen. ADR-002 menetapkan kebijakan resolusi — ADR-006 tidak mengubahnya. |
| Resolution policy berlaku seragam | ✓ KONSISTEN | Registry resolution (ADR-002) berlaku sama untuk Runtime menemukan Provider maupun Provider menemukan Runtime — universality. |

## ADR-003 — Idempotency

| Aspek | Status | Bukti |
|---|---|---|
| External boundary tidak mengubah semantik operasi | ✓ KONSISTEN | Idempotency adalah properti operasi yang dideklarasikan oleh Contract (ADR-003). Boundary — Contracts + Registry — tidak mengubah isi Contract. Posisi eksternal tidak mengubah properti operasi. |

## ADR-004 — Failure Propagation

| Aspek | Status | Bukti |
|---|---|---|
| Propagation tetap linear sampai Audit | ✓ KONSISTEN | ADR-004: linear propagation Registry → Approval → Execution → Audit. ADR-006 menambahkan fakta bahwa external-access failures TERMINATE di Provider/Connector layer (R1-001 L196) — TIDAK merambat masuk ke chain Runtime. Ini KONSISTEN dengan ADR-004: tidak ada jalur propagasi baru di dalam Runtime. |
| Termination boundary jelas | ✓ KONSISTEN | Runtime failures → Audit Recorder; External-access failures → Provider/Connector layer. Tidak ada "failure leakage" antar Citizen. |

## ADR-005 — Execution Ordering

| Aspek | Status | Bukti |
|---|---|---|
| Boundary tidak mengubah ordering | ✓ KONSISTEN | ADR-005 L256: "C-07: ordering tidak mempengaruhi placement Provider/Connector — ordering adalah internal Execution." Operasi dari Citizen eksternal memasuki chain yang sama — di-queue dalam urutan Approval-arrival (ADR-005 Strict Linear). |

**Verification Verdict: KONSISTEN dengan seluruh root ADR (ADR-000 s.d. ADR-005).** Tidak ada kontradiksi. ADR-006 menambahkan fakta arsitektural baru (boundary) tanpa mengubah keputusan yang sudah ada.

---

# Architectural Boundary

ADR ini TIDAK menciptakan:

| Kategori | Tidak dibuat | Anchor |
|---|---|---|
| Lifecycle | Provider lifecycle | CITIZEN_SPEC sudah mendefinisikan Provider sebagai Citizen — lifecycle Citizen sudah ada |
| Lifecycle | Connector lifecycle | CITIZEN_SPEC sudah mendefinisikan Connector sebagai Citizen — lifecycle Citizen sudah ada |
| SDK | Provider/Connector SDK | Di luar scope — implementasi |
| Protocol | Komunikasi protocol | Di luar scope — implementasi |
| Transport | Transport layer | Di luar scope — implementasi |
| API | API definition | Di luar scope — implementasi |
| Authentication | Auth mechanism | Di luar scope — implementasi |
| Authorization | AuthZ mechanism | Di luar scope — implementasi |
| Security | Security model | Di luar scope — implementasi |
| Concurrency | Concurrent access model | Di luar scope — implementasi |
| Deployment | Deployment model baru | ADR-000 sudah Accepted |
| Authority | Authority/domain baru | Semua authority sudah ada di baseline beku |

---

# Out of Scope

ADR ini secara eksplisit TIDAK membahas:

| Di luar scope |
|---|
| REST |
| HTTP |
| gRPC |
| WebSocket |
| IPC |
| RPC |
| Message Queue |
| Event Bus |
| Serialization |
| JSON |
| Protobuf |
| Authentication |
| Authorization |
| Encryption |
| TLS |
| SDK |
| Connector implementation |
| Provider implementation |
| Runtime implementation |
| Validation |

---

# Review History

| Date | Reviewer | Outcome |
|---|---|---|
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

# Audit Trail

## Audit 1 — Problem Coverage

| Pertanyaan | Status |
|---|---|
| Apakah problem statement menjawab satu pertanyaan arsitektural? | ✓ Satu pertanyaan: bagaimana seluruh akses dibatasi melalui mekanisme arsitektural yang sama |
| Apakah seluruh aspek problem ter-cover oleh decision? | ✓ Decision mencakup external boundary, interaction boundary, ownership boundary, Runtime responsibility, Citizen responsibility, termination boundary — seluruh 6 aspek konseptual |
| Apakah ada sub-problem yang tidak terjawab? | Tidak. C-07 adalah satu keputusan atomik. |

**Verdict: LULUS.**

## Audit 2 — Alternative Coverage

| Alternatif | Evidence | Verdict |
|---|---|---|
| Alternative A — Runtime Boundary via Contracts + Registry | 17 evidence dari 6 dokumen mendukung | Didukung penuh |
| Alternative B — Direct component access | 7 evidence menolak; 0 evidence mendukung | Ditolak |
| Alternative C — Provider inside Runtime | 8 evidence menolak; 0 evidence mendukung | Ditolak |

**Verdict: LULUS.** Seluruh alternatif yang reasonable telah dievaluasi. Tidak ada alternatif berbasis evidence yang terlewat.

## Audit 3 — Foundation Compliance

| Foundation Document | Status |
|---|---|
| CONSTITUTION (docs/core/CONSTITUTION.md) | ✓ KONSISTEN — Article: Citizen as constitutional participant, Contract as boundary mechanism |
| GOVERNANCE (GOVERNANCE.md) | ✓ KONSISTEN — L198 (external world governance), L283 (provider independence) |
| SAM_ARCHITECTURE (docs/architecture/SAM_ARCHITECTURE.md) | ✓ KONSISTEN — L84 (Providers/Connectors), L103 (responsibility separation), L127 (replaceable) |
| PHILOSOPHY (docs/PHILOSOPHY.md) | ✓ KONSISTEN — tidak ada kontradiksi |

**Verdict: LULUS.** Tidak ada perubahan Foundation. Semua klaim ter-anchor ke dokumen Foundation.

## Audit 4 — Specification Compliance

| Specification | Status |
|---|---|
| CITIZEN_SPECIFICATION | ✓ KONSISTEN — L55/L59/L79/L145/L149/L639/L643/L647/L859/L863/L875/L947-L957; Provider/Connector = Citizens, all equal |
| CONTRACT_SPECIFICATION | ✓ KONSISTEN — L55: Contract = boundary between Citizens |
| REGISTRY_SPECIFICATION | ✓ KONSISTEN — L53: Registry makes Capabilities discoverable |
| APPROVAL_SPECIFICATION | ✓ KONSISTEN — access through chain preserves Approval gate |
| EXECUTION_SPECIFICATION | ✓ KONSISTEN — Execution tetap dalam chain internal Runtime |
| AUDIT_SPECIFICATION | ✓ KONSISTEN — Audit Recorder tetap titik terminasi internal |
| SPECIFICATION_FREEZE | ✓ KONSISTEN — tidak ada perubahan pada Specification Layer |

**Verdict: LULUS.** Tidak ada perubahan Specification. Specification Layer tetap beku.

## Audit 5 — Root ADR Consistency

| Root ADR | Status |
|---|---|
| ADR-000 — Deployment Topology | ✓ KONSISTEN — boundary struktural, deployment-independent |
| ADR-001 — Approval Decision | ✓ KONSISTEN — access tidak melewati Approval |
| ADR-002 — Capability Resolution | ✓ KONSISTEN — discovery melalui Registry, resolution policy uniform |
| ADR-003 — Idempotency | ✓ KONSISTEN — boundary tidak mengubah semantics |
| ADR-004 — Failure Propagation | ✓ KONSISTEN — propagation linear sampai Audit |
| ADR-005 — Execution Ordering | ✓ KONSISTEN — ordering internal Execution |

**Verdict: LULUS.** Konsisten dengan seluruh root ADR (6/6). Detail terlampir di Explicit Consistency Verification.

## Audit 6 — Runtime Boundary Consistency

| Boundary Aspect | Status |
|---|---|
| R1-001 Audit 1: inside/outside Runtime | ✓ KONSISTEN — external access tetap di luar |
| R1-001 L58/L65: Contracts + Registry surface | ✓ KONSISTEN — ditegaskan kembali, bukan diubah |
| R1-001 L104: linear causality | ✓ KONSISTEN — interaction boundary mengikuti chain |
| R1-001 L116: every external interaction through Registry | ✓ KONSISTEN — ditegaskan sebagai satu-satunya jalur |
| R1-001 L51: "Runtime does not implement external access" | ✓ KONSISTEN — Provider/Connector di luar |
| R1-001 L196: external access failures stay outside | ✓ KONSISTEN — termination boundary jelas |
| R1-001 L24: 7 komponen 1:1 | ✓ KONSISTEN — tidak menambah komponen |

**Verdict: LULUS.** ADR-006 adalah pengakuan arsitektural dari boundary R1-001 — bukan perubahan.

## Audit 7 — Implementation Independence

| Cek | Status |
|---|---|
| Tidak ada protokol (REST/gRPC/HTTP/WebSocket) | ✓ |
| Tidak ada format data (JSON/Protobuf/serialization) | ✓ |
| Tidak ada mekanisme keamanan (auth/TLS/encryption) | ✓ |
| Tidak ada SDK/library | ✓ |
| Tidak ada implementasi Provider/Connector | ✓ |
| Tidak ada transport/RPC/MQ | ✓ |
| Tidak ada API definition | ✓ |
| Tidak ada concurrency/scheduling | ✓ |

**Verdict: LULUS.** ADR murni konsep arsitektural — tidak ada kontaminasi implementasi.

## Audit 8 — Final ADR Validation

| Kriteria | Status |
|---|---|
| Satu keputusan arsitektur | ✓ "Bagaimana seluruh akses dibatasi" — satu pertanyaan, satu jawaban |
| Seluruh alternatif berbasis evidence | ✓ 17 evidence (A), 7 counter-evidence (B), 8 counter-evidence (C) |
| Seluruh driver memiliki anchor dokumen | ✓ D-1 s.d. D-10 — seluruhnya dengan anchor eksplisit |
| Tidak mengubah Foundation | ✓ Hanya mengakui fakta yang sudah ada |
| Tidak mengubah Specification | ✓ Specification Layer tetap beku |
| Tidak mengubah Blueprint | ✓ G0-001: C-07 sekarang terjawab |
| Konsisten dengan ADR-000 s.d. ADR-005 | ✓ 6/6 lulus consistency verification |
| Tidak memperkenalkan konsep implementasi | ✓ 0 kontaminasi implementasi |
| STOP tidak aktif | ✓ Lihat STOP section |

**Verdict: LULUS.** ADR-006 memenuhi seluruh acceptance criteria.

---

# STOP

| Trigger | Hadir? | Bukti |
|---|---|---|
| Membutuhkan perubahan Foundation | **Tidak** | Hanya mengakui fakta dari CONSTITUTION, GOVERNANCE, SAM_ARCHITECTURE, PHILOSOPHY |
| Membutuhkan perubahan Specification | **Tidak** | CITIZEN_SPEC, CONTRACT_SPEC, REGISTRY_SPEC tidak diubah |
| Membutuhkan perubahan Root ADR (ADR-000..005) | **Tidak** | Consistency verification 6/6 lulus — tidak ada yang perlu diubah |
| Membutuhkan perubahan Blueprint G0-001 | **Tidak** | G0-001: C-07 = candidate — ADR-006 menjawab candidate |
| Membutuhkan authority baru | **Tidak** | Provider/Connector sudah ada di CITIZEN_SPEC — tidak ada authority baru |
| Membutuhkan domain baru | **Tidak** | Semua domain sudah ada di baseline beku |
| Membutuhkan lifecycle baru | **Tidak** | Provider/Connector menggunakan lifecycle Citizen yang sudah ada |
| Menemukan kontradiksi struktural | **Tidak** | Semua dokumen konsisten — tidak ada kontradiksi |

**STOP TIDAK AKTIF.** ADR-006 dapat di-Accept.

---

# Completion Checklist

- [x] Metadata complete
- [x] Cross references validated
- [x] Review completed
- [x] Status updated (Accepted)
- [x] Ready for repository publication
