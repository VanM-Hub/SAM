# EA-001 — Repository Gap Analysis

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Package:** EA-001 · **Status:** AUTHORIZED · **Bersifat:** READ-ONLY
**Tanggal:** 2026-08-08 · **Oleh:** ZARA

> Semua gap di bawah **berbasis evidence** dari pemeriksaan langsung repo. Tidak ada tindakan korektif — menunggu otorisasi EA-002.

---

## G1 — Duplicate Canonical Documents

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G1-01** | `docs/blueprint/STRUCTURE.md` vs `docs/blueprint(s)/` | `loader.py` memetakan **dua key:** `"docs/blueprint"` DAN `"docs/blueprints"` (dua path berbeda utk konsep sama) | Low | Tentukan satu nama folder kanonik; jangan dua alias | Architecture |
| **G1-02** | Root: `ROADMAP.md`, `SPRINT_TRACKER.md` vs kitab `docs/engineering/roadmap/ROADMAP SAM 2.x.md` | Root punya `ROADMAP.md` (M, ditahan) yang perannya **tumpang-tindih** dengan roadmap SAM 2.x baru | Medium | Tegaskan satu-satunya sumber roadmap; atau arsipkan ROADMAP.md root ke `docs/history/` | Architecture |
| **G1-03** | `docs/adr/` | ADR-008, 009, 010, 014 **TIDAK ada** (lompat) — 25 ADR ada, nomor tidak kontigu | Medium | Verifikasi docahapus/merged; dokumentasikan; jangan biarkan gap numbering tanpa catatan | Architecture |

---

## G2 — Duplicate Engineering Documents

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G2-01** | `docs/development/capability_sdk.md` vs `docs/implementation/capability-sdk.md` | Dua file SDK **nama berbeda, kemungkinan isi sama** (underscore vs hyphen; folder berbeda) | High | Bandingkan isi; gabung ke satu lokasi kanonik, hapus duplikat | Engineering |
| **G2-02** | `src/sam/` runtime folder (artifact_runtime, audit_runtime, cognitive_runtime, knowledge_runtime, memory, policy_runtime, workflow_runtime, model_runtime, intelligence_runtime, skills) | Tiap runtime punya pola folder berulang `builder/catalog/certification/dashboard/foundation/integration/model/monitoring/runtime` → **duplikasi struktur X 10 runtime** | Info | Bukan gap kritis (pola iterasi), tapi berpotensi overlap; mapping kepemilikan capability perlu tegas | Engineering |
| **G2-03** | `modules/openclaw/` | Duplikasi file internal: `capabilities/runtime/capability-composition.md` vs `capabilities/capability-composition.md`; `health-checks.md`, `cli.md`, `configuration.md`, `filesystem.md`, `runtime.md`, `workspace.md` di `diagnostics/` DAN `knowledge/` | Medium | Vendor/copy OpenClaw ter-track berisiko duplikat; audit apakah benar-benar dibutuhkan di repo utama | Engineering |
| **G2-04** | `docs/core/EXECUTION_MODEL.md` + `THINKING_PROTOCOL.md` vs `docs/runtime/` + `docs/design/` | `docs/core` dipetakan `loader.py` sebagai `foundation`, tapi isinya model eksekusi (bukan identity) → **kategori keliru** | Low | Reklasifikasi `docs/core/` ke folder yang tepat (engineering/runtime) | Architecture |

---

## G3 — Orphan Documents

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G3-01** | `docs/design/` (30 file) | Sebagian besar adalah **recording proses** (R0-R3, G0-G2, C0, D0, D1, O0, E0, E1) — banyak bersifat historical design recovery, bukan acuan aktif | High | Klasifikasi: mana yang masih dirujuk vs arsip → pindahkan yang usang ke `docs/history/` | Engineering |
| **G3-02** | `docs/blueprint/STRUCTURE.md` | Satu-satunya file blueprint; berisi **kritik struktur** (menandai development/ "tumpang tindih") — statusnya draft/konsep, bukan keputusan final | Low | Tegaskan status (draft/active); update atau arsipkan | Architecture |
| **G3-03** | `docs/architecture/ARCHITECTURE_AUDIT_REPORT.md`, `runtime-kernel-specification-v1.md` | Dokumen yang besarannya report/spesifikasi versi, berpotensi out-of-date vs struktur baru | Medium | Verifikasi relevansi; pindahkan yang superseded | Architecture |

---

