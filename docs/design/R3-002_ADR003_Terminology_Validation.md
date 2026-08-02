# R3-002 — ADR-003 Terminology Validation

| Field | Value |
|---|---|
| **Review ID** | R3-002 |
| **Title** | ADR-003 Terminology Validation |
| **Type** | Read-only terminology validation audit |
| **Scope** | EXECUTIVE_SPECIFICATION + ADR-003 + referensi Foundation yang diperlukan |
| **Auditor** | ZARA |
| **Date** | 2026-08-03 |
| **Directive** | Chief Architect Directive R3-002 |
| **Verdict** | **B — Architectural Extension** |

---

## 1. Purpose

Validasi apakah istilah **"Execution Conflict"** pada ADR-003 merupakan:

- **(A)** tipe failure baru,
- **(B)** terminologi operasional dari **Execution Failure** yang sudah ada,
- atau **(C)** kontradiksi terhadap Specification.

Audit ini **read-only**: hanya memastikan interpretasi yang benar. **Tidak memperbaiki, tidak memilih solusi, tidak mengubah dokumen, tidak membuat ADR baru, tidak membuat proposal wording.** Mandat: bukti, bukan intuisi.

---

## 2. Prinsip Pembuktian

Sesuai semangat Project SAM, kesimpulan audit didasarkan pada **buktibukti verifikasi langsung** terhadap dokumen sumber — bukan pada kesan "terlihat salah". Setiap audit di bawah menyertakan lokasi baris yang diverifikasi.

---

## 3. Ringkasan Temuan Kunci (Bukti)

| # | Fakta terverifikasi | Lokasi |
|---|---|---|
| K1 | Istilah **"Execution Conflict" HANYA** muncul di ADR-003 — tidak ada di EXECUTION_SPEC, CONTRACT_SPEC, REGISTRY_SPEC. Lahir di ADR-003. | `ADR-003` L144, L171, L229, L231, L234, L241, L276, L277, L287, L296, L308 |
| K2 | **Failure set EXECUTION_SPEC bersifat tertutup**: "All failures are observable and defined by this specification." | `EXECUTION_SPEC` L163 |
| K3 | Enam defined failure EXECUTION_SPEC: Missing Approval, Invalid Approval, Missing Contract, Capability Unavailable, Execution Timeout, **Execution Failure**. "Execution Conflict" **tidak** ada di antaranya. | `EXECUTION_SPEC` L154–L161 |
| K4 | **"Execution Failure"** didefinisikan sebagai "the operation did not complete successfully." | `EXECUTION_SPEC` L161 |
| K5 | Rule pengulangan idempotency (mandat behavior): "A Completed Execution SHALL NOT be re-executed as a new Execution unless the operation is idempotent." — **SHALL NOT**, larangan normatif terhadap pembentukan Execution baru. | `EXECUTION_SPEC` L175 |
| K6 | Spec **tidak** menetapkan label/surface failure untuk kasus "pengulangan ditolak" — surface mengembalikan refusal **tidak disebutkan** di defined failures; hanya behavior yang dimandatkan (L173–L175). | `EXECUTION_SPEC` L173–L175, L150–L163 |
| K7 | ADR-003 L277 sendiri **meng-ekuivokasi**: "defined failure baru **(atau sub-tipe dari Execution Failure** yang sudah ada)". Penulis mengakui dua bacaan yang berbeda. | `ADR-003` L277 |
| K8 | Precedence "Conflict" di framework: **APPROVAL_SPEC** mendefinisikan **"Approval Conflict"** sebagai defined failure peer (bukan sub-tipe) dalam daftar tertutupnya: "an Approval State contradicts the requested operation." Pola penamaan "...Conflict" adalah konvensi arsitektural eksisting. | `APPROVAL_SPEC` L155 |
| K9 | Makna "Conflict" dalam framework = **suatu state/kondisi yang mengkontradiksi operasi yang diminta** (Approval Conflict: Approval State contradicts operation). Ini alignment dengan makna Execution Conflict ("operasi sudah Completed dan non-idempotent" — Completed state mengkontradiksi permintaan re-execution). | `APPROVAL_SPEC` L155; `ADR-003` L171 |

