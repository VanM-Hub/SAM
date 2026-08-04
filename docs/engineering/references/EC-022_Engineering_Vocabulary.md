# EC-022 — Engineering Vocabulary

Activation

Capability mulai memiliki consumer nyata.

---

Activation Path

Jalur wiring yang benar-benar dilewati request.

Memiliki consumer, dipanggil runtime, ikut lifecycle, terlihat pada execution trace.

---

Consumer

Komponen yang menggunakan capability.

---

Producer

Komponen yang menghasilkan request.

---

Entry Point

Aplikasi memiliki titik masuk (CLI, Desktop, REST, Web).

Keberadaan entry point tidak otomatis berarti activation path atau host operational aktif.

---

Host / Launcher Operational

Launcher berhasil menjalankan aplikasi secara penuh sampai process hidup.

Kondisi terpisah dari activation dan dari entry point.

---

Operational

Digunakan production.

Hanya dipakai bila launcher benar-benar hidup atau jalur benar-benar aktif.

---

Partially Operational

Sebagian jalur aktif, sebagian belum.

---

Operational Core

Bagian yang menjadi tulang punggung runtime yang benar-benar berjalan.

---

Transition State

Berada di antara jalur lama dan jalur baru.

---

Ready but not primary

Selesai secara desain, tersedia, tetapi belum menjadi jalur utama.

---

Available but not fully activated

Tersedia, tetapi belum teraktivasi penuh.

---

Direct Wiring

Entry membuat komponen inti (mis. RuntimeCoordinator) secara langsung, tanpa jalur resmi.

---

Not Fully Operational

Belum sepenuhnya berjalan (mis. launcher mismatch).

---

Preview

Sudah dapat berjalan tetapi belum menjadi jalur utama.

---

Dormant

Capability tersedia tetapi belum memiliki activation.

---

Legacy

Masih digunakan tetapi bukan arah akhir Architecture.

---

Gateway

Boundary.

Tidak berisi business logic.

---

Execution

Pipeline yang menjalankan capability.

---

Provider

Implementasi konkret terhadap dunia luar.

---

Technical Debt

Perubahan implementasi yang menghambat activation atau integration.

---

Engineering Progress

Bertambahnya activation dan berkurangnya technical debt.
