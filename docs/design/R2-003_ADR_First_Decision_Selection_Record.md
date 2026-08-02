# R2-003 — ADR-000 Selection Record (Chief Architect Directive)

**Version:** 1.0
**Status:** Selection Record — the **final gate** before the first official ADR is written. It records **why selecting one candidate as the first ADR is a legitimate process decision**, grounded in R1-003 (Several Equivalent) and the lifecycle standardized in R2-001. It does **not** decide architectural content, does **not** write an ADR, does **not** choose a solution, does **not** select a candidate.
**Mode:** Read-only. No ADR, no architectural decision, no solution selection, no candidate selection, no Foundation change, no Specification change.
**Commit intent:** `docs(design): record selection framework for first architectural decision`
**Scope / Authority / Source of Truth:** only C-02, C-03, C-04, C-06; Foundation (Mission, Constitution, Philosophy, Governance, Glossary, Canonical Architecture), the seven Specifications, Blueprint (G0-001), G-series (G1-001…G2-003), R-series (R0-001…R2-002).

---

## Source Anchors (verbatim, read)

| # | Source | Anchor | Grounds |
|---|---|---|---|
| R1a | R1-003 Audit 7 | "Several Equivalent = {C-02, C-03, C-04, C-06}." | The four roots are equally-valid first decisions. |
| R1b | R1-003 Audit 3 | "**No 'before' in R1-002 is an Architectural Necessity.** Every relation is at most Logical or Implementation Convenience… expresses *construction strategy*, not an architectural constraint that a decision's validity depends on." | No valid-first-ADR is forced; order is process strategy. |
| R1c | R1-003 final | ADR-first rationale must be declared as a **process decision**, not an architectural claim. | The selection is process-owned. |
| R2a | R2-001 Audit 7 | Lifecycle valid at 10/100/1000 ADR without Foundation change; per-decision stateless. | Selection of first does not bind the chain. |
| R2b | R2-001 Audit 5 | ADR is **not a new authority**; subordinate recording channel below frozen Spec (G5/F3; "no new authority"). | Selecting a root adds no authority. |
| R2c | R2-002 Output 8 | **C-02, C-03, C-04, C-06 = A — Certified** (atomic architectural decisions). | All four ready; none needs cleanup. |
| R2d | R2-002 Audit 7 | Four roots mutually independent; dependency only outward to C-01/C-05/C-07/C-08. | Selecting one does not disturb the other three. |
| B1 | G0-001 L41 | "Any design decision that requires a trade-off is recorded… as a **Candidate ADR** without being resolved." | Candidates exist in register pre-resolution. |
| B2 | G0-001 L163 | "turned into a formal ADR **only** at the point an implementation-facing decision must be made, and each such ADR must not contradict the frozen baseline." | ADR is written only when implementation-facing; non-contradiction. |
| F1a | SPECIFICATION_FREEZE L28/L37 | "All future design decisions… expressed through ADR"; "All subsequent design decisions belong in the ADR layer." | Selection record does not decide content; content will live in ADR. |
| G1a | GOVERNANCE L125–127 | "Architecture Decisions are documented using ADR." | Decisions go to ADR layer. |
| T1 | ADR_TEMPLATE L61–63 | Status: Draft \| Accepted \| Superseded \| Deprecated. | ADR written later will carry a status; nothing here claims one. |

---

## Output 1 — Candidate Summary

Ringkas identitas keempat kandidat: **tujuan, domain, ruang keputusan.**