## G4 — Legacy Documents (belum diklasifikasi)

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G4-01** | `docs/design/*.md` | 30 file design recovery = **kandidat legacy** (sebagian besar hasil audit sesi G/D/R yang sudah selesai) | High | Jalankan **Legacy Classification** (EA berikutnya): tandai mana yang arsip | Engineering |
| **G4-02** | `docs/architecture/*.md` (non-SAM_ARCHITECTURE) | DTO_Catalog, Dependency_Map, Module_Ownership dll. = artefak yang mungkin sudah digantikan struktur baru | Medium | Klasifikasi legacy vs aktif | Architecture |
| **G4-03** | `docs/releases/release_notes/v30.md`, `docs/releases/version-history.md` (disebut) | Release notes era v30 (sprint lama) tersisa di struktur | Info | Arsipkan ke `docs/history/` | Release |

---

## G5 — Historical Documents di Area Aktif

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G5-01** | `docs/engineering/journals/` | 3 journal (2026-08-06/07) = catatan kerja yang sudah selesai; berstatus aktif padahal historis | Medium | Pindah journal selesai ke `docs/history/` atau arsip eksternal | Engineering |
| **G5-02** | `docs/design/` (lihat G3-01/G4-01) | Recording proses historis masih di area aktif "design" | High | Pindah ke history setelah klasifikasi | Engineering |
| **G5-03** | `docs/history/` subfolder `audit/`, `reports/`, `sprint-reports/` | Folder **kosong** — struktur history belum terisi meski banyak dokumen historis tersebar di area aktif | Medium | Konsolidasi dokumen historis ke sini | Engineering |

---

## G6 — Repository Inconsistency

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G6-01** | `docs/` — 8 folder kosong | `assets`, `backlog`, `decisions`, `glossary`, `incidents`, `knowledge`, `playbooks`, `research` = **0 file** | Low | Hapus/tandai; atau isi — jangan biarkan folder hantu | Engineering |
| **G6-02** | `docs/` — 3 folder .gitkeep saja | `incidents`, `knowledge`, `playbooks` hanya berisi `.gitkeep` | Info | Putuskan: aktif atau hapus | Engineering |
| **G6-03** | `docs/engineering/reports/` KOSONG | Pergeseran: report sesi disebutkan di README tapi folder kosong (laporan EP/OP/L2/L6 "diarsipkan ke backup eksternal") | Medium | Verifikasi apakah laporan hilang/benar diarsip; konsistensi klaim README | Engineering |
| **G6-04** | `docs/engineering/references/` KOSONG | 25 file EC-* dihapus (commit ca561a4) tapi README engineering & AD-ENG masih sempat merujuk (sudah diperbaiki) | Info | Sudah dibereskan; pastikan tidak ada rujukan sisa | Engineering |
| **G6-05** | Overlap `docs/development/` vs `docs/implementation/` vs `docs/engineering/` | 3 folder "engineering-ish" dengan makna tumpang-tindih (SDK di development & implementation; strategi di engineering) | High | Normalisasi penamaan & batas (core dari Program A A5) | Engineering |
| **G6-06** | `docs/` root hanya punya 2 file langsung (HISTORY_POLICY, SPECIFICATION_FREEZE) | Struktur dokumentasi tidak konsisten dengan klasifikasi canonical/engineering | Info | Tegaskan struktur target di REPOSITORY_CONVENTION | Architecture |

---

## G7 — Naming Inconsistency

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G7-01** | `docs/design/` | Campuran gaya: `D0-001_`, `A0-001_`, `R1-001_`, `operations-console.md`, `ADR-006_PREP_...` — ada yang pakai prefix kode, ada yang tidak | Medium | Normalisasi naming convention di design folder | Engineering |
| **G7-02** | `docs/architecture/` | Campuran `UPPER_SNAKE`, `PascalCase`, `kebab-case`: `ARCHITECTURAL_DECISIONS.md`, `Architecture_Rulebook.md`, `DTO_Catalog.md`, `Pipeline_Specification.md`, `runtime-kernel-specification-v1.md` | Low | Tetapkan satu konvensi nama | Architecture |
| **G7-03** | `capability_sdk.md` vs `capability-sdk.md` | File SDK sama konsep, penamaan beda di 2 folder (G2-01) | High | Sama dgn G2-01 | Engineering |
| **G7-04** | `docs/runtime/` vs `docs/engineering/roadmap/` | Istilah "runtime" dipakai utk blueprint (docs/runtime) DAN program (Program B Runtime Realization) | Info | Definisikan kamus istilah (lihat GLOSSARY yg kosong) | Architecture |

---

