# EC-014 — Repository Mental Model

## Tujuan

Memberikan cara berpikir yang benar ketika membaca repository SAM.

---

## Cara Melihat Repository

Jangan melihat repository sebagai kumpulan folder.

Lihat repository sebagai kumpulan capability.

---

## Capability

Capability dapat berada pada:

- Runtime
- Service
- Provider
- Presentation
- Guardian
- Connector
- Workflow

Capability bukan ditentukan oleh nama package.

---

## Runtime

Runtime bukan tujuan.

Runtime adalah tempat capability hidup.

Runtime tidak harus selalu aktif.

---

## Activation

Activation lebih penting daripada jumlah runtime.

Runtime tanpa consumer tidak memberikan nilai operasional.

---

## Wiring

Masalah terbesar repository saat ini adalah wiring.

Bukan desain.

Bukan struktur.

Catatan: wiring terbagi menjadi beberapa jalur; bukan satu jalur tunggal.

---

## RuntimeService

Lihat sebagai Gateway.

Bukan sebagai executor.

---

## ExecutionRuntime

Lihat sebagai execution pipeline.

Bukan business logic.

---

## RuntimeCoordinator

Lihat sebagai kernel operasional saat ini untuk sebagian flow.

Bukan desain akhir.

Kurangi consumer, bukan tambah responsibility.

Bukan satu-satunya jalur; Operations/Desktop berjalan tanpa Coordinator.

---

## Operations

Lihat sebagai jalur hidup Desktop/Conversation.

Mandiri: 0 import sam.runtime.

Sudah berjalan lewat Provider.

---

## Dormant Runtime

Jangan dianggap gagal.

Sebagian besar memang menunggu activation.

---

## Engineering Success

Repository dianggap berkembang apabila:

- consumer bertambah
- producer bertambah
- activation bertambah
- coupling berkurang

Bukan ketika:

- runtime bertambah
- folder bertambah
- abstraction bertambah

---

## Pertanyaan yang Harus Selalu Ditanyakan

Sebelum membuat capability baru:

Apakah capability ini sudah ada?

Sebelum membuat runtime baru:

Apakah runtime yang ada belum memiliki consumer?

Sebelum refactor:

Apakah technical debt benar-benar berkurang?

---

## Engineering Insight

Repository SAM sudah kaya capability.

Nilai engineering berikutnya berasal dari menghubungkan capability tersebut menjadi sistem yang benar-benar hidup.

---

## Referensi

MISSION
CONSTITUTION
E0-001
O0-001
D0-001
D1-001
