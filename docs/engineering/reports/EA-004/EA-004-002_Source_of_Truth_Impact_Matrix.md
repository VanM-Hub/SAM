# EA-004-002 — Source of Truth Impact Matrix

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Source of Truth Impact Matrix · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini **memetakan konflik, ketergantungan, dan dampak SoT** — TANPA memilih SoT.
> Tujuan: menyediakan evidence yang akan dipakai **Software Architect** untuk keputusan.
> Engineering tidak memilih / menyatukan / merekomendasikan SoT.

---

## 1. Scope — Domain dengan Klaim Source of Truth

Daftar domain yang memiliki klaim/potensi klaim SoT. **Belum ditentukan mana yang benar.**

| # | Domain | Mengklaim SoT? | Note |
|---|---|---|---|
| 1 | Mission | Implisit (status Accepted, Owner Project SAM) | `docs/foundation/MISSION.md`; VISION status Foundational |
| 2 | Roadmap | **Ya — eksplisit (konflik)** | `ROADMAP.md` [5 klaim] vs `.../ROADMAP SAM 2.x.md` |
| 3 | Architecture | **Ya — Canonical:true** | `SAM_ARCHITECTURE.md`; derived from Constitution |
| 4 | Foundation | **Ya — Governance "Git is SoT"** | CONSTITUTION Canonical:true, Authority:Highest; GOVERNANCE, GLOSSARY |
| 5 | ADR | Implisit kuat | ADR-000..028 (25 file), "Source of Authority" |
| 6 | Engineering | Tidak (eksplisit "Bukan SoT arsitektur") | `docs/engineering/roadmap/README.md` |
| 7 | Runtime | Implisit — deklarasi Source of Authority | R4-001: "Foundation\|Spec\|Blueprint\|ADR-000..007" |
| 8 | Release | Implisit — metadata rilis | `docs/releases/manifest.md` |
| 9 | Documentation | Implisit — aturan pengelolaan | `docs/documentation/` (8 file) |

---

## 2. Source Inventory

Per domain: dokumen yang mengklaim SoT, yang mereferensikannya, dan yang bergantung padanya.

### 2.1 Roadmap (domain paling konfliktual G1-02)

| Dokumen | Peran | Referensinya | Bergantung pada |
|---|---|---|---|
| `ROADMAP.md` (root) | Klaim "Sumber kebenaran tunggal untuk seluruh fase SAM" (baris 3, 195) + "Kebijakan Sinkronisasi Dokumen" | ATLAS, README | — |
| `docs/engineering/roadmap/ROADMAP SAM 2.x.md` | Strategi SAM 2.x (Program A–E); Version 2.0.0, Authority Chief Architect; **tanpa klaim SoT eksplisit** | ATLAS menunjuk ke sini | Foundation, ROADMAP.md (histori) |
| `docs/engineering/roadmap/README.md` | **Eksplisit "Bukan SoT arsitektur"** — hanya rencana kerja engineering | — | — |

### 2.2 Architecture

| Dokumen | Peran | Referensinya | Bergantung pada |
|---|---|---|---|
| `docs/architecture/SAM_ARCHITECTURE.md` | **Canonical:true**, Authority derived from Constitution; realizes Governance | ruang arsitektur | MISSION, CONSTITUTION, PHILOSOPHY, GOVERNANCE, GLOSSARY, Model (TRUST/RISK/DECISION/MEMORY) |
| `docs/architecture/Architecture_Rulebook.md` | Rulebook (tanpa klaim eksplisit) | arsitektur | SAM_ARCHITECTURE |

### 2.3 Foundation

| Dokumen | Peran | Referensinya | Bergantung pada |
|---|---|---|---|
| `docs/foundation/CONSTITUTION.md` | **Canonical:true, Authority:Highest**, Scope seluruh SAM; Supersedes history | GOVERNANCE, docs | MISSION (legitimacy), VISION |
| `docs/foundation/GOVERNANCE.md` | **"The Git repository is the single source of truth"** (bagian Source of Truth) | CONSTITUTION | MISSION, PHILOSOPHY |
| `docs/foundation/GLOSSARY.md` | Klaim=5; definisi istilah | banyak dokumen | — |
| `docs/foundation/MISSION.md` | Status Accepted, Owner Project SAM | CONSTITUTION ("Mission Source: MISSION.md") | — |
| `docs/foundation/VISION.md` | Status Foundational | — | — |