| Candidate | Tujuan (purpose) | Domain (arsitektur) | Ruang keputusan (decision space) |
|---|---|---|---|
| **C-02** | Mendefinisikan bagaimana Discovery Resolver memilih saat beberapa Capability memenuhi satu request. | Discovery / Registry (capability resolution). | Exact match vs version-compatible match; trade-off precision vs availability (Blueprint C-02). Constraint tetap: determinism (REGISTRY L147/L149). |
| **C-03** | Mendefinisikan bagaimana Approval Coordinator menghasilkan keputusan otorisasi. | Approval (authorization gate). | Otomatis vs human-mediated; trade-off automation vs oversight. Approval Spec L109 membiarkan mekanisme terbuka. |
| **C-04** | Mendefinisikan bagaimana properti idempotency sebuah operasi dibuat observable. | Execution / Contract (idempotency semantics). | Explicit keys vs operation-defined semantics; trade-off. EXECUTION L177 membiarkan mekanisme terbuka. |
| **C-06** | Mendefinisikan topologi deployment Runtime. | Structural / deployment topology. | Satu Runtime vs distribusi komponen lintas host; trade-off simplicity vs distribution. GOVERNANCE L291–301 membiarkan topologi terbuka. |

Source: Blueprint C-02/C-03/C-04/C-06; S-02/S-03/S-04/S-06; R2-002 Output 1/2.

---

## Output 2 — Selection Criteria

Ekstrak kriteria yang **boleh** dipakai memilih ADR pertama — hanya jika didukung dokumen.

| Kriteria | Diizinkan? | Evidence |
|---|---|---|
| **Process consideration (pertimbangan proses)** | **Ya** | R1c: rationale pemilihan ADR-first adalah *process decision*; R1b: order adalah *construction strategy*. Chief Architect boleh memilih berdasar proses/urutan authoring. |
| **Architectural neutrality (netralitas arsitektur)** | **Ya** | R1a (Several Equivalent = keempat sah); R1b (tidak ada "before" yang Architectural Necessity) → pilihan apa pun tidak mengubah validitas arsitektur. |
| **Documentation continuity (kesinambungan penulisan)** | **Ya** | R1b: "before" = memberi konteks authoring (Logical/Implementation Convenience). Memilih per strand authoring (mis. mulai dari struktural C-06) sah secara dokumentasi. |
| **Implementation dependency (kebutuhan implementasi)** | **Ya (terbatas)** | B2: ADR ditulis "only at the point an implementation-facing decision must be made" → sebuah kandidat boleh dipilih lebih dulu jika keputusan tersebut adalah yang pertama "menghadap implementasi" yang harus diputuskan. Ini satu-satunya kriteria berbasis-dokumen yang bersifat *wajib/waktu*. |
| **Architectural necessity (keharusan arsitektur)** | **Tidak** | R1b: tidak ada "before" yang Architectural Necessity → tidak boleh mengklaim satu root *harus* dulu karena arsitektur. |
| **Fan-out / ripple (dampak ke kandidat lain)** | **Ya (sebagai proses)** | R1-002 menyarankan C-06 "first among equals" oleh fan-out, tapi R1-003 Audit memverifikasi itu *strategy*, bukan necessity. Sah dipakai sebagai *proses*, bukan klaim keharusan. |

**Kesimpulan kriteria:** kriteria yang diizinkan = **process consideration, architectural neutrality, documentation continuity, implementation-facing need (B2), dan fan-out-as-process**. Yang **tidak** diizinkan sebagai klaim keharusan = architectural necessity. Kriteria ini hanya membimbing *cara* memilih, bukan *isi* keputusan.

---

## Output 3 — Selection Constraint

Buktikan apa yang **tidak boleh** dijadikan alasan memilih — jika memang tidak didukung dokumen.

