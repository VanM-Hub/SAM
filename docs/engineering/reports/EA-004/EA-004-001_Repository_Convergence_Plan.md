# EA-004-001 — Repository Convergence Plan

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Repository Convergence Plan · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini **mendefinisikan TARGET REPOSITORY STATE akhir Program A** — BUKAN langkah implementasi.
> Tidak ada usulan perubahan repository: tidak memindahkan folder, tidak rename, tidak delete,
> tidak menentukan arsip final, tidak menentukan Source of Truth. Seluruhnya read-only.

---

## 1. Current Repository Baseline

Ringkasan kondisi saat ini (merujuk EA-001 s.d. EA-003; detail di dokumen masing-masing).

> ⚠️ **Sifat angka berikut: SNAPSHOT, bukan invariant.** Angka ini dokumen kondisi awal Program A.
> Jumlah artefak BOLEH berubah pada EA berikutnya selama klasifikasi tetap benar. Jangan perlakukan
> (mis.) "canonical harus selalu 88" sebagai aturan — ia hanyalah rekaman titik awal.

### 1.1 Ringkasan Area (file git-tracked, verifikasi ulang 2026-08-08)

| Area | Jumlah file | Karakter |
|---|---|---|
| **Canonical area (`docs/foundation` + `specifications` + `adr` + `compliance` + `architecture` + `runtime`)** | 9 + 7 + 25 + 8 + 24 + 15 = **88** | Dokumen normatif: MISSION/VISION/CHARTER/PRINCIPLES/GOVERNANCE/CONSTITUTION/GLOSSARY/PHILOSOPHY/CITIZEN_SPECIFICATION, Spec fungsional, ADR-000..028, baseline P1-001..008, arsitektur, blueprint runtime |
| **Engineering area (`docs/engineering` + `design` + `development` + `implementation` + `documentation`)** | 29 + 30 + 6 + 4 + 8 = **77** | Decisions, journals, roadmap(11), strategy(3), templates(2), design recovery R/D/C/E/G/O, panduan dev, aturan dokumentasi |
| **Legacy area (`docs/history`)** | 6 | `docs/history/legacy/` (6 dokumen era Framework+Module) + subfolder kosong audit/, reports/, sprint-reports/ |
| **History area (partial)** | `docs/releases/history/` = 0, `docs/engineering/references/` = 0, `docs/engineering/reports/` = 0 | Kosong (arsip/report lama dihapus/berpindah) |
| **Release area (`docs/releases`)** | 4 | compatibility, manifest, release_checklist, upgrade |
| **Compliance area (`src/sam/compliance`)** | 255 file | 99 checker executable (Builder) + framework + baseline loader + runtime P1-008 |
| **Source (`src/sam`)** | 2.571 file .py | Area runtime/domain (activation, agent, api, compliance, execution, guardian, operations, providers, runtime_service, dll.) |
| **Testing (`tests`)** | 550 file | 62+ folder sprint + capability (api, compliance, desktop, execution_runtime, presentation, runtime_service, unit) |
| **Vendor/eksternal (`modules/openclaw`)** | 80 file | copy OpenClaw (git-tracked) |
| **Scripts (`scripts`)** | ~13 | Tooling + validasi |
| **Data (`data`)** | 4 | Migrations/SQL |

### 1.2 Takeaway baseline (kunci EA-003)

- **99 compliance checker = IMPLEMENTED & executable** via `Builder`; `_placeholders.py` = artefak deklaratif/obsolete di luar jalur produksi. (Koreksi EA-003 menggantikan EA-001/002.)
- **Ditemukan duplicate canonical** (EA-002): `development/capability_sdk.md` vs `implementation/capability-sdk.md` (G2-01); 7 pasang OpenClaw docs (G2-03).
- **Konflik Source of Truth roadmap** (G1-02): `ROADMAP.md` (klaim "satu-satunya") vs `ROADMAP SAM 2.x.md` (ATLAS memihak). Keputusan = Architecture Authority, BUKAN EA-004.
- **Traceability end-to-end belum ada** matriks Mission→Capability→Program→Release→Evidence→Acceptance (G9-01/03).

---

## 2. Target Repository State

Struktur repository **setelah Program A selesai** (final state/has jadi). Ini mendefinisikan **bentuk akhir**,
bukan lokasi pemindahan file.

