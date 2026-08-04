# AD-ENG-001 — Activation Readiness Rule

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision

Keputusan Project SAM. Mengunci roadmap & menetapkan aturan aktivasi berbasis kondisi repository.

## Aturan Aktivasi
Sebuah capability boleh jadi Engineering Session HANYA jika memenuhi SEMUA:
- memiliki **Registry**
- memiliki **Bridge**
- dapat di-DI ke jalur resmi
- tidak butuh Runtime baru
- tidak butuh Provider baru
- tidak butuh Architecture Decision baru

Jika SATU syarat belum terpenuhi → **bukan** target Engineering Session, melainkan **Architecture Backlog**.

## Keputusan Aktivasi Terkait
- S07 Artifact · S08 Memory · S09 Policy+Audit · S10 Model (preview)/TDR — dipilih via Activation Readiness, bukan urutan "yang terlihat bagus".
- Intelligence / Agent / Reasoning → Architecture Backlog (activation model belum memberi nilai operasional tanpa perubahan arsitektur, lihat RSR-I01).

## Dasar
Setiap sesi dipilih berdasar Activation Readiness yang dihitung dari repository. Ini membuat roadmap **stabil & prediktif**; capability baru cukup diskor & ditempatkan di tier (lihat EC-025).