---

## 4. Audit 1 — Terminology Origin

**Pertanyaan:** Dari mana istilah "Execution Conflict" berasal? Pernah muncul sebelumnya, atau pertama kali lahir di ADR-003?

**Analisis (bukti):**
- Pencarian menyeluruh atas `EXECUTION_SPECIFICATION`, `CONTRACT_SPECIFICATION`, `REGISTRY_SPECIFICATION`, `APPROVAL_SPECIFICATION` menunjukkan **tidak ada** "Execution Conflict" di dokumen manapun selain ADR-003.
- Istilah **"Conflict"** sendiri eksis di framework (APPROVAL_SPEC L155 "Approval Conflict"), tetapi **"Execution Conflict"** spesifik **tidak pernah** muncul sebelum ADR-003.
- ADR-003 L277 bahkan menandai statusnya dengan ekuivokasi "defined failure baru (atau sub-tipe ...)" — menandakan istilah ini dibentuk selama penulisan ADR-003.

**Hasil:** Istilah **"Execution Conflict" lahir pertama kali di ADR-003**. Tidak ada jejak sebelumnya di Specification Layer. (K1, K8)

---

## 5. Audit 2 — Specification Vocabulary

**Pertanyaan:** Verifikasi seluruh vocabulary failure EXECUTION_SPEC. Apakah failure set memang bersifat tertutup?

**Analisis (bukti):**
- EXECUTION_SPEC Failure Behaviour (L150–L163) menyatakan: "Execution SHALL return a **defined failure** rather than an unintended outcome" + daftar enam defined failure + penutup **"All failures are observable and defined by this specification."** (L163).
- Pernyataan L163 bersifat **tertutup**: tidak ada klausa "dan lain-lain", tidak ada mekanisme ekstensi, tidak ada "or any other".
- Interoperability L188–L191 mensyaratkan "Return the **defined failures**" — konsisten dengan himpunan tertutup.
- **"Execution Conflict" TIDAK termasuk** dalam enam defined failure.

**Hasil:** Failure set EXECUTION_SPEC **tertutup** dengan **enam** tipe. "Execution Conflict" **berada di luar** vocabulary defined failure Specification. (K2, K3)

---

## 6. Audit 3 — Semantic Mapping

**Pertanyaan:** Dapatkah "Execution Conflict" dipetakan **sepenuhnya (lossless)** ke "Execution Failure" tanpa kehilangan makna?

**Analisis (bukti):**
- Makna **Execution Failure** (`EXECUTION_SPEC` L161): "the operation **did not complete successfully**." — menyiratkan operasi yang **mulai berjalan lalu tidak berhasil selesai** (kondisi dalam-domain sebuah Execution yang telah ada).
- Makna **Execution Conflict** (`ADR-003` L171): "operasi sudah **Completed** dan **non-idempotent**" — situasi di mana permintaan **membuat Execution baru** untuk operasi yang sudah selesai dan non-idempotent **ditolak**.
- `EXECUTION_SPEC` L175 memandatkan **prohibition**: "SHALL NOT be **re-executed as a new Execution**" — artinya untuk operasi non-idempotent, **Execution baru TIDAK boleh eksis**. Refusal ini terjadi **di gerbang sebelum Execution terbentuk**, bukan setelah Execution berjalan lalu gagal.
- Karena per L175 refusal menegah *pembentukan* Execution, secara ketat **tidak ada operasi (dalam domain Execution) yang "mulai lalu gagal"** — ada larangan pembentukan. Maka pemetaan lossless ke "an operation did not complete successfully" **tidak sempurna**: "Execution Conflict" membawa makna tambahan (prohibition di pre-creation), bukan murni sinonim "operation failed".
- ADR-003 L277 tidak memperlakukan keduanya sebagai identik — ia memerlukan kata "atau" untuk memisahkan bacaan "tipe baru" vs "sub-tipe", yang menandakan penulis sendiri melihat perbedaan konseptual.

