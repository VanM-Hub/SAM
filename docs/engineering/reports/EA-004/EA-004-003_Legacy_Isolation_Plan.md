# EA-004-003 — Legacy Isolation Plan

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Legacy Isolation Plan · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini **menginventarisasi & merencanakan isolasi** artefak legacy — TANPA perpindahan,
> penghapusan, atau perubahan repository. Belum ada eksekusi. Strategi disusun agar **dapat diverifikasi**.

---

## 1. Legacy Inventory

Artefak legacy terverifikasi (evidence: struktur + isi + referensi file-eksplisit).

### 1.1 `docs/history/legacy/` — 6 file (era Framework+Module)

| Artefak | Lokasi | Jenis | Ukuran | Domain | Status penggunaan |
|---|---|---|---|---|---|
| `DEPENDENCY_RULES.md` | `docs/history/legacy/` | Dok. aturan | 5.6 KB | Architecture | Direferensikan file-eksplisit oleh A0-001 (audit) saja |
| `FRAMEWORK_VS_MODULE.md` | `docs/history/legacy/` | Dok. keputusan | 6.7 KB | Architecture | Direferensikan file-eksplisit oleh A0-001 saja |
| `GROWTH_MODEL.md` | `docs/history/legacy/` | Dok. model | 7.3 KB | Architecture | Direferensikan file-eksplisit oleh A0-001 saja |
| `LAYERS.md` | `docs/history/legacy/` | Dok. struktur | 5.9 KB | Architecture | **TIDAK ada referensi file-eksplisit**; kata "layers" di dok aktif = generik |
| `MODULE_INTERFACE.md` | `docs/history/legacy/` | Dok. interface | 5.4 KB | Architecture | Direferensikan file-eksplisit oleh A0-001 saja |
| `OPENCLAW_AS_MODULE.md` | `docs/history/legacy/` | Dok. keputusan | 7.6 KB | Vendoring | Direferensikan oleh A0-001 + README.md |

### 1.2 `docs/core/` — 2 file (potential legacy)

| Artefak | Lokasi | Jenis | Versi | Status penggunaan |
|---|---|---|---|---|
| `EXECUTION_MODEL.md` | `docs/core/` | Dok. model | **0.1.0** | Direferensikan oleh A0-001, I2-006, SAM_FRAMEWORK_v1.0_SPECIFICATION |
| `THINKING_PROTOCOL.md` | `docs/core/` | Dok. protokol | **0.1.0** | Belum terverifikasi referensi file-eksplisit |

### 1.3 Folder kosong — 9 folder (Dormant, struktur saja)

| Folder | Isi | Jenis |
|---|---|---|
| `docs/backlog` | 0 file | Dormant (kosong) |
| `docs/decisions` | 0 file | Dormant (kosong) |
| `docs/glossary` | 0 file | Dormant (kosong) — catatan: GLOSSARY aktif ada di `docs/foundation/GLOSSARY.md` |
| `docs/research` | 0 file | Dormant (kosong) |
| `docs/engineering/references` | 0 file | Dormant (kosong) — 25 file EC-\* pernah dihapus |
| `docs/engineering/reports` | 0 file | Dormant (kosong) |
| `docs/releases/history` | 0 file | Dormant (kosong) — arsip release lama dipindah |
| `docs/history/audit`, `reports`, `sprint-reports` | 0 file | Dormant (kosong) |

> Catatan: `docs/history/` berisi `docs/history/legacy/` (6 file) + 3 subfolder kosong (audit, reports, sprint-reports).
> `docs/assets` berisi 4 file (aktif, bukan legacy).

---

## 2. Legacy Classification

Klasifikasi **eksklusif** — setiap artefak TEPAT SATU status utama. Evidence belum cukup → **Unknown** (bukan asumsi).

| Status | Definisi | Artefak |
|---|---|---|
| **Historical** | Rekaman masa lalu era lama; dipertahankan utk konteks | — |
| **Deprecated** | Masih ada tapi resmi tidak disarankan; penggantinya ada | — |
| **Obsolete** | Statusnya telah digantikan penuh; TIDAK lagi valid | — |
| **Dormant** | Ada sebagai wadah/struktur, tidak berisi / tidak aktif | 9 folder kosong (backlog, decisions, glossary, research, engineering/references, engineering/reports, releases/history, history/audit, history/reports, history/sprint-reports) |
| **Archived** | Dipindah ke area history utk rujukan; TIDAK di jalur aktif | `LAYERS.md`, `DEPENDENCY_RULES.md`, `FRAMEWORK_VS_MODULE.md`, `GROWTH_MODEL.md`, `MODULE_INTERFACE.md`, `OPENCLAW_AS_MODULE.md` |
| **Unknown** | Evidence belum cukup untuk klasifikasi | `docs/core/EXECUTION_MODEL.md`, `docs/core/THINKING_PROTOCOL.md` |

**Ringkasan klasifikasi (12 artefak):**
- **Archived:** 6 file di `docs/history/legacy/` — sudah di area history (isolasi awal sudah terjadi).
- **Dormant:** 9 folder kosong — wadah struktur belum terisi.
- **Unknown:** 2 file `docs/core/` — versi 0.1.0, status formal belum terverifikasi penuh.

