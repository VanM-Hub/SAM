# AD-S04 — Presentation menerima RuntimeService via DI (Opsi A)

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision (Session 04)

## Keputusan
- Presentation (PresentationLayer) menerima **RuntimeService via Dependency Injection**.
- **Desktop** = Presentation pertama yang memakai activation path resmi.

```
Desktop Entry → Presentation → RuntimeService (WebRuntimeService)
```

## Aturan
- Presentation TIDAK membuat RuntimeService sendiri (harus di-DI dari entry).
- Presentation TIDAK boleh mengetahui RuntimeCoordinator / ExecutionRuntime.
- HANYA membaca kontrak RuntimeService: lifecycle, readiness, status, descriptor, metadata, contract.

## Alasan TIDAK buat PresentationRuntimeBinding
- Baru satu Presentation (Desktop) yang dimigrasikan.
- Belum ada bukti Desktop/Web/Mobile/CLI butuh binding abstraction yang sama.
- Abstraction lahir dari kebutuhan nyata, bukan prediksi.
- Tambah layer tanpa responsibility unik = melanggar prinsip SAM.