**Hasil:** Pemetaan **TIDAK lossless**. "Execution Conflict" **bukan sinonim murni** dari "Execution Failure" — ia menambahkan makna arsitektural (prohibition gate / pre-creation refusal of an already-Completed operation). (K3, K4, K5, K7)

---

## 7. Audit 4 — Architectural Meaning

**Pertanyaan:** Bandingkan makna "Execution Failure" vs "Execution Conflict". Identik secara arsitektural atau berbeda?

**Analisis (bukti):**

| Dimensi | Execution Failure (`EXECUTION_SPEC` L161) | Execution Conflict (`ADR-003`) |
|---|---|---|
| Domain | In-domain Execution (sebuah Execution yang ada) | Pre-creation / boundary (refusal sebelum Execution baru terbentuk, per L175 SHALL NOT re-execute) |
| Kondisi | Operasi **mulai lalu tidak berhasil selesai** | Permintaan **re-execution ditolak** karena operasi sudah Completed & non-idempotent (L171) |
| Implikasi lifecycle | Result state Failed / Lifecycle Failed (L110/L128) | **Tidak ada** Execution baru (dicegah), tidak ada transisi lifecycle baru |
| Makna | Kegagalan eksekusi operasi | Larangan pembentukan ulang operasi non-idempotent |

**Perbedaan inti:** Execution Failure menggambarkan **kegagalan sebuah Execution**; Execution Conflict menggambarkan **penolakan membentuk Execution baru** untuk operasi yang sudah selesai dan non-idempotent. Keduanya **berbeda secara arsitektural** — bukan identik.

**Hasil:** **Execution Failure ≠ Execution Conflict** secara arsitektural. Execution Conflict membawa makna prohibition/refusal yang tidak dikandung secara eksplisit oleh Execution Failure. (K4, K5)

---

## 8. Audit 5 — Authority Test

**Pertanyaan:** Apabila "Execution Conflict" merupakan tipe baru, apakah ADR punya authority untuk memperkenalkannya?

**Analisis (bukti):**
- Framework: ADR hidup di ruang keputusan yang dibuka oleh baseline beku, **tidak boleh mengubah Specification** (SPECIFICATION_FREEZE + R2-001). Menambah **kategori defined failure baru** ke EXECUTION_SPEC seolah-olah bagian dari daftar tertutupnya (L163) **melampaui authority** ADR — itu perubahan Specification.
- Namun EXECUTION_SPEC **tidak menetapkan surface/label failure** untuk kasus "pengulangan non-idempotent ditolak" (L173–L175 memandatkan *behavior*, bukan *surface*; L150–L163 tidak memuatnya). Ruang ini **terbuka**.
- ADR-003 menamai situasi yang *diakibatkan langsung oleh* aturan spec (L175) dengan istilah "Execution Conflict". Penamaan tersebut berada di ruang terbuka spec — **dapat dijustifikasi** sepanjang dibaca sebagai **label untuk refusal yang ditetapkan oleh behavior spec**, bukan sebagai entri baru dalam daftar tertutup defined-failure spec.
- ADR-003 L277 sendiri mengakui keterbatasan ini dengan menawarkan bacaan "sub-tipe dari Execution Failure" (defer ke taksonomi spec).

**Hasil:** ADR **tidak** memiliki authority untuk menambah **tipe failure baru** ke daftar tertutup EXECUTION_SPEC. Namun ADR **memiliki** authority untuk menamai **situasi refusal** yang ditimbulkan behavior spec (L175) dalam ruang terbuka — selama label itu tidak diklaim sebagai entri baru daftar tertutup spec. (K2, K5, K6, K7)

---