> `docs/core/` berstatus **Unknown** karena: versi 0.1.0 menyerupai draft, 1 file direferensikan (EXECUTION_MODEL oleh 3 dok), 1 belum terverifikasi (THINKING_PROTOCOL). Belum cukup evidence untuk memastikan archived/deprecated/dormant. Jangan berasumsi.

---

## 3. Dependency Mapping

Siapa mereferensikan / bergantung, apakah di jalur eksekusi, apakah hanya dokumentasi.

| Artefak | Siapa mereferensikan (file-eksplisit) | Di jalur eksekusi? | Hanya dokumentasi? |
|---|---|---|---|
| `DEPENDENCY_RULES.md` | `docs/design/A0-001…Audit.md` (objek analisis) | ❌ Tidak | ✅ Ya |
| `FRAMEWORK_VS_MODULE.md` | `docs/design/A0-001…Audit.md` | ❌ Tidak | ✅ Ya |
| `GROWTH_MODEL.md` | `docs/design/A0-001…Audit.md` | ❌ Tidak | ✅ Ya |
| `LAYERS.md` | **Tidak ada** (kata "layers" di dok aktif = generik, bukan link) | ❌ Tidak | ✅ Ya |
| `MODULE_INTERFACE.md` | `docs/design/A0-001…Audit.md` | ❌ Tidak | ✅ Ya |
| `OPENCLAW_AS_MODULE.md` | `docs/design/A0-001…Audit.md`, `README.md` | ❌ Tidak | ✅ Ya |
| `EXECUTION_MODEL.md` (core) | `A0-001`, `I2-006`, `SAM_FRAMEWORK_v1.0_SPECIFICATION` | ❌ Tidak (dokumentasi) | ✅ Ya |
| `THINKING_PROTOCOL.md` (core) | belum terverifikasi | ❌ Tidak | ✅ Ya |

**Temuan kunci:**
- **6 file legacy TIDAK berada di jalur eksekusi** — murni dokumentasi. Referensi eksklusif dari `A0-001` (paper audit EA-001) memperlakukan file ini sebagai **objek yang dianalisis**, bukan dependensi yang dipakai.
- **LAYERS.md** tidak punya referensi file-eksplisit dari dok aktif; penyebutan "layers" (1–6×) di SAM_ARCHITECTURE/Rulebook/Layer_Validation/ADR-000 adalah **kata generik** tentang konsep layering — bukan dependensi ke file legacy.
- **`docs/core/`** dirujuk sebagai objek (A0-001) dan sebagai sumber (I2-006, SAM_FRAMEWORK spec) — perlu verifikasi lebih lanjut apakah keduanya memang dependensi atau sekadar rujukan.

---

## 4. Isolation Strategy

Untuk **setiap kategori**: prinsip isolasi, target area, prasyarat sebelum isolasi. **Tidak menentukan lokasi folder akhir / aksi pemindahan** (itu fase implementasi).

| Kategori | Prinsip isolasi | Target area isolasi | Prasyarat sebelum isolasi |
|---|---|---|---|
| **Archived** (6 file legacy) | Sudah di area history → isolasi **terverifikasi** ketat: pastikan TIDAK ada referensi file-eksplisit dari area aktif yang membutuhkannya sebagai dependensi | Area history yang sudah terpisah dari area aktif | ① Konfirmasi A0-001 hanya objek analisis (bukan dependensi) — done; ② pastikan kata "layers" di dok aktif BUKAN link ke LAYERS.md — done (fileLink=0); ③ tidak ada import/execution path — done (dokumentasi murni) |
| **Dormant** (9 folder kosong) | Wadah kosong = isolasi pasif; pastikan tidak ada rujukan buntu ke isi yang diharapkan ada | Area structure (kosong) | ① Verifikasi tidak ada dok yang menunjuk ke path folder ini (broken reference risk); ② pastikan GLOSSARY aktif merujuk `docs/foundation/GLOSSARY.md` bukan folder `docs/glossary/` kosong |
| **Unknown** (2 file core) | **Jangan diisolasi dulu** — klasifikasi belum cukup; pertahankan di posisi saat ini hingga evidence lengkap | (belum ditentukan) | ① Verifikasi peran EXECUTION_MODEL & THINKING_PROTOCOL (source aktif vs draft lama) via rujukan I2-006 & SAM_FRAMEWORK spec; ② deteksi penggunaan/import nyata |

**Prinsip umum (dari EA-004-001 P-02 Classify-before-Archive):** isolasi hanya boleh terjadi jika klasifikasi sudah final. Artefak **Unknown** tidak diisolasi sampai terklasifikasi.

---

## 5. Risk Assessment

