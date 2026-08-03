# HISTORY_POLICY

**Status:** Live Policy
**Version:** 1.0
**Date:** 2026-08-03

> **Aturan inti: History bukan Authority.**
> Dokumen History tidak boleh digunakan sebagai dasar implementasi baru.

---

## Definisi

**History** = dokumen di `docs/history/**` yang berisi catatan masa lalu Project SAM:
desain lama, laporan fase, keputusan yang sudah digantikan, dan artefak proses yang telah selesai.

## Kapan History BOLEH dipakai

History hanya boleh dipakai untuk:

| Penggunaan | Contoh |
|---|---|
| **Audit** | Menelusuri mengapa suatu keputusan diambil |
| **Forensik** | Melacak asal-usul perubahan / bug historis |
| **Evolusi desain** | Memahami bagaimana arsitektur berkembang |
| **Referensi keputusan lama** | Melihat konteks keputusan yang sudah tidak aktif |

## Kapan History TIDAK BOLEH dipakai

History **tidak boleh** dipakai untuk:

- Implementasi fitur baru.
- Membuat keputusan arsitektur baru.
- Membaca spesifikasi yang masih berlaku.
- Mengambil status "masih berlaku" dari doc lama.

> Jika engineer/AI menemukan keputusan di History yang tampak masih relevan,
> itu **bukan** otoritas. Yang berlaku adalah dokumen Live di `docs/AUTHORITY_MAP.md`.

## Prinsip

1. **Authority selalu di atas History.** Jika konflik, Live authority menang.
2. **History tidak pernah dipromosikan kembali** ke Live tampa proses resmi
   (baru boleh menjadi authority setelah melalui saluran yang sah).
3. **Arsip tidak dihapus.** History tetap ada untuk audit — hanya diklasifikasikan
   sebagai bukan-otoritas.

## Akibat Bagi AI / Engineer

- Jangan pernah mengambil keputusan dari `docs/history/**` untuk kode baru.
- Jika satu-satunya sumber keputusan ada di History, itu tanda bahwa keputusan
  tersebut **belum dimigrasikan** ke Live — laporkan, jangan eksekusi.
- Saat ragu dokumen mana yang jadi otoritas, lihat `docs/AUTHORITY_MAP.md`.

---

*Kebijakan ini berlaku untuk semua dokumen di bawah `docs/history/**`.*