## 9. Audit 6 — Consistency Test

**Pertanyaan:** Apakah ada **interpretasi tunggal** yang membuat **Specification** dan **ADR-003** keduanya benar secara bersamaan?

**Analisis (bukti):**

**Ya — ada interpretasi tunggal yang merekonsiliasi:** baca "Execution Conflict" sebagai **manifestasi khusus / sub-tipe dari "Execution Failure"** (cabang kedua dari ADR-003 L277).

Di bawah bacaan ini:
- **Specification tetap benar:** daftar tertutup enam defined failure (L154–L161) tetap utuh; "Execution Conflict" **tidak** menjadi entri ketujuh dalam taksonomi spec — ia adalah *label yang lebih spesifik* untuk satu instance dari kategori generik **Execution Failure** ("operation did not complete successfully" — di mana re-execution yang diminta memang **tidak berhasil** karena ditolak).
- **ADR-003 tetap benar:** ia mendeskripsikan surface defined-failure yang sama dengan spec, hanya dengan nama yang lebih presisi untuk kasus refusal non-idempotent.

**Namun catatan penting:** interpretasi tunggal ini **berhasil hanya dengan pengorbanan presisi** (Audit 3/4 — makna prohibition tidak lossless dipetakan ke Execution Failure). Rekonsiliasi **mungkin**, tetapi **bukan tanpa biaya semantik** — bukan rekonsiliasi "gratis" yang membuat keduanya sama persis. Ini berbeda dari kesimpulan "murni sinonim".

**Hasil:** Terdapat interpretasi tunggal yang merekonsiliasi keduanya, **tetapi** pemetaannya tidak lossless — keberhasilan rekonsiliasi bergantung pada kesediaan membaca "Execution Conflict" sebagai sub-tipe, yang menelan sebagian makna arsitektural prohibition (Audit 4). (K5, K7)

---

## 10. Audit 7 — Final Classification

Berdasarkan bukti Audit 1–6:

### Verdict yang dipertimbangkan

| Verdict | Definisi | Kesesuaian bukti |
|---|---|---|
| **A — Terminology Only** | "Execution Conflict" = murni sinonim/terminologi dari "Execution Failure", tanpa makna tambahan | **TIDAK cocok.** Pemetaan tidak lossless (Audit 3); makna arsitektural berbeda (Audit 4 — prohibition gate vs operation failure). Bukan murni sinonim. |
| **B — Architectural Extension** | ADR-003 memperkenalkan istilah/surface failure yang **memperluas vocabulary** di luar daftar tertutup EXECUTION_SPEC, namun tetap dalam ruang terbuka behavior spec dan dapat direkonsiliasi sebagai sub-tipe | **COCOK.** "Execution Conflict" lahir di ADR-003 (Audit 1), di luar daftar tertutup spec (Audit 2), maknanya distinct (Audit 4), dalam ruang terbuka spec (Audit 5), dan memerlukan penafsiran sub-tipe untuk rekonsiliasi (Audit 6) — bukan murni sinonim. |
| **C — Specification Contradiction** | ADR-003 secara normatif mengontradiksi EXECUTION_SPEC | **TIDAK cocok.** Spec tidak menetapkan surface untuk kasus refusal (K6); ADR-003 menawarkan bacaan sub-tipe yang defer ke taksonomi spec (K7); tidak ada klaim bahwa salah satu salah. Rekonsiliasi mungkin (Audit 6). |
| **A (baca lain)** | "Execution Conflict" = tipe failure baru yang sah | **TIDAK** — ADR tidak punya authority menambah tipe baru ke daftar tertutup spec (Audit 5). |

### Klasifikasi Final

**VERDICT: B — Architectural Extension**

