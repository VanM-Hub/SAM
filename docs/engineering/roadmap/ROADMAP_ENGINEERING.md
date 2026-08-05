# ROADMAP ENGINEERING

**Status:** Disetujui (Software Architect + Guardian Mission, 2026-08-06)
**Isi:** Rencana kerja Engineering. Bukan sumber aturan arsitektur.

---

## Prinsip kerja

Engineering mengerjakan yang sudah diputuskan, tidak memutuskan yang arsitektural.

Boleh: implementasi, refactor, test, integrasi, observability, performa, CI/CD, kurangi utang teknis, tutup kesenjangan implementasi.

Tidak boleh: menetapkan arsitektur, ADR, spesifikasi, batasan, dependensi, kepemilikan, atau model runtime.

Kalau nemu hal yang terasa melanggar aturan arsitektur: **berhenti, kumpulkan bukti, lapor, serahkan ke Software Architect.**

---

## Rencana 7 Sprint

| # | Sprint | Catatan |
|---|---|---|
| 1 | Tutup kesenjangan implementasi | L1 ditutup. L2 & L6 dianggap kesenjangan implementasi. |
| 2 | Kepatuhan arsitektur | Ada dugaan pelanggaran? Jangan putuskan sendiri. Sertakan klausul aturan, bukti, analisis → eskalasi. |
| 3 | Kualitas kode | Jangan ubah perilaku publik, aturan dependensi, kepemilikan, atau batasan. |
| 4 | Testing | Testing membuktikan implementasi, bukan arsitektur. |
| 5 | Compliance | Checker dipakai untuk cek implementasi vs baseline, bukan untuk memutuskan arsitektur. |
| 6 | Utang teknis | Hapus hanya yang benar-benar tak terpakai dan tak dilindungi arsitektur. Jangan sentuh compatibility layer yang masih bagian arsitektur. |
| 7 | Siap rilis | Kondisi: tidak ada pelanggaran arsitektur yang dikonfirmasi. (Penentuan pelanggaran = wewenang Architect.) |

---

## Aturan eskalasi

Temuan yang dianggap melanggar aturan arsitektur:
1. Berhenti.
2. Kumpulkan bukti.
3. Lapor: fakta · bukti · dampak · area yang terdampak.
4. Serahkan ke Software Architect.

*Dokumen ini rencana kerja Engineering dan tidak mengubah aturan arsitektur apa pun.*
