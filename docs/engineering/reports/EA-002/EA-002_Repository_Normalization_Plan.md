# EA-002 — Repository Normalization Plan

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Package:** EA-002 · **Status:** AUTHORIZED · **Bersifat:** 100% READ-ONLY
**Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini adalah **RENCANA normalisasi** — memetakan setiap Gap ID (G1–G10) dari EA-001 menjadi
> langkah implementasi, urutan eksekusi, rollback, risiko, dan authority.
> **BELUM ada perubahan repository** — semua batasan EA-002 tetap: boleh analisis, **dilarang** ubah/rename/delete/move/refactor.

---

## 0. Prinsip EA-002 (sesuai Keputusan Lead Engineer 00:37 WITA)

1. **Pisahkan fakta ↔ rekomendasi.** EA-002 hanya memetakan fakta/evidence/dampak + langkah. Solusi final eksekusi = ruang EA-003+.
2. **Evidence deterministik.** Semua gap di-EA-002 dikualifikasi ulang dgn bukti: hash SHA-256, line count, semantic diff, hitungan eksplisit — BUKAN kata "kemungkinan/berpotensi/kandidat".
3. **Authority** (Architecture / Engineering / Release) sesuai governance.
4. **G10 prioritas.** Untuk G10-01 JANGAN perbaiki di EA-002 — langkah pertama adalah **klasifikasi**: placeholder vs desain vs implementasi vs obsolete.

---

## 1. Kualifikasi Ulang Evidence (deterministik) — Dasar EA-002

Angka di bawah diverifikasi langsung dari repo (bukan asumsi).

| Gap | Evidence Deterministik | Arti |
|---|---|---|
| **G1-02** | Root `ROADMAP.md` (baris 4: *"Sumber kebenaran tunggal"*) vs `docs/engineering/roadmap/ROADMAP SAM 2.x.md` (Version 2.0.0, Active). ATLAS mengarahkan navigasi ke `docs/engineering/roadmap/`. | **2 file mengklaim peran single-source-of-truth** → konflik klaim SoT, bukan sekadar duplikasi |
| **G1-03** | ADR 0–28 → yang ADA: 0,1,2,3,4,5,6,7,11,12,13,15,16,17,18,19,20,21,22,23,24,25,26,27,28 (25 file). **Missing: 8,9,10,14** (4 lompat). | Gap numbering pasti (bukan typo) |
| **G2-01/G7-03** | `development/capability_sdk.md`: hash 1C53…B49, 128 baris, punya section `# Capability SDK`. `implementation/capability-sdk.md`: hash 7371…F6, 257 baris, baris 1 `\# Capability SDK` (escaped), dan **secara eksplisit menyatakan**: *"Canonical documentation ada di `docs/development/capability_sdk.md`", "This document is NOT a Domain Specification"*. | **BUKAN duplikat identik** — pasangan CANONICAL (`development/`) ↔ REFERENCE (`implementation/`), sudah deklaratif konsisten. Yang tersisa: penamaan `_` vs `-` + escaped markdown |
| **G2-03** | 7 pasang file di `modules/openclaw/`: capability-composition (hash beda, 111 vs 99 l), health-checks (214 vs 156), cli (117 vs 119), configuration (185 vs 73), filesystem (190 vs 87), runtime (199 vs 79), workspace (185 vs 71). Tidak ada yang hash-identik. | **Bukan duplikat** — `diagnostics/` = versi penuh, `knowledge/` = distilasi/ringkasan. Perlu definisi peran (bukan penghapusan) |
| **G3-01/G4-01** | `docs/design/` 30 file; konten dict: R0-* R1-* R2-* R3-* (recording proses, C0 E0 G0-* D0 D1 O0, `operations-console.md`, `ADR-006_PREP`). | Campuran design recovery + recording proses; klasifikasi legacy/aktif belum ada |
| **G6-01** | Folder docs kosong (0 file): `backlog`, `decisions`, `glossary`, `research`. Hanya `.gitkeep` (1 file): `incidents`, `knowledge`, `playbooks`. `assets` = 4 file (non-md). | 4 kosong total + 3 .gitkeep |
| **G6-03** | `docs/engineering/reports/` = 0 file (kosong) meski README engineering merujuk laporan EP/OP/L2/L6. | Folder report kosong → klaim README tidak terwakili file |
| **G9-02 / G10-01** | `_placeholders.py`: docstring "99 placeholder", namung **92 tuple check** (`ComplianceCheck(` counted = 14 literal; sisanya lewat loop `_build_all_checks()` → 92 tuple eksplisit L0=12 L1=40 L2=17 L3=15 L4=8). **0 baris `execution_fn =`** di file. `session_runner.py` berisi literal: *"Placeholder — no execution_fn (checkers implemented later)"*. | **92 placeholder tanpa eksekusi**; klaim "99" tidak cocok aktual (inkonsistensi). Ini bukan desain — ini deklarasi kosong |
| **G10-03** | Checker executable nyata (punya method run/execute/check): `behavioral.py`(3), `l0_structural.py`(6), `source_required.py`(2), `system_level.py`(7) di `concrete/`. `baseline_backed_runner.py` + `base_check.py` = wrapper/runner (bukan check isi). | Ada subset checker nyata di luar 92 placeholder → yang 92 itu benar-benar belum diimplementasi |

