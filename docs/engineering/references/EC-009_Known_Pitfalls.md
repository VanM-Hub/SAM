# EC-009 — Known Pitfalls

## Tujuan

Mencatat jebakan implementasi yang telah ditemukan selama audit sehingga tidak terulang pada pekerjaan engineering berikutnya.

---

## Pitfall 1

Folder ada ≠ Runtime hidup.

Selalu verifikasi:
- consumer
- activation path
- startup trace

Jangan menilai hanya dari nama folder.

---

## Pitfall 2

Runtime lengkap ≠ Operational.

Banyak runtime memiliki:
- descriptor
- contract
- certification
- bridge

tetapi tetap dormant.

---

## Pitfall 3

0 Consumer ≠ Bug.

RuntimeService bukan gagal.

Masalahnya adalah wiring.

---

## Pitfall 4

0 Producer ≠ Pipeline rusak.

ExecutionRuntime lengkap.

Masalahnya tidak ada yang mengirim request.

---

## Pitfall 5

Coordinator besar bukan berarti harus dipecah.

Kurangi consumer terlebih dahulu.

Refactor internal dilakukan setelah activation berjalan.

---

## Pitfall 6

Jangan mengejar aktivasi semua runtime.

Aktifkan hanya runtime yang memiliki kebutuhan operasional nyata.

---

## Pitfall 7

Jangan membuat Runtime baru.

Cari capability yang sudah tersedia.

Repository sudah memiliki banyak capability yang belum digunakan.

---

## Pitfall 8

Jangan memperbaiki Architecture untuk menyelesaikan Wiring.

Architecture sudah Freeze.

Yang berubah adalah implementasi.

---

## Pitfall 9

Jangan menambah Business Logic pada RuntimeService.

RuntimeService adalah Gateway.

---

## Pitfall 10

Jangan menjadikan RuntimeCoordinator sebagai tempat semua fitur baru.

Setiap fitur baru yang masuk akan memperbesar God Object.

---

## Pitfall 11

Jangan menganggap Technical Debt terbesar adalah SQLite.

Technical Debt terbesar adalah Activation.

---

## Pitfall 12

Jangan menghapus runtime dormant tanpa bukti bahwa runtime tersebut benar-benar tidak menjadi bagian roadmap.

Dormant bukan dead code.

---

## Pitfall 13

Jangan menghubungkan Provider langsung dari Presentation.

Selalu melalui jalur resmi.

---

## Pitfall 14

Jangan mengukur kemajuan dari jumlah dokumen.

Kemajuan diukur dari:
- activation
- integration
- operational capability

---

## Pitfall 15 (baru)

Entry point tersedia ≠ Host operational.

Keberadaan CLI/Web/REST/Desktop tidak berarti launcher berhasil hidup.

Periksa fungsi run/start module-level sebelum menyatakan "Operational".

---

## Pitfall 16 (baru)

Jangan menganggap ada satu jalur tunggal.

Repository memiliki beberapa activation path yang hidup berdampingan.

Sebagian flow lewat RuntimeCoordinator, sebagian lewat Operations/Provider.

Generaliasi "semua berhenti di Coordinator" tidak akurat.

---

## Engineering Insight

Sebagian besar kesalahan yang mungkin dilakukan engineer berasal dari salah membaca kondisi repository, bukan dari kesalahan coding.

---

## Referensi

A0-001
E0-001
O0-001
RSR-001
RSR-002