| Constraint (alasan terlarang) | Didukung? | Evidence |
|---|---|---|
| **Preferensi teknologi (tech preference)** | **Tidak didukung** | Tidak ada dokumen yang menghubungkan pemilihan ADR-first dengan teknologi. ADR mencatat keputusan, bukan memilih teknologi (ADR_TEMPLATE "Do not describe implementation"); pemilihan ADR-first tak boleh karena menyukai teknologi tertentu. |
| **Kemudahan implementasi (ease of implementation)** | **Tidak didukung sebagai alasan** | B2 mengizinkan "implementation-facing must be made" sebagai *kapan* menulis, tetapi *kemudahan* implementasi bukan kriteria arsitektur; F1a menyalurkan keputusan ke ADR layer tanpa basis "mudah". Kemudahan bisa menempel pada proses authoring (R1b), bukan pada justifikasi arsitektur. |
| **Opini pribadi (personal opinion)** | **Tidak didukung** | Tidak ada dokumen yang memberi ruang opini pribadi; keputusan berakar pada Framework R1-003 dan lifecycle R2-001. |
| **Urutan buatan sebagai keharusan (artificial/mandated order)** | **Tidak didukung** | R1b: tidak ada "before" yang Architectural Necessity; R2a: per-decision stateless → urutan tidak boleh dipaksakan sebagai keharusan. (Urutan hanya sah sebagai proses/konteks — Output 2.) |
| **Klaim "harus lebih dulu" berdasar arsitektur** | **Tidak didukung** | R1b/R2d; semua root equivalent (R1a), mutually independent (R2d). |
| **Memilih karena "itu yang paling mudah ditulis"** | **Tidak didukung sebagai justifikasi arsitektur** | Boleh sebagai *process/documentation continuity* (Output 2), tetapi tak boleh diklaim sebagai keharusan arsitektur (R1b). |

**Kesimpulan constraint:** preferensi teknologi, kemudahan-implementasi-sebagai-justifikasi, opini pribadi, dan urutan buatan-sebagai-keharusan **tidak didukung dokumen** dan karenanya dilarang menjadi alasan. Yang sah hanyalah kriteria Output 2 (process, neutrality, continuity, implementation-facing need, fan-out-as-process) **tanpa diklaim sebagai necessity arsitektur**.

---

## Output 4 — Selection Justification Framework

Definisikan **bagaimana** Chief Architect boleh memilih salah satu kandidat — **tanpa memilih**. Buktikan dari R1-003 dan R2-001.

```
Several Equivalent                 (R1-003 Audit 7: {C-02, C-03, C-04, C-06})
      ↓  keempat sama-sama sah sebagai ADR pertama; tidak ada necessity arsitektur (R1-003 Audit 3 R1b)
Chief Architect Process Decision   (R1c: rationale = keputusan proses; R2-001 lifecycle)
      ↓  memilih berdasar kriteria Output 2 (process/neutrality/continuity/impl-facing/fan-out-as-process)
ADR-000                             (Candidate → Preparation → Decision → ADR Draft → … → Accepted, R2-001 lifecycle)
```

**Bukti langkah demi langkah:**
1. **Several Equivalent** — R1a: keempat root adalah pilihan sah pertama yang setara; tidak ada yang "must come first" oleh arsitektur (R1b: no Architectural Necessity).
2. **Chief Architect Process Decision** — R1c: *identifikasi & pemilihan* ADR pertama dideklarasikan sebagai **keputusan proses**, bukan klaim konsekuensi arsitektur. Chief Architect adalah pemilik ruang keputusan (R2-001 Audit 2: Decision stage "Chief Architect selects"). Keputusan dilakukan **tanpa** mengklaim the chosen satu lebih penting secara arsitektur (R2d: empat root independent) dan **tanpa** memilih solusi/isi (komitmen R2-003).
3. **ADR-000** — setelah dipilih, kandidat berjalan melalui **lifecycle R2-001** (Candidate → Preparation → Decision → ADR Draft → Verification → Accepted → Reference Runtime → Implementation) sebagai ADR pertama. Verifikasi mensyaratkan **non-contradiction terhadap baseline beku** (B2) dan mekanisme kebijakan dokumentasi (G1a/F1a).

**Kesimpulan framework:** Chief Architect **memiliki otoritas cara** untuk memilih salah satu dari keempat (R1-003), dan pemilihan itu **sah sebagai keputusan proses** (R1c), dijalankan lewat lifecycle yang dibakukan (R2-001), **tanpa** memutus isi arsitektur atau solusi (obyektif R2-003). Framework ini hanya *menampung* pilihan; ia tidak menunjuk kandidat.

