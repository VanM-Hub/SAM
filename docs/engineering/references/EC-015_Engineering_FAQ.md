# EC-015 — Engineering FAQ

## Tujuan

Menjawab pertanyaan yang hampir selalu muncul ketika engineer baru mulai bekerja pada repository SAM.

---

### Kenapa RuntimeService terlihat kosong?

Karena RuntimeService adalah Gateway.

Masalahnya bukan implementasi.

Masalahnya adalah belum memiliki consumer.

Lihat:
D0-001

---

### Kenapa ExecutionRuntime tidak dipakai?

Pipeline sudah selesai.

Belum ada producer dari entry point.

Lihat:
D1-001

---

### Kenapa RuntimeCoordinator sangat besar?

Karena sebagian entry point masih melakukan direct wiring ke Coordinator.

Prioritas engineering adalah mengurangi consumer, bukan memecah Coordinator.

Catatan: tidak semua flow lewat Coordinator — Operations/Desktop sudah berjalan lewat Provider.

---

### Kenapa banyak runtime dormant?

Sebagian besar runtime merupakan capability framework yang belum memiliki activation path.

Dormant bukan dead code.

---

### Kenapa tidak membuat runtime baru?

Repository sudah memiliki capability yang jauh lebih banyak daripada yang saat ini digunakan.

Activation lebih penting daripada ekspansi.

---

### Kenapa ada dua execution?

Repository masih berada pada masa transisi antara jalur lama dan jalur baru.

Target engineering adalah menyelesaikan wiring, bukan membuat execution ketiga.

---

### Kenapa Presentation baru belum dipakai?

Presentation sudah selesai secara desain.

Integrasi entry point belum selesai.

Consumer masih sedikit (Ready but not primary).

---

### Kenapa Provider belum aktif?

Provider observation sudah aktif di jalur Operations/Desktop.

Provider execution belum aktif karena ExecutionRuntime belum menerima request production.

---

### Kenapa console / api_server / headless tidak jalan melalui launcher?

Kontrak fungsi run/start module-level belum cocok antara launcher dan modul host.

Status: Not Fully Operational (bukan activation debt murni).

Ini akan disesuaikan seiring migrasi entry yang bersangkutan.

---

### Apa technical debt terbesar?

Activation.

Bukan SQLite.

Bukan struktur folder.

---

### Apa ukuran keberhasilan engineering?

Consumer bertambah.

Producer bertambah.

Activation bertambah.

Technical Debt berkurang.

---

### Apa yang harus dilakukan sebelum coding?

- Baca 01_AKTUAL_STATE.md
- Baca Work Order aktif
- Pastikan tidak bertentangan dengan Constitution
- Cari capability yang sudah ada
- Hindari membuat Runtime baru
- Identifikasi entry point, activation path, dan status launcher secara terpisah

---

### Apa yang tidak boleh dilakukan?

- Mengubah Foundation.
- Menambah Runtime baru.
- Menambah Business Logic ke Presentation.
- Menjadikan RuntimeService sebagai Executor.
- Menambah responsibility ke RuntimeCoordinator.
- Menyatakan host Not Fully Operational sebagai "Operational".

---

## Referensi

MISSION
CONSTITUTION
SPECIFICATION_FREEZE
E0-001
O0-001
D0-001
D1-001
RSR-001
RSR-002
