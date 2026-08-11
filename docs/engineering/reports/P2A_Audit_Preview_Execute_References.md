# P2-A — Architet Authority Check: Audit Preview/Execute & Referensi "ADR-008"

> **Sifat:** Inventory HANYA. Tidak ada source yang diubah/dihapus. Ini basis keputusan activation policy.
> **Auditor:** Zara (Engineer) · **Tanggal:** 2026-08-12
> **Metode:** Scan `src/` + `docs/` di repo SAM, verifikasi line-by-line, bukan asumsi.

---

## 1. Latar Permintaan

Verdict arsitektur (dari rekan arsitek) menyatakan:
> "ADR-008 tidak ditemukan di VanM-Hub/SAM; komentar 'ADR-008 sec 12' adalah orphaned/stale reference."

Audit ini memverifikasi klaim tersebut langsung terhadap repo.

---

## 2. HASIL PENTING — Klaim perlu dikoreksi

### 2.1 ADR-008 ADA (berbeda dari yang dilaporkan)
File **ada**: `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md`
Juga terdaftar di `docs/architecture/ARCHITECTURAL_DECISIONS.md` baris 27 sebagai **Accepted**.

### 2.2 Struktur ADR-008 & makna "sec 12"
File ADR-008 punya 15 section. **Section 12 = "Architectural Boundaries"** (baris 188). Isinya:

```
Citizen → Capability → Registry → Contract → Approval → Execution → Audit
```
+"Tidak boleh dibuat jalur alternatif yang melewati boundary resmi."

**Temuan kunci:** Section 12 TIDAK menyebut kata "preview" atau "provider tidak dieksekusi" SAMA SEKALI. Malah, Section 12 **menyertakan langkah Execution** dalam rantai resmi — jadi Section 12 justru **mendukung** execution, bukan melarangnya.

### 2.3 Komentar kode "ADR-008 sec 12: provider tidak dieksekusi" = misreading
Komentar ini muncul 12x di `src/`. Ia menunjuk ke Section 12 sebagai alasan preview-only. Tetapi Section 12 tidak memuat klaim itu. → **Komentar adalah interpretasi yang keliru terhadap Section 12**, bukan kutipan resmi.

### 2.4 ADR-024 "Preview Only Execution" — RETIRED (dibersihkan dari index 2026-08-12)
Semula `docs/architecture/ARCHITECTURAL_DECISIONS.md` baris 43 mencantumkan ADR-024 "Preview Only Execution — Accepted, consolidated into ADR-008". Entri itu ternyata **jejak yang luput** dalam pembersihan ADR yang sudah dihapus (keputusan Van) — ADR-024 sudah retired/dibatalkan.
- **Aksi (2026-08-12):** Entri ADR-024 dihapus dari tabel index; catatan konsolidasi kini menyatakan "ADR-024 Preview Only Execution retired".
- **Implikasi:** Tidak ada keputusan arsitektur aktif bernama "Preview Only Execution". Komentar `mode="preview"` di kode **tidak punya rujukan arsitektur yang sah** — ia hanya kebijakan implementasi default.

---

## 3. Inventory Lengkap Referensi "ADR-008" di `src/`

| File | Baris | Teks | Klasifikasi |
|---|---|---|---|
| `api/llm_wiring.py` | 356 | "Mode preview (ADR-008 sec 12): ApprovalGate otomatis approved (tidak eksekusi" | IMPLEMENTATION POLICY (misread sec 12) |
| `api/llm_wiring.py` | 423 | "(preview, ADR-008). Governance eksternal + execution official path." | IMPLEMENTATION POLICY |
| `api/wiring.py` | 61 | "Provider TIDAK dieksekusi (mode preview, ADR-008 sec 12): external_calls=0." | IMPLEMENTATION POLICY (misread) |
| `api/wiring.py` | 69 | `mode="preview", # preview-only (ADR-008 sec 12); bukan execute` | IMPLEMENTATION POLICY |
| `mission_cognition/runtime.py` | 165 | "provider/operation di-pass dari wiring, mode tetap preview (ADR-008)." | IMPLEMENTATION POLICY |
| `mission_cognition/runtime.py` | 355 | "Execution (serah ke jalur resmi - ADR-008 Real Execution Runtime)" | VALID AUTHORITY (merujuk rantai resmi) |
| `mission_cognition/runtime.py` | 363 | "Ia membangun ExecutionRequest (mode='preview', ADR-008..." | IMPLEMENTATION POLICY |
| `mission_cognition/runtime.py` | 376 | "Bangun request resmi (immutable, preview-only sesuai ADR-008):" | IMPLEMENTATION POLICY |
| `mission_cognition/runtime.py` | 381 | `mode="preview", # ADR-008 sec 12: provider tidak dieksekusi` | IMPLEMENTATION POLICY (misread) |
| `runtime_service/api/conversation_execution_builder.py` | 56 | `mode="preview", # ADR-008 sec 12 preview-only; bukan execute` | IMPLEMENTATION POLICY |
| `runtime_service/api/execution_preview_wiring.py` | 12 | "no network, approval pre-aware. Konsisten ADR-008 sec 12." | IMPLEMENTATION POLICY |
| `runtime_service/api/preview_gateway.py` | 14 | "Konsisten ADR-008 sec 12 (preview-only) & D0-001..." | IMPLEMENTATION POLICY |
| `web/server.py` | 119 | "Provider TIDAK dieksekusi (preview, ADR-008 sec 12)." | IMPLEMENTATION POLICY |
| `web/server.py` | 140 | `mode="preview", # preview-only (ADR-008 sec 12); bukan execute` | IMPLEMENTATION POLICY |
| `web/server.py` | 190 | "Provider TIDAK dieksekusi (ADR-008 sec 12 preview-only)." | IMPLEMENTATION POLICY |