---

## Output 5 — Selection Neutrality

Buktikan bahwa memilih salah satu root **tidak mengubah validitas tiga lainnya**.

**Bukti:**
1. **Mutual independence** — R2d (R2-002 Audit 7): keempat root "mutually independent"; dependency hanya **keluar** (root → C-01/C-05/C-07/C-08), bukan antar-root. Memilih C-06 tidak menuntut atau melumpuhkan C-02/C-03/C-04.
2. **No Architectural Necessity** — R1b: tidak ada "before" yang mengikat validitas satu root pada root lain. Keempatnya decidable in any order, kandungannya tetap sah (R2e/R2f).
3. **Order-neutral content** — R1-003 Audit 6 (R2f): semua ADR "order-neutral in content"; urutan hanyalah konteks authoring, bukan pengubah validitas. Menulis yang satu lebih dulu **tidak** mengubah isi valid tiga yang lain.
4. **Per-decision stateless** — R2a: lifecycle valid di skala berapa pun tanpa perubahan Foundation; setiap ADR independen terhadap yang lain.

**Kesimpulan neutrality:** **memilih salah satu root tidak mengubah validitas tiga lainnya.** Kandidat yang belum terpilih tetap **A — Certified** (R2c) dan tetap sah sebagai ADR berikutnya; pemilihan pertama hanyalah *urutan penulisan*, bukan *peringkat validitas*.

---

## Output 6 — Future Sequence

Jelaskan konsekuensi setelah ADR pertama selesai: **Remaining Candidate → Future ADR**, tanpa mengubah Foundation.

```
ADR-000 (Accepted)               — kandidat terpilih, terselesaikan via lifecycle R2-001
        ↓
Remaining Candidate(s)           — 3 root tersisa (masing-masing tetap A-Certified, R2c; mutually independent R2d)
        ↓  "turned into a formal ADR only at the point an implementation-facing decision must be made" (B2)
Future ADR(s)                    — ditulis saat perlu, melalui lifecycle R2-001 yang sama
        ↓
C-01 / C-05 / C-07 / C-08        — kandidat non-root (konteks authoring dari root; R2f) menyusul
        ↓
Reference Runtime & Implementation — G3: implementation realizes the architecture; B2: must not contradict baseline
```

**Konsekuensi (semua tanpa mengubah Foundation):**
1. Setelah ADR-000 Accepted, **sisa proses dan ADR berikutnya mengikuti lifecycle yang sama** (R2-001); tidak ada kebutuhan mengubah Foundation (R2a: stateless, F1/F5; R2b: ADR bukan authority baru).
2. **Remaining root (3) tetap A-Certified** (R2c) dan **tidak berkurang validitasnya** oleh pilihan pertama (Output 5). Masing-masing menjadi Future ADR saat "implementation-facing decision" muncul (B2).
3. **Kandidat non-root (C-01/C-05/C-07/C-08)** menyusul; dependency-nya terhadap root adalah *konteks authoring*, bukan validitas (R2f) — sehingga menulis root lebih dulu **memperkaya konteks** bagi yang non-root tanpa mengubah kewajiban arsitektur.
4. Akhirnya **Reference Runtime & Implementation** mewujudkan arsitektur (G3), dengan setiap ADR **tidak bertentangan dengan baseline beku** (B2) dan **tanpa menyentuh Foundation** (F1a/F5).

**Kesimpulan Future Sequence:** memasuki fase Architectural Decision Making ini **tidak menutup** kandidat lain; ia **membuka** produksi ADR berurutan dalam satu lifecycle, semuanya **di bawah baseline beku yang tak berubah** (A→S→Blueprint→ADR→Implementation; R1-004 layer).

---

## Output 7 — Certification

Satu verdict: **Ready** atau **Not Ready** untuk memulai ADR pertama.

