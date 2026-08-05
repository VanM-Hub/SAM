# L6 — Engineering Implementation Constraint (kendala implementasi)

**Tanggal:** 2026-08-06

## Status
L6 (Preview → Audit terminal) **TIDAK di-commit**. Diblok oleh kendala desain, bukan karena malas menyelesaikan — sesuai arahan: jangan pilih solusi yang mengubah desain hanya agar DoD tampak selesai.

## Verifikasi (berbasis kode)
Pertanyaan Lead Engineer: "Bisakah registry hasil register() menjadi registry yang digunakan AuditPreviewConsumer tanpa mengubah model immutable?"

Jawaban: **TIDAK, dengan wiring yang ada sekarang.**

Fakta kode:
1. `AuditPreviewConsumer.__init__(registry=...)` menetapkan `self._registry` sekali; **tidak ada setter/accessor** untuk menggantinya (0 hit `set_registry`/`replace`).
2. `ExecutionPreviewProducer` menyimpan hasil `register()` di internal `self._audit_registry`, **tanpa accessor** ke luar.
3. `AuditRegistry` **immutable** (`@dataclass(frozen=True)`, `register()` → instance baru, tidak memutasi self).

Akibat: record yang dihasilkan helper tersimpan di instance hasil register (internal producer), **tidak terlihat oleh `audit_consumer`** yang memakai registry asli.

Untuk membuat record terlihat perlu salah satu:
- (a) merekonstruksi `audit_consumer` per preview dgn registry hasil → mengubah cara dependency di-wire / ownership; ATAU
- (b) share registry mutable antar modul → mengubah lifecycle/ownership (melanggar immutable).

Keduanya = perubahan desain → STOP per arahan.

## Kesimpulan
- Rekomendasi implementasi awal (helper `record_execution_audit` + wire di producer) **sudah ditulis sebagian** (modul audit_recording.py + wiring di execution_preview_wiring.py + test L6) tapi **belum di-commit**.
- Karena tidak dapat dicapai tanpa ubah desain, dilaporkan sebagai **Engineering Implementation Constraint** ke Lead Engineer untuk evaluasi (keputusan arsitektur/desain).
- Digunakan pola: tidak memaksakan solusi; kendala dilaporkan, bukan ditutup-tutupi.

## Handoff
Bila Lead Engineer memutuskan perlu record terlihat dari `audit_consumer`, keputusan menyentuh desain (cara wire/ownership registry) → bukan kewenangan engineering murni.
