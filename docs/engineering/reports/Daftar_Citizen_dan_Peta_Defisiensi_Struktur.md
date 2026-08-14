# Peta Defisiensi Struktur — SUPERSEDED

> ⚠️ **Dokumen ini DIGANTIKAN** oleh `Semantic_Repository_Map.md` (2026-08-14).

Pendekatan awal yang memetakan folder `src\sam\*` ke Citizen/Ward/duplikat **berdasarkan kecocokan nama folder dengan CitizenKind terbukti keliru** (koreksi Aster).

Kesalahan yang diperbaiki:
- `runtime_kernel`/`runtime_root`/`runtime_service` **bukan duplikat** — semuanya di-import aktif (226/26/165 referensi) dan berperan berbeda.
- `memory` vs `knowledge_runtime` **bukan duplikat identik** — dua domain berbeda (Memory Runtime vs Knowledge Runtime, entitas berbeda), keduanya canonical dan dipakai.

**Rujukan aktif:** `docs/engineering/reports/Semantic_Repository_Map.md` (klasifikasi semantic ownership, 13 kategori, UNKNOWN diperbolehkan).