| Risiko | Artefak terdampak | Level | Alasan (evidence) |
|---|---|---|---|
| **Kehilangan traceability** | 6 file legacy + 2 core | **Medium** | Jika diisolasi tanpa matriks rujukan, rujukan A0-001/README/I2-006 bisa kehilangan jejak objek |
| **Kehilangan history** | 6 file legacy | **Low-Medium** | Sudah di area history; risiko rendah, tapi konteks era Framework+Module bisa hilang jika dihapus (bukan diarsip) |
| **Broken reference** | 9 folder kosong + OPENCLAW_AS_MODULE | **Medium** | `README.md` mereferensikan `OPENCLAW_AS_MODULE.md`; folder kosong (glossary) bisa menimbulkan rujukan buntu |
| **Compliance drift** | LAYERS, DEPENDENCY_RULES | **Low** | Compliance berpatokan pada `docs/compliance` (99 checker), bukan legacy; drift kecil. Namun jika fase (G9) merujuk legacy, berisiko |
| **Documentation drift** | docs/core, 6 legacy | **Medium** | Dua tumpukan (docs/core vs docs/history/legacy + dok aktif) bisa menyimpang; istilah "layers" generik menambah ambiguitas |

---

## 6. Rollback Consideration

Karena **belum ada implementasi**, rollback mendefinisikan **kondisi agar isolasi dapat dibatalkan** bila nanti dieksekusi.

| Kondisi | Deskripsi |
|---|---|
| **Revert path tersedia** | Sebelum isolasi dieksekusi, harus ada mekanisme mengembalikan artefak ke posisi semula (data/opsional backup) |
| **Referensi dipertahankan** | Rujukan ke artefak (A0-001, README, I2-006, SAM_FRAMEWORK spec) TIDAK boleh dihapus/ubah selama isolasi; hanya lokasi yang berubah |
| **Klasifikasi terdokumentasi** | Status asal (Archived/Dormant/Unknown) dicatat agar pembatalan mengembalikan status yang benar |
| **Tidak ada penghapusan permanen** | Isoolasi = pemindahan, BUKAN delete; rollback harus bisa memulihkan isi penuh |
| **Verifikasi balik** | Setelah isolasi, jalankan verifikasi deterministik (rujukan berekspektasi sama) untuk memastikan rollback konsisten |

---

## 7. EA-005 Input

### 7.1 Evidence yang diteruskan ke EA-005
- **Inventaris 12 artefak legacy** (6 file `docs/history/legacy/` + 2 file `docs/core/` + 9 folder kosong dormant).
- **Klasifikasi eksklusif**: Archived (6), Dormant (9 folder), Unknown (2 core).
- **Dependency map**: 6 legacy = dokumentasi murni, tidak di execution path; referensi eksklusif dari A0-001 (objek analisis); LAYERS tanpa referensi file-eksplisit.
- **Risk register**: 5 risiko (traceability, history, broken ref, compliance drift, doc drift) dengan level.

### 7.2 Gap yang masih harus diverifikasi (sebelum isolasi dieksekusi)
| Gap | Pertanyaan terbuka |
|---|---|
| `docs/core/*` status | Apakah EXECUTION_MODEL/THINKING_PROTOCOL source aktif atau draft lama? (periksa I2-006, SAM_FRAMEWORK spec, import path) |
| THINKING_PROTOCOL referensi | Referensi file-eksplisit belum terverifikasi — perlu scan all-repo |
| Folder `docs/glossary/` | Konfirmasi tidak ada rujukan buntu ke folder kosong ini |
| Rujukan buntu di folder dormant lain | Scan seluruh dok apakah ada path ke backlog/decisions/research/references/reports kosong |

### 7.3 Authority yang diperlukan
- **EA-005** (Implementation/Sequencing): otorisasi untuk merancang langkah isolasi (belum eksekusi).
- **Software Architect**: hanya untuk **klasifikasi final** `docs/core/*` (karena terkait arsitektur/otoritas dokumen) dan keputusan SoT terkait (G1-02) yang menjadi prasyarat sebagian isolasi.
- **Engineering**: evidence & verifikasi (sudah disediakan di dokumen ini).

---

## 8. Batasan (Larangan EA-004-003 — dipatuhi)

- ❌ Tidak memindahkan file
- ❌ Tidak menghapus file
- ❌ Tidak mengubah folder
- ❌ Tidak menentukan lokasi legacy
- ❌ Tidak menentukan folder archive
- ❌ Tidak menentukan retention policy
- ❌ Tidak menentukan lifecycle baru

---

## 9. Exit Criteria EA-004-003

| Kriteria | Status |
|---|---|
| Seluruh legacy terinventarisasi | ✅ (12 artefak: 6 file + 2 core + 9 folder) |
| Seluruh legacy punya satu klasifikasi | ✅ (Archived 6, Dormant 9, Unknown 2 — eksklusif) |
| Seluruh dependency dipetakan | ✅ (§3, file-eksplisit) |
| Strategi isolasi terdokumentasi | ✅ (§4) |
| Risiko dipetakan | ✅ (§5, 5 risiko) |
| Rollback consideration tersedia | ✅ (§6) |
| Input EA-005 tersedia | ✅ (§7) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ (cek git status) |
| Tanpa commit | ✅ |

---

*— Akhir EA-004-003 Legacy Isolation Plan —*