### 2.4 ADR

| Dokumen | Peran | Referensinya | Bergantung pada |
|---|---|---|---|
| `docs/adr/ADR-000…028` (25 file) | Keputusan arsitektur; "Source of Authority: Foundation\|Spec\|Blueprint" | runtime/architecture/design | Foundation, Spec, arsitektur |

### 2.5 Compliance / Runtime / Release

| Dokumen | Peran | Referensinya | Bergantung pada |
|---|---|---|---|
| `docs/compliance/P1-005_Runtime_Compliance_Manifest.md` | **"Validator bind ke catalog sebagai source of truth"** | compliance | catalog |
| `docs/compliance/P1-001…008` | Baseline compliance + 99 checker | runtime | — |
| `docs/runtime/R4-001_Reference_Runtime_Architecture.md` | "Source of Authority: Foundation\|Spec\|Blueprint\|ADR-000..007" | runtime | Foundation, Spec, ADR |
| `docs/releases/manifest.md` | Metadata rilis (SAM 1.0, Active Development) | release | ROADMAP (fase) |

---

Status konflik yang digunakan dokumen ini (konsisten untuk seluruh EA):
- **Active** — konflik yang sudah dikonfirmasi aktif (rujukan bertabrakan nyata).
- **Potential** — indikasi konflik yang belum dikonfirmasi; butuh verifikasi lebih lanjut.
- **Historical** — konflik masa lalu yang sudah tidak relevan/tercatat sebagai riwayat.
- **Resolved** — sudah ada keputusan (keputusan Architecture).

## 3. Conflict Matrix

Hanya klasifikasi konflik — **tanpa solusi**.

| Gap ID | Status | Domain | Dokumen terlibat | Jenis Konflik | Klaim/evidence |
|---|---|---|---|---|---|
| **G1-02** | **Active** | Roadmap | `ROADMAP.md` vs `ROADMAP SAM 2.x.md` | **Klaim eksplisit + referensi silang** | ROADMAP.md klaim tunggal [5 hit]; ATLAS navigasi → folder strategi; keduanya hash-different (2A0D… vs 2813…) |
| G8-03 | **Active** | Documentation | ROADMAP.md, ATLAS, GLOSSARY | **Terminologi** — "single source of truth" dipakai inkonsisten | ROADMAP klaim tunggal; ATLAS arah lain; GLOSSARY tak terindeks (folder glossary/ kosong) |
| (D1) | **Potential** | Architecture | `SAM_ARCHITECTURE.md` (Canonical:true) vs `Architecture_Rulebook.md` | **Klaim implisit** — dua dok arsitektur dgn peran berbeda | SAM_ARCHITECTURE Canonical:true [7 hit]; Rulebook tanpa klaim |
| (D2) | **Potential** | Mission | `MISSION.md` vs `VISION.md` | **Overlap terminologi** — keduanya status berbeda (Accepted vs Foundational), peran tak dibedakan eksplisit | Header status (Accepted vs Foundational) |
| (D3) | **Potential** | Foundation | `GOVERNANCE.md` "Git is SoT" vs `CONSTITUTION.md` Canonical:true | **Klaim implisit tumpang tindih** — siapa "SoT ultimate"? | GOVERNANCE §SoT; CONSTITUTION Canonical:true, Authority:Highest |
| (D4) | **Potential** | Compliance | `P1-005` "catalog sebagai SoT" vs `P1-008`/builder | **Referensi silang** — SoT katalog vs checker | P1-005 klaim; 99 checker di builder |
| (D5) | **Potential** | Runtime | `R4-001` "Source of Authority…" | **Klaim implisit** — banyak sumber otoritas | Header R4-001 |

> **Catatan:** (D1)–(D5) berstatus **Potential** — indikasi konflik yang belum dikonfirmasi, bukan konflik aktif. Hanya G1-02 & G8-03 berstatus **Active**. Semua disajikan sebagai evidence, bukan keputusan.

