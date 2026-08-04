# EC-008 — Safe Refactor Rules

## Tujuan

Menjadi panduan refactor agar perubahan implementasi tidak merusak identitas SAM.

---

## Rule 1

Jangan mengubah Foundation.

Ubah implementasi.

---

## Rule 2

Jangan membuat Runtime baru.

Cari Runtime yang sudah ada.

---

## Rule 3

Jangan menambah Business Logic ke Presentation.

Presentation hanya ViewModel, Command, Navigation, Workspace.

---

## Rule 4

RuntimeService tetap Gateway.

Bukan Executor.

Bukan Decision.

Bukan Approval.

---

## Rule 5

ExecutionRuntime tetap jalur eksekusi resmi.

Jangan membuat execution baru.

---

## Rule 6

Coordinator tidak menerima responsibility baru.

Kurangi consumer.

Bukan tambah fitur.

---

## Rule 7

Provider tetap provider.

Jangan menaruh governance pada provider.

Provider yang belum aktif tetap dipertahankan (bukan dihapus).

---

## Rule 8

Approval tidak boleh dilewati.

Tidak ada shortcut.

---

## Rule 9

Composition Root tetap tunggal.

Jangan membuat composition baru di Presentation.

---

## Rule 10

Tambahkan Consumer.

Jangan menambah Capability.

---

## Rule 11

Activation lebih penting daripada Refactor.

---

## Rule 12

Refactor dilakukan hanya jika mengurangi Technical Debt.

---

## Regression Minimum

Sebelum commit:

- CLI
- Web
- REST
- Conversation
- Dashboard
- Runtime Status

Harus tetap berjalan.

Catatan: "berjalan" berarti entry point tersedia dan fungsi inti tidak rusak, sesuai status aktual masing-masing (beberapa host memang Not Fully Operational — jangan memperburuk).

---

## Engineering Insight

Perubahan kecil yang mengurangi coupling lebih bernilai daripada refactor besar yang hanya mempercantik struktur.

---

## Exit Criteria

Setiap commit mengurangi Technical Debt atau menambah Activation.

---

## Referensi

MISSION
CONSTITUTION
SPECIFICATION_FREEZE
ADR-000
ADR-007
D0-001
D1-001