---

## 2. Klasifikasi Gap → Tindakan (EA-002: fakta + dampak, bukan eksekusi)

### 2.1 Gap yang merupakan **Klaim/Deklarasi** (perlu resolusi authority, bukan refactor)

| Gap | Fakta | Dampak jika dibiarkan | Cek yang diperlukan |
|---|---|---|---|
| **G1-02** | 2 file klaim SoT roadmap; ATLAS sudah tunjuk satu | Navigasi ganda -> pembaca bisa ikut file salah | Verifikasi revisi terakhir kedua file (git log) |
| **G2-01/G7-03** | Canonical/reference sudah deklaratif; sisa penamaan & escape | Minor; risk pembaca bingung `_` vs `-` | Semantic diff header utk pastikan tak ada isi ganda |
| **G7-04** | Term "runtime" dipakai utk blueprint & program | Ambiguitas istilah | Rekonsiliasi dgn GLOSSARY (yg kosong G6-01) |

### 2.2 Gap yang merupakan **Klasifikasi Legacy/Arsip** (perlu tag, bukan hapus)

| Gap | Fakta | Dampak | Klasifikasi yang diperlukan |
|---|---|---|---|
| **G3-01** | `docs/design/` 30 file campuran aktif/recording | Area aktif membesar tak terkendali | Tandai tiap file: active / archived (oleh author asli) |
| **G4-01** | Sama (recording proses) | Sama | Sama |
| **G4-02** | `docs/architecture/` non-SAM_ARCHITECTURE (DTO_Catalog, Dependency_Map, Module_Ownership) | Berpotensi superseded | Verifikasi yg masih dirujuk kode/checker |
| **G5-01** | `docs/engineering/journals/` = catatan selesai | Catatan kerja masuk area "engineering" (seharusnya history) | Klasifikasi journal selesai vs aktif |
| **G5-03** | `docs/history/` subfolder audit/reports/sprint-reports kosong | Struktur history ada tapi kosong | Konsolidasi saat EA-003+ |

### 2.3 Gap yang merupakan **Normalisasi Folder** (perlu keputusan struktur)

| Gap | Fakta | Dampak | Keputusan yang diperlukan |
|---|---|---|---|
| **G1-01** | `loader.py` memetakan `docs/blueprint` DAN `docs/blueprints` (dua key alias) | Dua nama utk konsep sama; checker baseline double-map | Pilih nama folder tunggal |
| **G6-01** | 4 folder kosong (backlog/decisions/glossary/research) + 3 .gitkeep (incidents/knowledge/playbooks) | Folder hantu membuat struktur tak jelas | Putuskan aktif/hapus/isi utk tiap folder |
| **G6-05** | 3 folder engineering-ish: `development/`, `implementation/`, `engineering/` | Tumpang-tindih makna; SDK ada di 2 | Normalisasi penamaan & batas (inti Program A A5) |

### 2.4 Gap yang merupakan **Inkonsistensi Administratif** (verifikasi, bukan kode)