## G8 — Documentation Inconsistency

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G8-01** | `docs/glossary/` KOSONG | Referensi GLOSSARY.md di foundation, tapi folder glossary kosong → istilah tidak ter-indeks | Medium | Isi glossary atau hapus folder | Architecture |
| **G8-02** | `docs/documentation/` (8 file) | Aturan pengelolaan dokumen ada, tapi banyak dokumen tak patuh (G6, G7) | Medium | Tegakkan DOCUMENTATION_STANDARD; audit kepatuhan | Engineering |
| **G8-03** | Aliran Foundation→Roadmap →… | ROADMAP.md root vs ROADMAP SAM 2.x — kalimat "Source of Truth" tidak konsisten (ATLAS sudah dikoreksi; file lain menunggu) | Medium | Sinkronisasi istilah di seluruh dokumen navigasi | Architecture |

---

## G9 — Traceability Gap

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G9-01** | Mission→Architecture→Engineering→Release | Tidak ada **matriks traceability eksplisit** dari Mission/Constitution → capability → program → release yang teruji otomatis | High | Bangun traceability matrix (Mission→Capability→Program→Release) sebagai compliance check | Architecture |
| **G9-02** | Compliance traceability_check.py | Ada checker `traceability_check.py` tapi **99 placeholder check TANPA execution_fn** → traceability tidak benar-benar dieksekusi | High | Implementasi execution_fn / verifikasi hasil checker nyata | Engineering |
| **G9-03** | `docs/engineering/strategy/*` → Program → Appendix | Appendix A (Capability Readiness Matrix) ada tapi **tidak ada artefak checker** yang memvalidasi klaim readiness terhadap kode | Medium | Hubungkan readiness matrix dgn evidence checker | Engineering |

---

## G10 — Compliance Gap

| Gap ID | Lokasi | Evidence | Severity | Recommendation | Authority |
|---|---|---|---|---|---|
| **G10-01** | `src/sam/compliance/checks/_placeholders.py` | **99 placeholder compliance check** — "NO execution_fn, framework structure only" | **Critical** | Implementasi checker nyata atau hapus deklarasi palsu; compliance TIDAK boleh berupa placeholder | Engineering |
| **G10-02** | `docs/development/`, `docs/implementation/`, `docs/documentation/`, `docs/user/` | Folder-folder ini **TIDAK dipetakan `loader.py`** (di luar baseline) → status compliance tidak jelas | Medium | Putuskan: apakah area ini dalam lingkup compliance; jika ya, petakan | Architecture |
| **G10-03** | `src/sam/compliance/checks/concrete/` | Ada `l0_structural.py`, `system_level.py`, `behavioral.py` — perlu verifikasi jumlah yang punya execution nyata vs stub | High | Audit checker executable nyata (bukan placeholder) | Engineering |
| **G10-04** | Evidence/Report compliance | Tidak ditemukan **artefak report keberhasilan compliance** yang jelas di `docs/reports/` (hanya 2 laporan kondisi, bukan compliance cert) | Medium | Standardisasi output checker → evidence → report | Engineering |

---

## Ringkasan Kuantitatif EA-001 (jawaban "berapa?")

| Pertanyaan | Jawaban |
|---|---|
| Canonical document? | **~53** (foundation 9 + spec 7 + ADR 25 + compliance 8 + architecture inti 4) |
| Duplicate (G1+G2)? | ≥ **4** hotspot duplikasi (blueprint alias, ROADMAP root, SDK x2, vendor OpenClaw) |
| Orphan (G3)? | ≥ **3** area (design 30 file, blueprint, architecture audit) |
| Legacy (G4)? | ≥ **2** area besar (design 30 file, architecture non-inti) |
| Historical (G5)? | ≥ **2** area (journals, design) + history subfolder kosong |
| Engineering report? | `docs/engineering/reports/` = **0** (kosong) |
| Release artifact? | **4** aktif (compatibility, manifest, checklist, upgrade) |
| Compliance artifact (docs)? | **8** (P1-001…008) |
| Compliance checker (kode)? | framework + **99 placeholder** |
| Folder aktif (docs)? | **22** |
| Folder obsolete/kosong (docs)? | **8 kosong + 3 .gitkeep** |

---

## Exit Criteria EA-001 — Status

| Kriteria | Status |
|---|---|
| Repository dipetakan 100% | ✅ Lengkap (Mapping Report) |
| Seluruh gap terdokumentasi dgn evidence | ✅ 10 kategori, 25+ gap ID |
| Tidak ada perubahan pada repository | ✅ (hanya `ROADMAP.md` M sisa sebelumnya, bukan dari EA-001) |
| Working tree bersih | ✅ relatif thd EA-001 |
| Tidak ada commit/branch | ✅ EA-001 tidak membuat commit apa pun |
| Tidak ada perubahan baseline Architecture | ✅ |
| Siap masuk EA-002 Normalization Plan | ✅ Siap menunggu otorisasi |

---

*— Akhir Repository Gap Analysis —*