**Verdict: READY**

**Dasar:**
- Semua fase discovery **CLOSED/FROZEN/CERTIFIED** (Foundation CLOSED, Specification FROZEN, Discovery CLOSED, Process DEFINED, Candidates CERTIFIED — R2-002 Output 8 A).
- Empat root **A — Certified** (R2c) dan **mutually independent** (R2d) → layak sebagai ADR pertama.
- Seleksi dideklarasikan sebagai **keputusan proses yang sah** (R1c) via framework Output 4.
- Neutraity (Output 5) & Future Sequence (Output 6) terjaga — pilihan tidak merusak kandidat lain, tidak menyentuh Foundation.
- **STOP tidak aktif** (lihat bawah).

→ **READY.** Project SAM dapat memasuki **Architectural Decision Making** dan menulis **ADR resmi pertama** dari salah satu root, sesuai lifecycle R2-001 dan framework R2-003.

---

## Validation (8 Audit)

### Audit 1 — Candidate Summary
**LULUS.** Keempat kandidat dirangkum dalam tujuan/domain/ruang keputusan (Output 1) dengan anchor Blueprint + Spec (S-02/S-03/S-04/S-06). Tidak ada kandidat yang lolos dari ringkasan identitas.

### Audit 2 — Selection Criteria
**LULUS.** Kriteria yang diizinkan diekstrak **hanya yang didukung dokumen** (Output 2): process consideration (R1c), architectural neutrality (R1a/R1b), documentation continuity (R1b), implementation-facing need (B2), fan-out-as-process (R1-002 + R1-003 note). Architectural necessity di-*exclude* karena R1b. Tidak ada kriteria non-dokumen.

### Audit 3 — Selection Constraint
**LULUS.** Hal yang **tidak boleh** menjadi alasan dibuktikan tidak didukung (Output 3): tech preference, ease-of-implementation-as-justification, personal opinion, artificial/mandated order, klaim "harus lebih dulu" — semuanya dilarang karena tak berakar dokumen (R1b, ADR_TEMPLATE no-implementation, F1a). Tidak ada alasan terlarang yang lolos.

### Audit 4 — Selection Neutrality
**LULUS.** Memilih satu root tidak mengubah validitas tiga lainnya (Output 5): mutual independence (R2d), no Architectural Necessity (R1b), order-neutral content (R2f), per-decision stateless (R2a). Kandidat lain tetap A-Certified (R2c).

### Audit 5 — Future Sequence
**LULUS.** Setelah ADR pertama selesai, Remaining Candidate → Future ADR berlanjut dalam lifecycle R2-001 yang sama, tanpa mengubah Foundation (Output 6; B2, G3, F1a/F5, R2a). Urutan = konteks authoring, bukan kewajiban.

### Audit 6 — Authority Preservation
**LULUS.** Tidak ada authority baru: seleksi adalah **keputusan proses Chief Architect** (R1c), ADR tetap kanal subordinat di bawah Spec beku (R2b; G1a/F1a; R1-003 Audit 5 "no new authority"). Framework R2-003 tidak menaikkan status siapa pun; ia hanya menegaskan otoritas cara yang sudah ada (R1-003).

### Audit 7 — ADR Process Compliance
**LULUS.** Seleksi mematuhi lifecycle R2-001: kandidat berjalan Candidate → … → ADR-000 (Output 4); ADR hanya ditulis saat implementation-facing (B2); non-contradiction dengan baseline (B2); ADR mencatat, bukan mengimplementasi (ADR_TEMPLATE/F1a). Tidak ada deviasi dari proses.

### Audit 8 — Final Readiness
**LULUS.** Konsekuensi: **READY** (Output 7). Semua prasyarat terpenuhi (discovery closed, 4 root A-Certified, proses DEFINED, framework seleksi sah, STOP tidak aktif). Tidak ada pekerjaan discovery tersisa (Catatan Chief Architect: "setelah R2-003 selesai, tidak ada lagi pekerjaan discovery").