| Gap | Fakta | Dampak | Verifikasi |
|---|---|---|---|
| **G6-03** | `docs/engineering/reports/` kosong tapi README rujuk EP/OP | README tidak terwakili file → link putus | Telusuri rujukan README → status file laporan |
| **G6-04** | `docs/engineering/references/` kosong (25 file EC-* dihapus ca561a4) | Rujukan sisa mungkin ada | cari referensi `references/` di dokumen |
| **G8-01** | `docs/foundation/GLOSSARY.md` ada, folder `glossary/` kosong | Istilah tak terindeks | Rekonsiliasi GLOSSARY vs folder |
| **G8-02** | `docs/documentation/` 8 aturan, banyak dokumen tak patuh | Standar tak ditegakkan | Audit kepatuhan |
| **G8-03** | Istilah "single source of truth" tidak konsisten antar file | Ambiguitas navigasi | Sinkronisasi istilah |
| **G7-01/G7-02** | Naming campur di design/ & architecture/ | Sulit dicari | Tetapkan konvensi (EA-003) |

### 2.5 Gap yang merupakan **Definisi/Implementasi Compliance** (koreksi/klasifikasi, prioritas)

| Gap | Fakta | Dampak | Klasifikasi pertama (bukan perbaikan) |
|---|---|---|---|
| **G9-01** | Tidak ada traceability matrix Mission→capability→program→release yang teruji | Tak ada jaminan kualitas end-to-end | Rancang matriks (desain, bukan build) |
| **G9-02** | `traceability_check.py` ada tapi 92 placeholder tanpa eksekusi | Traceability tidak jalan | Masuk klasifikasi G10 |
| **G9-03** | Appendix A readiness matrix ada, tak ada checker validasi | Klaim readiness tak teruji | Hubungkan matriks ↔ evidence |
| **G10-01** | **92 placeholder tanpa execution_fn** (0 attach); klaim "99" vs aktual 92 | Complikasi serius: compliance deklaratif, tak dieksekusi | **Klasifikasi (prioritas #1): placeholder vs desain vs implementasi vs obsolete** |
| **G10-02** | `development/`, `implementation/`, `documentation/`, `user/` TIDAK dipetakan `loader.py` | Status compliance folder tsb undefined | Putuskan lingkup compliance |
| **G10-04** | Tidak ada artefak report keberhasilan compliance di `docs/reports/` | Bukti kepatuhan tak terlihat | Standardisasi output (EA-003+) |

---

## 3. Urutan Eksekusi Rencana Normalisasi (Fase EA-002 → EA-003+, read-only)

Urutan ini adalah **rencana kerja** — TIDAK dieksekusi sekarang (butuh otorisasi per fase).

| Fase | Aktivitas | Gap di-resolve | Authority | Risiko | Rollback |
|---|---|---|---|---|---|
| **P0** | Sinkronisasi catatan EA-002 dengan status aktual; pastikan baseline read-only | — | Engineering | Rendah | N/A (tanpa perubahan) |
| **P1 (prioritas)** | **Klasifikasi G10-01**: petakan 92 placeholder jadi `placeholder/desain/implementasi/obsolete` berdasar spesifikasi P1-001 & concrete yang ada | G10-01, G9-02 | Engineering + Compliance | Sedang: salah klasifikasi → perbaikan keliru | Tabel klasifikasi dipertahankan sebelum tindakan |
| **P2** | Tabel traceability Mission→Capability→Program→Release (desain) | G9-01, G9-03 | Architecture | Sedang | Matriks sebagai dokumen (rollback = tak apply) |
| **P3** | Resolusi klaim SoT: ROADMAP root vs SAM 2.x — tetapkan 1 sumber | G1-02, G8-03 | Architecture | Sedang: keputusan strategis | Catat keputusan ADR sebelum ubah |
| **P4** | Normalisasi nama folder: blueprint vs blueprints; development/implementation/engineering | G1-01, G6-05, G7-01/02/03 | Engineering | Tinggi: banyak file terlibat | Git history + plan migrasi bertahap |
| **P5** | Klasifikasi legacy/arsip: design/30, architecture non-inti, journals, history/ | G3-01, G4-01/02, G5-01/03 | Engineering + Architecture | Sedang | Arsip = move ke history (recoverable) |
| **P6** | Resolusi folder kosong & .gitkeep | G6-01, G6-02 | Engineering | Rendah | Recycle Bin sebelum hapus |
| **P7** | Rekonsiliasi administrasi: reports/ kosong, references/, glossary | G6-03/04, G8-01/02 | Engineering | Rendah | Audit dulu, bukan hapus |
| **P8** | Definisi lingkup compliance utk folder tak terpetakan | G10-02 | Architecture | Sedang | ADR lingkup |
| **P9** | Standar output compliance→evidence→report | G10-04 | Engineering | Rendah | Template ditetapkan |

> **Catatan:** Fase P1–P9 hanyalah **rencana**. Eksekusi tiap fase butuh otorisasi terpisah (EA-003+). EA-002 tidak menjalankan satu pun.

---

## 4. Daftar Lengkap Gap → Langkah (tabel konsolidasi)

| Gap ID | Severity EA-001 | Langkah (EA-002: rencana) | Urutan | Rollback | Risiko | Authority |
|---|---|---|---|---|---|---|
| G10-01 | Critical | Klasifikasi 92 placeholder (placeholder/desain/implementasi/obsolete); reconcile klaim 99 vs 92 | P1 | Tabel klasifikasi | Sedang | Engineering+Compliance |
| G2-01 | High | Selesaikan penamaan canon/reference (development/ vs implementation/); fix `\#` escape; verifikasi semantic tak ada isi ganda | P4 | Git history | Sedang | Engineering |
| G6-05 | High | Normalisasi batas development/implementation/engineering | P4 | Migrasi bertahap | Tinggi | Engineering |
| G3-01/G4-01 | High | Klasifikasi 30 file design/ → active/archived | P5 | Arsip=move | Sedang | Engineering |
| G9-01 | High | Rancang matriks traceability | P2 | Dokumen | Sedang | Architecture |
| G9-02 | High | Masuk klasifikasi G10 (traceability tak jalan) | P1 | Tabel | Sedang | Engineering |
| G1-02 | Medium | Resolusi klaim SoT roadmap | P3 | ADR keputusan | Sedang | Architecture |
| G1-03 | Medium | Verifikasi ADR-008/009/010/014 (dihapus/merged?) | P5 | Catatan | Sedang | Architecture |
| G2-03 | Medium | Definisikan peran diagnostics/ vs knowledge/ (distilasi, bukan hapus) | P5 | Audit | Sedang | Engineering |
| G10-02 | Medium | Putuskan lingkup compliance folder tak terpetakan | P8 | ADR | Sedang | Architecture |
| G6-01/02 | Low/Info | Resolusi 4 folder kosong + 3 .gitkeep | P6 | RecycleBin | Rendah | Engineering |
| G6-03/04 | Medium/Info | Rekonsiliasi reports/ & references/ kosong | P7 | Audit | Rendah | Engineering |
| G8-01 | Medium | Rekonsiliasi GLOSSARY vs folder glossary/ kosong | P7 | Audit | Rendah | Architecture |
| G7-01/02 | Medium/Low | Konvensi nama design/ & architecture/ | P4 | Template | Rendah | Engineering |

---

## 5. Exit Criteria EA-002

| Kriteria | Status |
|---|---|
| Seluruh Gap ID (G1–G10) terpetakan ke langkah + urutan + rollback + risiko + authority | ✅ (Tabel §4) |
| Evidence deterministik (bukan "kemungkinan") | ✅ (hash/line count/hitungan eksplisit — §1) |
| Fakta & rekomendasi dipisahkan | ✅ (solusi final di-tag sbg fase EA-003+, tak dieksekusi) |
| G10 diklasifikasi (placeholder vs desain vs implementasi vs obsolete) sbg RENCANA, bukan perbaikan | ✅ (P1) |
| Tidak ada perubahan repository / commit / branch | ✅ (read-only dipertahankan) |
| Mapping Report tidak diulang | ✅ (dirujuk, tidak ditulis ulang) |

---

## 6. Verifikasi Read-only (sama dgn EA-001)

- Git status usai EA-002 harus identik dengan sebelum (hanya `M ROADMAP.md` sisa lama, bukan dari EA-002).
- Tidak ada file baru/ubah/hapus di repo.
- Semua artefak EA-002 adalah artefak perencanaan (dokumen), bukan perubahan repo.

---

## EA-002-ANNEX-A — Normalization Execution Queue

> **Artefak wajib (deliverable EA-002, per Review Lead Engineer 00:41 WITA).**
> Menjadi antrean eksekusi resmi Program A — acuan EA-003 hingga penutupan Program A.
> Satu baris per Gap ID; **tidak ada gap yang hilang**; dependency antar-gap **eksplisit**;
> target EA implementasi **jelas**.

### A. Konvensi Kolom
- **Priority**: P0 (blocking) → P1… → P9.
- **Authority**: Architecture / Engineering / Release / Compliance (sesuai governance).
- **Depends On**: gap yang HARUS selesai/terpetakan dulu sebelum gap ini (kosong = independen).
- **Target EA**: paket eksekusi yang akan menjalankan langkah ini (EA-003 dst.).

### B. Execution Queue (36 Gap ID — lengkap)

| Priority | Gap ID | Action | Authority | Depends On | Target EA |
|---|---|---|---|---|---|
| **P0** | **G10-01** | Klasifikasi 92 placeholder (placeholder/desain/implementasi/obsolete) + reconcile klaim 99 vs 92 | Engineering + Compliance | — | EA-003 |
| **P0** | **G10-03** | Audit checker concrete executable (behavioral/l0_structural/source_required/system_level) — pisahkan nyata vs stub; hasil masuk klasifikasi G10-01 | Engineering | G10-01 | EA-003 |
| **P0** | **G9-02** | Traceability check tak jalan (92 placeholder) — ikut klasifikasi G10-01 | Engineering | G10-01 | EA-003 |
| P1 | **G1-02** | Resolusi Source-of-Truth claim: ROADMAP.md root vs ROADMAP SAM 2.x — tetapkan 1 sumber | Architecture | — | EA-003 |
| P1 | **G8-03** | Sinkronisasi istilah "single source of truth" di seluruh dokumen navigasi | Architecture | G1-02 | EA-003 |
| P1 | **G9-01** | Rancang matriks traceability Mission→Capability→Program→Release | Architecture | — | EA-003 |
| P1 | **G9-03** | Hubungkan Appendix A readiness matrix sbg evidence checker | Engineering | G9-01 | EA-003 |
| P2 | **G1-01** | Normalisasi alias folder: blueprint vs blueprints (loader.py double-key) | Engineering | — | EA-004 |
| P2 | **G6-05** | Normalisasi batas development/implementation/engineering | Engineering | G2-01 | EA-004 |
| P2 | **G2-01** | Tuntaskan penamaan canonical/reference SDK (development/ vs implementation/) + fix \# escape | Engineering | — | EA-004 |
| P2 | **G7-01** | Konvensi nama dokumen di docs/design | Engineering | G6-05 | EA-004 |
| P2 | **G7-02** | Konvensi nama dokumen di docs/architecture | Architecture | G6-05 | EA-004 |
| P2 | **G7-03** | Sinkronkan penamaan capability_sdk vs capability-sdk (sama G2-01) | Engineering | G2-01 | EA-004 |
| P2 | **G7-04** | Definisikan istilah "runtime" (GLOSSARY) | Architecture | G8-01 | EA-004 |
| P3 | **G3-01** | Klasifikasi docs/design 30 file → active/archived | Engineering | G7-01, G6-05 | EA-005 |
| P3 | **G4-01** | Klasifikasi legacy design recovery | Engineering | G3-01 | EA-005 |
| P3 | **G4-02** | Klasifikasi docs/architecture non-inti (DTO_Catalog, Dependency_Map, Module_Ownership) | Architecture | G6-05 | EA-005 |
| P3 | **G4-03** | Klasifikasi release notes v30/version-history (arsip) | Release | G8-03 | EA-005 |
| P3 | **G3-03** | Verifikasi dokumen arsitektur utk yang superseded | Architecture | G4-02 | EA-005 |
| P3 | **G5-01** | Klasifikasi journals selesai vs aktif | Engineering | G3-01 | EA-005 |
| P3 | **G5-02** | Pindah recording proses design ke history | Engineering | G3-01 | EA-005 |
| P3 | **G5-03** | Konsolidasi docs/history/ (subfolder audit/reports/sprint-reports kosong) | Engineering | G5-01, G5-02 | EA-005 |
| P3 | **G1-03** | Verifikasi ADR-008/009/010/014 (dihapus/merged? perlu catatan) | Architecture | G10-01 | EA-005 |
| P4 | **G2-03** | Definisikan peran diagnostics/ vs knowledge/ di modules/openclaw (purpose variants, bukan hapus) | Engineering | — | EA-006 |
| P4 | **G6-01** | Resolusi 4 folder docs kosong (backlog/decisions/glossary/research) | Engineering | — | EA-006 |
| P4 | **G6-02** | Resolusi 3 folder .gitkeep (incidents/knowledge/playbooks) | Engineering | G6-01 | EA-006 |
| P4 | **G6-03** | Rekonsiliasi docs/engineering/reports/ kosong vs klaim README | Engineering | G3-01 | EA-006 |
| P4 | **G6-04** | Rekonsiliasi docs/engineering/references/ kosong (EC-* dihapus ca561a4) | Engineering | G6-03 | EA-006 |
| P4 | **G6-06** | Tegaskan struktur target docs/ di REPOSITORY_CONVENTION | Architecture | G6-05 | EA-006 |
| P5 | **G8-01** | Rekonsiliasi GLOSSARY.md (foundation) vs folder glossary/ kosong | Architecture | G6-01 | EA-007 |
| P5 | **G8-02** | Audit kepatuhan dokumen thd DOCUMENTATION_STANDARD | Engineering | G7-01, G7-02 | EA-007 |
| P6 | **G10-02** | Putuskan lingkup compliance utk folder tak terpetakan loader (development/implementation/documentation/user) | Architecture | G10-01 | EA-008 |
| P6 | **G10-04** | Standardisasi output compliance→evidence→report | Engineering | G10-01, G10-02 | EA-008 |
| P7 | **G2-02** | Audit duplikasi struktur runtime (10x builder/catalog/... — overlap capability) | Engineering | G10-03 | EA-009 |
| P7 | **G2-04** | Reklasifikasi docs/core (EXECUTION_MODEL/THINKING_PROTOCOL) dari foundation → runtime/engineering | Architecture | G10-02 | EA-009 |
| P8 | **G3-02** | Tegaskan status docs/blueprint/STRUCTURE.md (draft/active) | Architecture | G1-01, G2-04 | EA-010 |

> **Jumlah baris: 36 Gap ID — lengkap, tidak ada yang hilang atau ganda** (G1:3, G2:4, G3:3, G4:3, G5:3, G6:6, G7:4, G8:3, G9:3, G10:4 = 36).

### C. Catatan Dependency & Urutan
- **G10-01/G10-03/G9-02** = klaster P0 (klasifikasi compliance) — tidak tergantung ke gap lain, jadi pintu masuk pertama.
- **Rantai normalisasi folder**: G2-01 → G6-05 → G7-xx; kemudian G3-01 → G4-xx → G5-xx (legacy).
- **Rantai compliance**: G10-01 → G10-02 → G10-04 (standar output paling akhir).
- **G2-04 & G3-02** paling akhir (P7–P8) karena menunggu keputusan struktur folder (G1-01) & lingkup compliance (G10-02).

### D. Peta Target EA
| Target EA | Gap Yang Dieksekusi |
|---|---|
| EA-003 | G10-01, G10-03, G9-02, G1-02, G8-03, G9-01, G9-03 |
| EA-004 | G1-01, G6-05, G2-01, G7-01, G7-02, G7-03, G7-04 |
| EA-005 | G3-01, G4-01, G4-02, G4-03, G3-03, G5-01, G5-02, G5-03, G1-03 |
| EA-006 | G2-03, G6-01, G6-02, G6-03, G6-04, G6-06 |
| EA-007 | G8-01, G8-02 |
| EA-008 | G10-02, G10-04 |
| EA-009 | G2-02, G2-04 |
| EA-010 | G3-02 |

---

*— Akhir Repository Normalization Plan (EA-002) + ANNEX-A Execution Queue —*
