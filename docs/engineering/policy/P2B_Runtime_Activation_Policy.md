# P2-B — Runtime Execution Activation Policy (Implementation Policy)

> **Jenis:** Implementation Policy — BUKAN ADR baru.
> **Kedudukan:** Menetapkan `ExecutionMode` sebagai kebijakan implementasi; tidak mengubah arsitektur (rantai resmi ADR-008 Section 12 tetap otoritas).
> **Status:** DRAFT · Menunggu persetujuan Van · **Tanggal:** 2026-08-12
> **Auditor/Penulis:** Zara (Engineer)

---

## 1. Tujuan

Menetapkan kapan & bagaimana extraksi nyata (REAL external side effect) diizinkan,
dan membedakannya secara tegas dari mode aman (preview). Ini mengakhiri asumsi keliru
bahwa "preview = SAM execution architecture".

---

## 2. ExecutionMode — Dua Mode Sah

```text
ExecutionMode
├── PREVIEW
└── EXECUTE
```

### PREVIEW (mode aman / tanpa efek samping)

```text
Request
  → Governance
  → Simulation / Preview
  → Result
```
- **External side effect = 0** (tidak ada panggilan ke sistem nyata).
- Berlaku untuk analisis, eksplorasi, demo, dan komputasi internal.
- Merupakan mode yang sah — **salah satu** mode, bukan identitas seluruh platform.

### EXECUTE (mode efek samping nyata)

```text
Request
  → Capability
  → Registry
  → Contract
  → Policy
  → Approval
  → Execution
  → REAL External System
  → Verification
  → Audit
```
- **External side effect diperbolehkan**, tetapi **hanya setelah seluruh gate terpenuhi**.
- Setiap langkah adalah gate wajib; tidak boleh dilompati.

---

## 3. Controlled Execution Rule (Wajib)

Untuk tahap pertama, real execution TIDAK mengubah seluruh SAM menjadi execute mode.
Ia DIKURUNG pada satu jalur terkontrol:

```text
EXECUTE
   ↓
RealExecutionHarness
   ↓
Execution Runtime
   ↓
External Adapter
```
- Satu-satunya jalur eksekusi nyata yang diizinkan.
- Rest-of-platform tetap di `PREVIEW` sampai diaktifkan per-capability.
- Ini membuktikan real execution **tanpa membuka seluruh platform sekaligus**.

---

## 4. P2-B Acceptance Criteria — Gate EXECUTE

**EXECUTE hanya boleh aktif apabila SEMUA berikut terpenuhi:**

- [ ] ExecutionMode secara eksplisit = `EXECUTE`
- [ ] Capability resolved
- [ ] Registry entry valid
- [ ] Contract valid
- [ ] Policy evaluation = `ALLOW`
- [ ] Approval = `APPROVED`
- [ ] External boundary valid
- [ ] Credential tersedia lewat approved boundary
- [ ] Execution request immutable
- [ ] Correlation ID tersedia
- [ ] Timeout tersedia
- [ ] Failure handling tersedia
- [ ] Verification tersedia
- [ ] Audit tersedia

> **Invariant:** Jika salah satu gate gagal → **NO EXTERNAL SIDE EFFECT.**
> Default adalah `PREVIEW`; `EXECUTE` hanya diperoleh dengan memenuhi semua gate di atas.

---

## 5. Sikap terhadap Komentar `mode="preview"` & Rujukan "ADR-008 sec 12"

### Yang HARUS diperbaiki (persepsi, bukan source dulu)
Komentar seperti:
```python
# ADR-008 sec 12: provider tidak dieksekusi
```
**tidak boleh lagi diperlakukan sebagai authority**. Bukti (lihat P2-A):
- Section 12 ADR-008 = "Architectural Boundaries" TIDAK memuat larangan eksekusi — malah memuat langkah `Execution` dalam rantai resmi.
- ADR-024 "Preview Only Execution" telah **retired** dan dibersihkan dari index (2026-08-12) — bukan keputusan aktif.

### Yang dipertahankan
- **PREVIEW tetap mode sah** = safe/no-side-effect mode.
- **EXECUTE** = real-side-effect mode.

### Yang dihilangkan (asumsi keliru)
```text
PREVIEW
=
SAM execution architecture
```
Itu **bukan architecture**. Itu hanya **salah satu ExecutionMode**.

---

## 6. Catatan Implementasi (untuk P2-C selanjutnya)

- Perkenalkan tipe `ExecutionMode` (enum/sentinel) dengan nilai `PREVIEW` & `EXECUTE`.
- Default seluruh sistem = `PREVIEW`.
- Satu jalur `RealExecutionHarness` mewajibkan (override) semua gate di bagian 4 sebelum mengeksekusi.
- Komentar source yang menyalahartikan "sec 12" **diperbarui di fase berikutnya** (P2-C), bukan sekarang, agar tetap read-only sampai kebijakan disetujui.

---

*Artefak P2-B. Implementation Policy — mendukung activation tanpa ADR baru.*
