# EC-010 — Engineering Decision Memory

## Tujuan

Menyimpan keputusan engineering yang telah dianggap final sehingga tidak diperdebatkan kembali pada sesi berikutnya.

---

## Keputusan 001

Architecture selesai.

Tidak dilakukan redesign.

---

## Keputusan 002

Foundation Freeze.

Mission, Constitution, Architecture dan Specification tidak diubah untuk mempermudah implementasi.

---

## Keputusan 003

Runtime baru tidak dibuat.

Capability yang sudah ada harus digunakan terlebih dahulu.

---

## Keputusan 004

RuntimeService tetap menjadi Gateway.

Tidak menjadi Executor.

Tidak menjadi Decision Engine.

---

## Keputusan 005

ExecutionRuntime tetap menjadi jalur execution resmi.

Tidak dibuat execution pipeline baru.

---

## Keputusan 006

RuntimeCoordinator tidak dipecah hanya karena ukurannya besar.

Prioritas adalah mengurangi consumer melalui activation.

Coordinator bukan satu-satunya jalur; sebagian consumer sudah di jalur Operations.

---

## Keputusan 007

Presentation tetap bebas dari Business Logic.

---

## Keputusan 008

Composition Root tetap tunggal.

Tidak membuat composition baru pada Presentation.

---

## Keputusan 009

Approval tetap menjadi boundary utama.

Tidak ada jalur execution tanpa approval resmi.

---

## Keputusan 010

Provider tetap provider.

Governance tetap berada di atas provider.

---

## Keputusan 011

Engineering berikutnya fokus pada Activation.

Bukan pada penambahan capability.

---

## Keputusan 012

Technical Debt dikurangi melalui integrasi nyata.

Bukan melalui refactor kosmetik.

---

## Keputusan 013

Consumer lebih penting daripada jumlah runtime.

Runtime tanpa consumer bukan prioritas untuk diperluas.

---

## Keputusan 014

Semua implementasi baru harus mengikuti:

Presentation
↓
RuntimeService
↓
ExecutionRuntime
↓
Provider

---

## Keputusan 015

Repository diukur dari kemampuan operasional, bukan dari jumlah dokumen.

---

## Engineering Insight

Dokumen desain dapat berubah melalui ADR.

Keputusan engineering di atas dianggap berlaku sampai ada keputusan arsitektur baru yang secara eksplisit menggantikannya.

---

## Referensi

MISSION
CONSTITUTION
SPECIFICATION_FREEZE
ADR-000 ~ ADR-007
D0-001
D1-001