---

## 4. Impact Matrix

Tingkat dampak untuk **setiap konflik** terhadap dimensi. Skala + definisi singkat (konsisten untuk seluruh dokumen):

| Level | Definisi singkat |
|---|---|
| **None** | Tidak ada dampak terukur pada dimensi tsb. |
| **Low** | Dampak minor/terlokalisir; tidak menghalangi pekerjaan; kosmetik/navigasi. |
| **Medium** | Dampak terasa; memerlukan keputusan atau kerja ekstra; risiko interpretasi. |
| **High** | Dampak signifikan; menghalangi sebagian alur kerja/keputusan; butuh intervensi. |
| **Critical** | Dampak menghentikan/merusak dimensi kunci; butuh keputusan segera sebelum lanjut. |

### 4.1 Impact Matrix

| Konflik | Arch | Eng | Compl | Release | Trace | Repo |
|---|---|---|---|---|---|---|
| **G1-02** (Roadmap dual) | **High** — dua arah roadmap untuk keputusan arsitektur | **High** — engineering tak tahu rujukan fungsi | **Medium** — compliance manifest merujuk fase | **High** — fase/release tak konsisten | **Critical** — Mission→…→Release putus di fase | **High** — dua dokumen induk |
| **G8-03** (terminologi SoT) | **Medium** — istilah ambigu | **Medium** — salah interpretasi | Low | Low | **Medium** — trace bergantung istilah | **Medium** — navigasi ganda |
| **(D1)** Arch (Canonical vs Rulebook) | **Medium** — dua sumber struktur | Low | Low | Low | Medium | Low |
| **(D2)** Mission vs Vision | **Low** | Low | None | None | Low | Low |
| **(D3)** Governance vs Constitution | **Medium** — klaim SoT ultimate tabrakan | Low | Low | None | Medium | **Medium** — dua klaim "tertinggi" |
| **(D4)** Compliance catalog | **Low** | **Medium** — jarak SoT katalog vs checker | **Medium** — inti compliance | None | Medium | Low |
| **(D5)** Runtime authority | **Low** | **Medium** — runtime merujuk banyak otoritas | Low | None | Medium | Low |

**Alasan kunci (berbasis evidence):**
- Komplit: G1-02 berdampak **Critical** pada traceability karena fase (Program A–E) adalah penghubung Mission→Release; jika rujukan fase ganda, matriks end-to-end (G9) tak bisa diverifikasi.
- D3: dua dokumen foundation menyandang klaim kuat (Constitution Authority:Highest + Governance "Git is SoT") → berpotensi tabrakan otoritas ultimate.

---

## 5. Dependency Graph (logis antar dokumen SoT)

### Observed Repository Dependency Graph

Grafik *merujuk yang diekstrak dari frontmatter/depends-on*, **tidak mengubah dependency**.

```
                    [MISSION]  [VISION]
                        \        /
         [PHILOSOPHY]  [GOVERNANCE] - "Git repo is SoT"
                 \         |
              [CONSTITUTION] (Canonical:true, Authority:Highest, Scope: entire SAM)
                    |  "Supersedes history"
            [SAM_ARCHITECTURE] (Canonical:true, derived from Constitution)
              /       |        \
    [Rulebook]   [ADR-000..028]   [Runtime R4-001]
                     |               |
              [Compliance P1]    [Release manifest]
                     |
            [ROADMAP.md] <---G1-02 conflict---> [ROADMAP SAM 2.x]
                     |
                   [ATLAS]
```

- **Root:** CONSTITUTION (Authority:Highest, seluruh scope) — + MISSION/VISION sebagai sumber legitimasi.
- **Upstream (yang direferensikan):** Constitution, MISSION, PHILOSOPHY, GOVERNANCE, GLOSSARY → SAM_ARCHITECTURE.
- **Downstream:** SAM_ARCHITECTURE → Rulebook/ADR/Runtime → Compliance/Release.
- **Leaf:** Compliance P1, Release manifest, ATLAS.
- **Konflik leaf:** dua ROADMAP (G1-02) — keduanya di posisi downstream yang sama.