### 2.1 Area yang harus ada (final state)

| Area | Fungsi normatif | Wajib memiliki |
|---|---|---|
| **Canonical Area** | Dokumen yang menjadi acuan kebenaran (antar-domain) | 1 SoT per domain; bebas duplicate |
| **Foundation Area** | Identitas & aturan dasar SAM (mission, vision, charter, principles, governance, constitution, glossary) | Konsisten dgn canonical; glossary terindeks |
| **Architecture Area** | Keputusan & struktur arsitektur (ADR + architecture) | ADR lengkap (tanpa gap nomor); rulebook arsitektur |
| **Engineering Area** | Rencana kerja, decisions, design recovery, reports, journals | Terpisah dari canonical; ownership jelas |
| **Runtime Area** | Blueprint & spec implementasi runtime | Traceable ke ADR/spec |
| **Testing Area** | Test suite | Terkelompok per capability; coverage traceable |
| **Release Area** | Artefak rilis (manifest, notes, compatibility, upgrade) | Metadata rilis tunggal; history terpisah |
| **Legacy Area** | Artefak usang yang di-archive (tidak aktif) | Terisolasi; tidak di ruang aktif |
| **History Area** | Rekaman historis (reports, sprint, release lama) | Terisolasi; append-only |
| **Generated Area** | Output mesin (workspace, memory, cache, venv, egg-info) | Tidak di-commit/ignored; bukan source |

### 2.2 Prinsip tata letak

- **Pemisahan tegas** antara canonical/aktif vs legacy/history/generated.
- **Satu klasifikasi per artefak** — tidak boleh satu file memegang >1 kategori.
- **Vendor terisolasi** (`modules/` atau area eksternal) — tidak bercampur dengan source aktif.
- **Generated tidak pernah menjadi source** — selalu ignorable, reproducible.

---

## 3. Repository Classification Rules

**Setiap artefak repo harus masuk TEPAT SATU kategori** (mutually exclusive & exhaustive).

| Kategori | Definisi | Contoh | Bukan |
|---|---|---|---|
| **Canonical** | Dokumen normatif yang menjadi acuan kebenaran sebuah domain | foundation, specifications, adr, compliance baseline, architecture inti | — |
| **Active Engineering** | Artefak kerja/proses yang aktif dipakai tim (bukan kebenaran final) | engineering/decisions, journey, roadmap kerja, design recovery, reports aktif | canonical |
| **Release** | Artefak metadata/siklus rilis | releases/manifest, notes, compatibility, upgrade | history |
| **Historical** | Rekaman masa lalu yang tidak lagi aktif diedit | history/legacy, releases/history, engineering/references lama | active |
| **Legacy** | Artefak usang yang dipertahankan utk rujukan, tidak dipakai produksi | docs/history/legacy era Framework+Module | canonical |
| **Generated** | Output yang dapat diregenerasi / data runtime | workspace, memory, cache, venv, egg-info, pyc | source |
| **External/Vendor** | Kode pihak ketiga yang ditempelkan | modules/openclaw | source aktif |

**Aturan wajib:**
- Klasifikasi **bersifat eksklusif** — satu file = satu kategori. Tidak ada kategori ganda.
- Klasifikasi **ditentukan oleh peran**, bukan lokasi semata.
- Sumber = Source Code aktif (src/sam) diklasifikasikan terpisah sebagai **Source/Foundation** aktif, bukan Canonical (canonical = dokumen).

---

## 4. Repository Invariants

Invariant yang **harus tetap benar setelah Program A selesai**, dan bertahan ke depannya:

| # | Invariant | Bukti verifikasi |
|---|---|---|
| I-01 | **Satu Source of Truth per domain** | Setiap domain (roadmap, spec, adr, compliance, release) punya tepat 1 dokumen SoT yang dirujuk konsisten |
| I-02 | **Tidak ada canonical duplicate** | Tidak ada 2 file canonical dengan konten/peran identik (0 duplicate) |
| I-03 | **Legacy tidak berada di area aktif** | Semua artefak legacy terisolasi; area aktif hanya berisi aktif |
| I-04 | **History terisolasi** | Rekaman historis tidak bercampur dengan dokumentasi aktif/operasional |
| I-05 | **Generated tidak menjadi source** | Tidak ada file generated yang dirujuk sebagai sumber kebenaran/implementasi |
| I-06 | **Vendor terisolasi** | Kode eksternal tidak bercampur/menyamar sebagai source SAM |
| I-07 | **Seluruh area dapat ditelusuri ownership-nya** | Setiap area/artefak punya pemilik (engineering, architecture, ops) yang jelas |
| I-08 | **Klasifikasi tunggal** | Setiap artefak memenuhi tepat 1 kategori (Rules §3), tidak ambigu |
| I-09 | **Bebas orphan aktif** | Tidak ada artefak aktif yang tak ter-lihat oleh index/navigasi (ATLAS) |

---

## 5. Convergence Principles

Prinsip Program A → aturan implementasi (acuan EA-005..EA-010):

| # | Prinsip | Arti operasional |
|---|---|---|
| P-01 | **Normalize before Move** | Sebelum pindah file, normalkan penamaan/konten dulu; jangan bawa anomali |
| P-02 | **Classify before Archive** | Klasifikasi artefak SELALU sebelum diputuskan arsip/hapus |
| P-03 | **Verify before Delete** | Tidak ada penghapusan tanpa verifikasi deterministik (isinya, rujukannya, backup) |
| P-04 | **Preserve History** | Semua rekaman historis dipertahankan; hanya dipindah ke area history, tak dihapus |
| P-05 | **Reversible Changes** | Setiap perubahan dapat dibalik (rollback-ready); tidak ada destruksi permanen non-reversibel |
| P-06 | **Single Ownership** | Setiap artefak punya tepat 1 pemilik (bukan ambiguity owner) |
| P-07 | **Single Canonical Reference** | Tiap domain merujuk 1 canonical; tidak ada referensi paralel |
| P-08 | **Engineering Verification Principle** | *Static inspection alone is insufficient whenever executable verification is available.* (Klasifikasi/validasi selalu via jalur eksekusi nyata bila tersedia — generik, tidak terikat kasus spesifik) |

---

## 6. Repository Success Criteria

Kriteria **objektif & terukur** bahwa repository telah konvergen (verifiable):

| # | Kriteria | Metrik target | Cara verifikasi |
|---|---|---|---|
| SC-01 | 0 canonical duplicate | **0** duplikat konten/peran canonical | Diff deterministik antar dokumen per domain |
| SC-02 | 100% classified | **100%** artefak masuk tepat 1 dari 7 kategori (§3) | Audit klasifikasi seluruh file |
| SC-03 | 100% ownership assigned | **100%** area/artefak punya pemilik jelas | Check ownership map (I-07) |
| SC-04 | 100% traceable | **100%** artefak aktif ter-cover matriks traceability (Mission→…→Acceptance) | Run checker traceability (G9) |
| SC-05 | 0 orphan active | **0** artefak aktif tak terindeks (ATLAS map lengkap) | Cek index/ATLAS vs file aktual |
| SC-06 | 0 unknown artifact | **0** file yang tak terklasifikasi / tak dikenal | Audit klasifikasi |
| SC-07 | 1 SoT per domain | **1** SoT per domain, bebas konflik G1-02 | Verifikasi rujukan konsisten (keputusan Architecture) |
| SC-08 | Clean working tree | Tidak ada deviasi EA di akhir tiap fase | `git status -s` = hanya pre-existing |

---

## 7. Batasan (yang TIDAK dilakukan EA-004-001)

EA-004-001 **tidak menentukan**:
- ❌ Source of Truth (keputusan Architecture Authority, G1-02)
- ❌ memindahkan folder / rename / delete / arsip final (deliverable berikutnya)
- ❌ mengubah repository (read-only penuh)

---

## 8. Exit Criteria EA-004-001

| Kriteria | Status |
|---|---|
| Target Repository State terdefinisi (§2) | ✅ |
| Repository Invariants lengkap (§4) | ✅ |
| Classification Rules lengkap (§3) | ✅ |
| Success Criteria terukur (§6) | ✅ |
| Tidak ada usulan perubahan repository | ✅ |
| Working tree bersih | ✅ (cek git status) |
| Tidak ada commit | ✅ |

---

*— Akhir EA-004-001 Repository Convergence Plan —*
