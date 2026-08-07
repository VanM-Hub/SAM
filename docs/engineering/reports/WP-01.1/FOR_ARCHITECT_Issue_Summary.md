# Architecture Issue Report — G1-02 & G1-03 (untuk Software Architect)

**Program:** MISSION-2A / Program A · **Fase:** Development Execution · **WS-01 Repository Convergence · WP-01.1**
**Pengirim:** ZARA (Lead Implementation Engineer) · **Tanggal:** 2026-08-08
**Sifat:** Pemintaan keputusan arsitektur · Evidence berbasis bukti deterministik

---

## Ringkasan

Implementasi WP-01.1 (Repository Mapping & Canonical Classification) menemukan 2 isu yang butuh keputusan
Software Architect. Keduanya **diluar kewenangan Engineering** (menyentuh Dependency Rules & Source of Truth).
Engineering **berhenti** pada area terdampak sesuai guardrail, mengamankan evidence, dan menerbitkan laporan ini.

---

## Issue 1 — Klasifikasi `docs\core\` (G1-03)

### Fakta (evidence)
Dua dokumen di `docs\core\`:
- `EXECUTION_MODEL.md` — **Draft v0.1.0**, updated 2026-07-20, hash `272213E1...`
- `THINKING_PROTOCOL.md` — **Draft v0.1.0**, updated 2026-07-20, hash `B63E2ADC...`

Keduanya:
- **Tidak tercantum di ATLAS** (bukan navigasi resmi repository)
- **Menduplikasi authority Execution** dari `docs/specifications/EXECUTION_SPECIFICATION.md` (v1.0 Foundational) — sudah tercatat sebagai **AI-002 (High)** di audit A0-001
- **Direferensikan eksplisit dari 8 file unik / 16 referensi**: 7 file di `modules\openclaw\` + 1 file di `docs\` (A0-001), **termasuk SPEC freeze** (`SAM_FRAMEWORK_v1.0_SPECIFICATION.md` L134-135)

### Implikasi
Memindahkan/menghapus kedua file akan **memutus 16 dependensi eksplisit yang sah** (termasuk dari spec freeze)
→ melanggar guardrail "tidak mengubah Dependency Rules". Oleh karena itu **relokasi fisik ditahan** sampai ada keputusan.

### Opsi keputusan yang diminta
| Opsi | Deskripsi | Risiko |
|---|---|---|
| **A (in-place)** | Tandai kedua file sebagai **Reference/Draft** tanpa mengubah isi; path tetap; 16 referensi tetap valid | Rendah, reversible |
| **B (relokasi)** | Pindah ke `docs\history\` (arsip) atau `docs\models\`; **wajib update 16 referensi di 8 file + spec freeze** | Sedang (bisa putus referensi bila tak tuntas) |
| **C (konsolidasi)** | `EXECUTION_SPECIFICATION.md` jadi satu-satunya authority; Draft `EXECUTION_MODEL` dihapus | Lebih luas, perlu sinkronisasi |

**Pertanyaan:** Opsi A/B/C mana yang dipilih? Jika **B**, apakah Engineering diberi wewenang untuk meng-update
referensi lintas file secara bertahap + reversible?

---

## Issue 2 — Source of Truth Roadmap (G1-02)

### Fakta
Konflik sumber kebenaran roadmap:
- `ROADMAP.md` (root) mengklaim "single source of truth"
- `docs/engineering/roadmap/ROADMAP SAM 2.x.md` — ber-Version 2.0.0, direferensikan ATLAS

Detail lengkap di EA-003-003 (Source of Truth Resolution Report).

### Implikasi
Pemilihan SoT roadmap adalah **keputusan arsitektur**, bukan Engineering.

### Opsi keputusan yang diminta
- **A** — Pisahkan peran: `ROADMAP.md` = historis/ringkas; `ROADMAP SAM 2.x.md` = SoT aktif.
- **B** — `ROADMAP.md` root jadi SoT utama.
- **C** — Konsolidasi menjadi satu dokumen tunggal.

**Pertanyaan:** Opsi A/B/C mana yang diotorisasi untuk SoT roadmap?

---

## Dampak jika tidak diputuskan
- WP-01.1 tidak dapat menyelesaikan klasifikasi fisik; **Gate A0 belum dapat ditutup**.
- Risiko pembaca memakai Draft `EXECUTION_MODEL` sebagai authority (salah tafsir) tetap ada.

## Setelah keputusan
Engineering langsung melanjutkan WP-01.1 (klasifikasi fisik) konsisten dengan opsi terpilih, bertahap, reversible,
dan diverifikasi.

---

*— Akhir Architecture Issue Report —*