> Grafik ini **observasi dependency yang ada** (dari frontmatter), bukan usulan. Tidak ada dependency yang diubah.

---

## 6. Resolution Preconditions

Untuk **setiap konflik**: evidence apa yang harus tersedia **sebelum Software Architect** mengambil keputusan. Fokus kebutuhan evidence, bukan solusi.

| Konflik | Evidence yang harus tersedia sebelum keputusan |
|---|---|
| **G1-02** | ① Niat/peran asli tiap dokumen (ROADMAP.md = histori+produk? SAM 2.x = strategi?); ② siapa yang direferensikan ATLAS/README/foundation saat ini (dampak navigasi); ③ jumlah rujukan eksternal ke tiap dokumen; ④ perbedaan konten substantif (roadmap produk vs strategi) — sudah dimiliki; ⑤ owner/authority asli tiap file |
| **G8-03** | ① Definisi tunggal istilah "source of truth" yang dipakai repo; ② lokasi glossary yang benar (docs/foundation/GLOSSARY vs folder glossary/ kosong); ③ daftar semua dokumen yang memakai istilah ini + frekuensi |
| **(D1)** | ① Peran eksplisit per dok arsitektur (SAM_ARCHITECTURE vs Rulebook) — apakah memang beda fungsi; ② siapa yang dikutip oleh ADR/runtime |
| **(D2)** | ① Peran MISSION vs VISION (Accepted vs Foundational) — perbedaan formal; ② siapa yang mereferensikan masing-masing |
| **(D3)** | ① Interpretasi "Git repo is SoT" vs "Constitution Canonical:true" — mana yang lebih tinggi; ② rantai otoritas formal (Constitution→Architecture→…) |
| **(D4)** | ① Peran catalog compliance (P1-005) vs checker builder (P1-008) — SoT definisi vs eksekusi; ② jalur produksi aktual (sudah: Builder) |
| **(D5)** | ① Definisi "Source of Authority" per dok runtime; ② apakah multi-source adalah desain (federasi otoritas) atau kontradiksi |

> Keseluruhan preconditions fokus pada **kebutuhan evidence**, bukan rekomendasi solusi — sesuai mandat EA-004-002.

---

## 7. Architecture Authority Boundary

Sebagai bagian **formal** dokumen ini, dinyatakan tanpa ambiguitas:

1. **Engineering TIDAK memilih Source of Truth** — keputusan SoT adalah wewenang Software Architect.
2. **Engineering TIDAK menyatukan Source of Truth** — konsolidasi/merge bukan tugas EA-004.
3. **Engineering HANYA menyediakan evidence** — pemetaan konflik, dependency, dampak, dan preconditions.
4. **Keputusan berada pada Software Architect** — termasuk untuk G1-02 (Roadmap), D1–D5 (potensial).

Dokumen ini (EA-004-002) adalah **input keputusan**, bukan **keputusan**.

---

## 8. Batasan (Larangan EA-004-002 — dipatuhi)

- ❌ Tidak memilih Source of Truth
- ❌ Tidak mengusulkan dokumen canonical
- ❌ Tidak mengubah ROADMAP
- ❌ Tidak mengubah ATLAS
- ❌ Tidak mengubah Architecture
- ❌ Tidak membuat rekomendasi implementasi
- ❌ Tidak mengusulkan rename

---

## 9. Exit Criteria EA-004-002

| Kriteria | Status |
|---|---|
| Seluruh konflik SoT dipetakan | ✅ (7 baris Conflict Matrix: G1-02, G8-03, D1–D5) |
| Seluruh dependency dipetakan | ✅ (§5 Dependency Graph) |
| Seluruh dampak diklasifikasikan | ✅ (§4 Impact Matrix, konsisten) |
| Tidak ada keputusan Architecture diambil | ✅ |
| Seluruh evidence dapat ditelusuri | ✅ (per-file + per-klaim) |
| Working tree bersih | ✅ (cek git status) |
| Tidak ada commit | ✅ |

---

*— Akhir EA-004-002 Source of Truth Impact Matrix —*
