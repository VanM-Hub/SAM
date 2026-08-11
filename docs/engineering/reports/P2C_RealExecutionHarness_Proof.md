# P2-C — Controlled RealExecutionHarness

> **Jenis:** Implementasi vertical slice (bukan ADR baru; mengikuti P2-B Activation Policy).
> **Status:** ✅ COMPLETE — terbukti end-to-end pada filesystem.
> **Tanggal:** 2026-08-12 · **Penulis:** Zara (Engineer)

---

## 1. Apa yang dibangun

Modul: **`src/sam/execution_runtime/real_harness.py`**

Satu-satunya jalur eksekusi nyata (Controlled Execution Rule P2-B):

```text
EXECUTE → RealExecutionHarness → ExecutionRuntime → ExternalAdapter
```

Komponen:
- `ExecutionMode` (PREVIEW / EXECUTE) — enum kebijakan.
- `RealFilesystemAdapter` — adaptor eksternal nyata (read / hash / meta; fase 1 non-destruktif).
- `ExecutionRuntime` — container hasil, timeout, penanganan kegagalan.
- `_verify_external_effect` — verifikasi bahwa outcome benar-benar efek nyata (bukan "Simulated...").
- `ControlledApprover` — gate approval eksplisit (EXECUTE wajib reason).
- `RealExecutionHarness` — mengevaluasi **14 gate P2-B** sebelum eksekusi; invariant `NO EXTERNAL SIDE EFFECT` bila ada gate gagal.

---

## 2. 14 Gate (P2-B Acceptance Criteria) — semua dievaluasi

| # | Gate | Status di harness |
|---|---|---|
| 1 | ExecutionMode eksplisit = EXECUTE | ✅ `req.mode == EXECUTE` |
| 2 | Capability resolved | ✅ ada di registry |
| 3 | Registry entry valid | ✅ registry non-kosong |
| 4 | Contract valid | ✅ contract non-kosong |
| 5 | Policy = ALLOW | ✅ `policy == "ALLOW"` |
| 6 | Approval = APPROVED | ✅ wajib reason untuk EXECUTE |
| 7 | External boundary valid | ✅ `os.path.isfile(target)` |
| 8 | Credential lewat approved boundary | ✅ filesystem lokal (akses OS) |
| 9 | Request immutable | ✅ snapshot terpisah |
| 10 | Correlation ID | ✅ `uuid4` |
| 11 | Timeout | ✅ `timeout_seconds > 0` |
| 12 | Failure handling | ✅ `ExecutionRuntime` try/except |
| 13 | Verification | ✅ `_verify_external_effect` |
| 14 | Audit | ✅ `AuditTrail` merekam tiap langkah |

> **Invariant:** ada gate gagal → `external_effect=False` + `blocked=True`. Terbukti di skenario 2.

---

## 3. Hasil Pengujian End-to-End (5 skenario)

| # | Skenario | Mode | Hasil | Bukti |
|---|---|---|---|---|
| 1 | PREVIEW (read) | PREVIEW | ✅ Aman, `simulated=True`, `external_effect=False`, verifikasi tidak dicek | audit hanya registry+preview |
| 2 | EXECUTE tanpa reason | EXECUTE | ✅ **DIBLOKIR** `blocked_by=['approval']`, `NO EXTERNAL SIDE EFFECT` | `harness.approval.denied` |
| 3 | EXECUTE read | EXECUTE | ✅ **REAL** — isi file 74 byte nyata terbaca, `verification.passed=True` | `harness.adapter.read` |
| 4 | EXECUTE hash | EXECUTE | ✅ **REAL** — `sha256=aef0ca97...0052ed` (64 hex), passed | `harness.adapter.hash` |
| 5 | EXECUTE meta | EXECUTE | ✅ **REAL** — `size=75`, `mtime`, `readonly=False`, passed | `harness.adapter.meta` |

Run CLI juga menulis laporan JSON ke `_demo/p2c_preview.json` & `_demo/p2c_execute_meta.json`.

---

## 4. Apa yang dibuktikan (penting)

1. **Rantai lengkap berjalan:** Capability → Registry → Contract → Policy → Approval → Execution → REAL external → Verification → Audit.
2. **PREVIEW benar-benar aman:** tanpa efek samping, murni simulasi.
3. **EXECUTE terkendali:** tidak otomatis; wajib semua gate; tanpa approval → diblokir.
4. **Efek eksternal NYATA & terverifikasi:** adapter benar-benar menyentuh file disk (baca konten, hitung hash asli, baca stat) — bukan string "Simulated...".
5. **Audit rekam jejak penuh:** setiap gate + aksi adaptor tercatat.

> **Status capabilitas (Truth Matrix):** dengan harness ini, **Filesystem** naik dari `UNPROVEN` → calon `PROVEN` **melalui real external effect + verification + audit + repeatable run** (memenuhi DoD Truth Matrix). Finalisasi per DoD dilakukan di **P3**.

---

## 5. Batasan (jujur)

- Fase ini **non-destruktif**: hanya `read`/`hash`/`meta`. Aksi tulis (write) **belum** diaktifkan — ada di fase berikut.
- Belum diintegrasikan ke REST API/UI SAM (masih modul mandiri).
- Belum memakai kredensial eksternal (filesystem lokal tidak butuh) — itu untuk P4+.
- `content` read menyertakan BOM dari PowerShell saat fixture dibuat (bukan bug harness).

---

## 6. Artefak

- Kode: `src/sam/execution_runtime/real_harness.py`
- Fixture: `_demo/harness_input.txt`
- Laporan JSON: `_demo/p2c_preview.json`, `_demo/p2c_execute_meta.json`

---

## 7. Berikutnya (P3)

P3 = **Filesystem Real E2E** — menjadikan Filesystem capability **PROVEN resmi**:
- Integrasi `sam_analyzer.py` (analisis nyata Excel/log) sebagai capability `filesystem/analyze` di harness.
- Uji repeatable run (jalankan → hasil sama → audit sama).
- Tandai Filesystem = **PROVEN** di `CAPABILITY_TRUTH_MATRIX.md` menurut DoD.

---

*Artefak P2-C. Real execution terkontrol, tanpa mengubah seluruh platform ke EXECUTE.*
