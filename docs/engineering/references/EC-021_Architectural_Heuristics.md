# EC-021 — Architectural Heuristics

## Tujuan

Mewariskan pola pikir engineer SAM.

Jika menemukan dua implementasi:

Jangan pilih salah satu.

Cari activation path.

---

Jika menemukan Runtime baru:

Jangan diasumsikan hidup.

Cari consumer.

---

Jika menemukan Service kosong:

Cari design intent sebelum mengisi implementasi.

---

Jika menemukan Coordinator besar:

Kurangi consumer.

Bukan langsung refactor.

---

Jika menemukan Provider tidak dipakai:

Jangan hapus.

Cari siapa producer-nya.

---

Jika menemukan Runtime dormant:

Jangan aktifkan.

Cari kebutuhan operasionalnya.

---

Jika menemukan banyak framework:

Jangan buat framework baru.

Gunakan yang ada.

---

Jika menemukan bug:

Periksa wiring lebih dulu.

Sering kali bug berasal dari activation, bukan implementasi.

---

Jika menemukan entry point tersedia:

Jangan otomatis sebut "Operational".

Periksa activation path dan status launcher.

---

Jika akan membuat abstraction:

Pastikan abstraction mengurangi coupling nyata.

---

Jika akan membuat Runtime:

Berhenti.

Cari capability yang sudah ada.

---

Engineering SAM lebih sering gagal karena salah membaca repository daripada salah menulis kode.