---

## 4. Inventory Referensi "ADR-008" di `docs/`

| File | Baris | Teks | Klasifikasi |
|---|---|---|---|
| `architecture/ARCHITECTURAL_DECISIONS.md` | 27 | ADR-008 Accepted, path ADR-008 file | VALID AUTHORITY |
| `architecture/ARCHITECTURAL_DECISIONS.md` | 30-42,44-47 | ADR-011..023, ADR-025..028 (ADR-024 retired) consolidated into ADR-008 | VALID AUTHORITY |
| `architecture/ARCHITECTURAL_DECISIONS.md` | 86 | Catatan konsolidasi ADR-011..028 → ADR-008 (Decision Authority: CA) | VALID AUTHORITY |
| `engineering/journals/2026-08-11_T3_Execution_Contract.md` | 1, 11 | "MCR serah ke jalur resmi (ADR-008)" — merujuk rantai resmi | VALID AUTHORITY |

---

## 5. Klasifikasi Kelompok (sesuai aturan: VALID / STALE / IMPLEMENTATION / TEST-ONLY / UNRESOLVED)

| Kelompok | Status | Penjelasan |
|---|---|---|
| **Rantai resmi** (ADR-001..007, ADR-006 boundary, Section 12 ADR-008) | 🟢 **VALID AUTHORITY** | Mendefinisikan Citizen→Capability→Registry→Contract→Approval→Execution→Audit. Execution adalah bagian sah. |
| **Komentar `mode="preview"` + "sec 12"** (15 token di src/) | 🟠 **IMPLEMENTATION POLICY (misread)** | Ini keputusan *implementasi* bahwa default = preview. Namun rujukan "sec 12" keliru: Section 12 tidak melarang execution. |
| **ADR-024 "Preview Only Execution"** | 🔴 **RETIRED** (dibersihkan 2026-08-12) | Bukan keputusan aktif. Komentar `mode="preview"` di kode tidak punya dasar arsitektur; hanya kebijakan implementasi. | |
| Rujukan T3 journal "jalur resmi ADR-008" | 🟢 VALID AUTHORITY | Merujuk rantai resmi, bukan preview lock. |
| "mode='preview'" di file lain tanpa rujukan "sec 12" (tidak dalam tabel) | 🟠 IMPLEMENTATION POLICY | Kebijakan default preview, bukan authority arsitektur. |

---

## 6. Kesimpulan Audit P2-A

1. **Execution nyata TIDAK melanggar arsitektur.** Section 12 ADR-008 secara eksplisit memuat langkah **Execution** dalam rantai resmi. Verdict arsitek yang menyatakan ini benar — **terkonfirmasi**.

2. **"ADR-008 sec 12: provider tidak dieksekusi" adalah misreading.** Section 12 tidak memuat larangan eksekusi. Komentar kode tersebut adalah **implementational safety policy** yang kebetulan salah menunjuk ke authority.

3. **ADR-008 ADA** (koreksi terhadap klaim "tidak ditemukan"). Isi file TIDAK memuat "Preview Only". ADR-024 "Preview Only Execution" yang sempat tercantum di index telah **retired/dibatalkan** dan dibersihkan dari index (2026-08-12) — jadi preview-only bukan keputusan arsitektur aktif.

4. **Keputusan yang hilang = activation policy**, bukan arsitektur. Semua rantai arsitektural (Approval→Execution→Audit) sudah ada dan sah. Yang belum ditetapkan: **dalam kondisi apa mode EXECUTE diaktifkan**.

---

## 7. Rekomendasi (untuk P2-B — activation policy)

- [x] ADR-024 "Preview Only Execution" telah retired & dibersihkan dari index (2026-08-12) — bukan keputusan aktif.
- [ ] Tetapkan `ExecutionMode` (PREVIEW / EXECUTE) sebagai **kebijakan implementasi**, bukan mengubah arsitektur.
- [ ] Batasi EXECUTE ke satu controlled path (RealExecutionHarness), bukan global.
- [ ] Jangan tulis ADR baru sampai activation policy P2-B ditetapkan.
- [ ] Pertahankan Approval sebagai gate (R5-001), sesuai Section 12 rantai resmi.

---

*Artefak P2-A. Hanya inventory — tidak ada source yang diubah.*