**Arti:** "Execution Conflict" adalah **istilah arsitektural yang diperkenalkan ADR-003** untuk penolakan re-execution operasi non-idempotent. Ia **memperluas vocabulary failure** di luar daftar tertutup EXECUTION_SPEC, tetapi **bukan kontradiksi** — karena:
1. Muncul pertama kali di ADR-003, bukan dari spec (Audit 1).
2. Di luar enam defined failure spec yang tertutup (Audit 2).
3. Makna arsitekturalnya **berbeda** dari "Execution Failure" (prohibition gate vs operation failure) (Audit 4).
4. Berada dalam ruang terbuka spec — spec memandatkan *behavior* (L175) tetapi tidak menetapkan *surface* (Audit 5).
5. Dapat direkonsiliasi sebagai sub-tipe "Execution Failure", tetapi rekonsiliasi itu tidak lossless (Audit 6).
6. Mengikuti konvensi penamaan "...Conflict" eksisting framework (preseden Approval Conflict, APPROVAL_SPEC L155) (K8, K9).

**Bukan A** karena pemetaan tidak lossless (bukan sinonim murni). **Bukan C** karena tidak mengontradiksi spec (ruang terbuka + bacaan sub-tipe defer).

---

## 11. STOP — Tindakan

Sesuai direktif:

- Karena Verdict = **B** → **Jangan memperbaiki.** Laporkan bukti saja.
- **Tidak** mengubah ADR-003, **tidak** mengubah Specification, **tidak** mengubah Foundation, **tidak** membuat ADR baru, **tidak** membuat proposal wording.
- Audit ini **read-only** — tidak ada file yang diubah.

**Konsekuensi terhadap R3-001:**

- Verdict R3-001 (**B — Minor inconsistency**) **tetap berdiri** untuk temuan ini — dan kini dikonfirmasi dengan klasifikasi R3-002 **Verdict B (Architectural Extension)**.
- Verdict R3-002 **bukan A**, sehingga pernyataan direktif "kalau Verdict A maka Root ADR Layer kembali Verdict A (Certified) tanpa ubah satu kata" **TIDAK berlaku** — bukti menunjukkan istilah ini adalah *architectural extension*, bukan sekadar istilah yang bisa dipetakan lossless ke Execution Failure.
- Namun **bukan** C — sehingga tidak ada kontradiksi Specification yang memaksa apapun. Root ADR Layer **tidak rusak**; hanya ada satu istilah yang memperluas vocabulary failure di luar daftar tertutup spec.

---

## 12. Implikasi untuk Fase Berikutnya (informasi, bukan proposal)

> Karena Verdict B, berikut **fakta** yang relevan untuk diputuskan Chief Architect melalui proses yang benar — **bukan** proposal wording dari audit ini.

- **C-05 (Failure Propagation)** akan "mengonsumsi" status "Execution Conflict" (ADR-003 L234, L308). Verdict B menegaskan bahwa C-05 harus menyadari posisi "Execution Conflict": ia adalah label arsitektural di ruang terbuka, **bukan entri daftar tertutup spec**.
- Bila Chief Architect ingin **stabilisasi terminologi**, proses yang benar adalah lewat lifecycle ADR (bukan pengeditan langsung), dengan basis Verdict B ini sebagai pembuktian.
- Tidak ada paksaan perubahan: Verdict B **tidak** menuntut revisi; ia hanya memberikan dasar pembuktian bila revisi dipertimbangkan.

---

## Review History

| Tanggal | Revisi | Perubahan |
|---|---|---|
| 2026-08-03 | 1.0 | Penulisan awal R3-002 — ADR-003 Terminology Validation |

---

## Author Checklist

- [x] Read-only — tidak mengubah ADR/Specification/Foundation, tidak membuat ADR baru, tidak membuat proposal wording
- [x] 7 audit dijalankan (Origin, Vocabulary, Semantic Mapping, Architectural Meaning, Authority, Consistency, Classification)
- [x] Verdict A/B/C digunakan (hasil: **B — Architectural Extension**)
- [x] Verdict B → jangan memperbaiki; bukti dilaporkan
- [x] Konsekuensi terhadap R3-001 dijelaskan