---

## STOP Condition

Hentikan bila ditemukan salah satu kondisi berikut → jangan memilih kandidat, jangan buat ADR, jangan buat proposal solusi; hanya lapor.

| Trigger | Hadir? | Bukti |
|---|---|---|
| **Masih ada discovery yang belum selesai** | **Tidak** | R1-004 Verdict A (Architecture Discovery CLOSED); R2-001 (Process DEFINED); R2-002 (Candidates CERTIFIED). Catatan Chief Architect menegaskan tanpa pekerjaan discovery tersisa. |
| **Kandidat belum independen** | **Tidak** | R2-002: keempat A-Certified, mutually independent (R2c/R2d); R1-003 Audit 2 no hidden dependency. |
| **Proses ADR belum lengkap** | **Tidak** | R2-001 mendefinisikan lifecycle lengkap (8 tahap + gate + compliance). |
| **Perlu mengubah Foundation** | **Tidak** | R2a/R2b/F1a/F5: lifecycle & seleksi beroperasi sepenuhnya di bawah baseline beku; tidak ada kebutuhan ubah Foundation. |
| **Perlu mengubah Specification** | **Tidak** | F1a/F5/B2: ADR mencatat keputusan tanpa mengubah Spec; seleksi tidak menyentuh SPEC anchor (S-02/S-03/S-04/S-06 tetap). |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP tidak aktif.** Project SAM **READY** untuk menulis ADR resmi pertama.

---

## Final Statement

R2-003 mencatat — secara read-only — bahwa **pemilihan ADR pertama adalah keputusan proses yang sah**, sebelum ADR resmi ditulis. Ini **bukan** ADR, **bukan** keputusan arsitektur, **bukan** pemilihan solusi, dan **bukan** penunjukan kandidat. Ia hanya mendefinisikan *mengapa dan bagaimana* Chief Architect boleh memilih.

**Ringkasan:**
- **Candidate Summary** (Output 1): empat root dirangkum (tujuan/domain/ruang keputusan) dari Blueprint + Spec.
- **Selection Criteria** (Output 2): kriteria yang diizinkan (process, neutrality, continuity, implementation-facing need, fan-out-as-process) — semua berakar dokumen.
- **Selection Constraint** (Output 3): alasan terlarang (tech preference, ease-of-impl, personal opinion, artificial order, keharusan) dibuktikan tidak didukung.
- **Justification Framework** (Output 4): Several Equivalent → Chief Architect Process Decision → ADR-000, dibuktikan dari R1-003 & R2-001 — **tanpa memilih**.
- **Selection Neutrality** (Output 5): memilih satu root tidak mengubah validitas tiga lainnya.
- **Future Sequence** (Output 6): Remaining → Future ADR dalam lifecycle R2-001 yang sama, tanpa mengubah Foundation.
- **Certification** (Output 7): **READY.**
- **STOP tidak aktif** — tidak ada discovery tersisa, kandidat independen, proses lengkap, tanpa ubah Foundation/Specification.

**Arti strategis (menjawab catatan Chief Architect):** ini **gerbang terakhir sebelum ADR pertama benar-benar ditulis**. Dokumen tidak memutuskan isi arsitektur; ia mencatat bahwa **pemilihan ADR pertama adalah keputusan proses yang sah**, sesuai temuan R1-003 (Several Equivalent) dan lifecycle yang dibakukan (R2-001). **Setelah R2-003 ini, tidak ada lagi pekerjaan discovery.** Langkah berikutnya yang tersisa hanyalah **menulis ADR resmi pertama** (dari salah satu C-02/C-03/C-04/C-06) dan menjalankannya lewat lifecycle R2-001. Deliverable: `docs/design/R2-003_ADR_First_Decision_Selection_Record.md`.

**Commit intent:** `docs(design): record selection framework for first architectural decision`
