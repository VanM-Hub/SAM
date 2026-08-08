# ADR — Consolidated Runtime & Platform Architecture Decisions

**Status:** Accepted
**Decision Authority:** Chief Architect
**Scope:** Runtime, Platform, Subsystem, Lifecycle, Recovery, and Federation

---

## Purpose

Menetapkan keputusan arsitektur Runtime dan Platform SAM yang masih berlaku sebagai satu baseline sederhana.

Dokumen ini merupakan konsolidasi keputusan arsitektur yang telah dibuat selama pengembangan SAM.

Dokumen ini **tidak memperkenalkan arsitektur baru**.

Tujuannya adalah mempertahankan keputusan yang masih bernilai tanpa mempertahankan dokumentasi historis yang tidak lagi diperlukan sebagai bagian dari Source Project.

---

# 1. Runtime Independence

Runtime tidak bergantung pada platform hosting tertentu.

Runtime harus dapat dijalankan pada berbagai bentuk host tanpa membawa logika platform ke dalam Runtime.

Perbedaan platform ditangani melalui boundary atau adapter yang sesuai.

Runtime bersifat **headless**.

GUI, CLI, Dashboard, Operations Console, dan client lainnya merupakan client terpisah dan tidak menjadi bagian dari Runtime Core.

---

# 2. Runtime Lifecycle

Runtime memiliki lifecycle yang deterministik.

Perubahan state Runtime dilakukan melalui mekanisme koordinasi lifecycle yang ditetapkan.

Setiap perubahan lifecycle menghasilkan **Lifecycle Event**.

Tidak terdapat perubahan state Runtime yang tidak menghasilkan event lifecycle.

Lifecycle event menjadi dasar bagi observability, telemetry, dan client operasional.

---

# 3. Recovery

Runtime mempertahankan kemampuan recovery melalui konteks operasional yang tersimpan secara bertahap:

```text
Session
   ↓
Snapshot
   ↓
Checkpoint
   ↓
Replay
```

Checkpoint bersifat immutable.

Operasi penting memiliki recovery point.

Apabila proses Replay tidak dapat memulihkan keadaan secara aman, Runtime memasuki `SAFE_MODE`.

---

# 4. Workspace

Workspace menjadi root persistence Runtime.

Data Runtime berada dalam Workspace sehingga keseluruhan state dapat dipindahkan, dibackup, dan direstore sebagai satu kesatuan.

Runtime tidak bergantung pada penyebaran persistence ke lokasi platform-specific di luar Workspace.

---

# 5. Runtime Subsystem Independence

Runtime menggunakan pendekatan **pipeline-oriented dengan subsystem independence**.

Setiap subsystem memiliki:

* responsibility yang jelas;
* public API yang eksplisit;
* pipeline internal;
* test boundary sendiri;
* contract antar-subsystem.

Subsystem tidak bergantung langsung pada implementasi internal subsystem lain.

Tujuannya adalah mempertahankan isolation, testability, dan kemampuan pengembangan independen.

---

# 6. Inter-Subsystem Communication

Komunikasi antar-subsystem dilakukan melalui boundary yang ditetapkan, bukan melalui direct dependency terhadap implementasi internal.

Bridge dan routing mechanism digunakan untuk menghubungkan subsystem.

DTO menjadi contract antar-subsystem.

Transformasi data dilakukan pada boundary yang sesuai.

Dengan demikian subsystem tidak perlu mengetahui struktur internal subsystem lain.

---

# 7. Immutable Contracts

DTO yang digunakan sebagai contract antar-subsystem bersifat immutable setelah diterbitkan.

Perubahan terhadap data dilakukan dengan menghasilkan nilai baru, bukan memodifikasi contract yang telah diterbitkan.

Hal ini menjaga determinisme dan mengurangi side effect antar-subsystem.

---

# 8. Runtime Kernel

Runtime Kernel merupakan lapisan koordinasi Runtime.

Kernel menyediakan fungsi lintas-subsystem seperti:

* coordination;
* routing;
* aggregated health;
* security enforcement;
* lifecycle event distribution;
* telemetry aggregation.

Kernel tidak mengambil alih responsibility subsystem.

Responsibility tetap berada pada subsystem masing-masing.

---

# 9. Approval Boundary

Approval merupakan boundary tersendiri antara keputusan teknis dan policy organisasi.

Approval dapat mencakup:

* policy evaluation;
* workflow evaluation;
* approval chain.

Approval tidak digabungkan dengan Decision Runtime.

Approval tetap menjadi bagian dari governance flow sebelum operasi yang memerlukan authorization dapat dilanjutkan.

---

# 10. Federation Trust

Federation menggunakan **dynamic trust evaluation** berdasarkan observed behaviour dan historical reliability.

Trust dapat berubah berdasarkan evidence perilaku dan mengalami decay.

Trust tidak ditentukan hanya berdasarkan static identity.

Tujuannya adalah agar tingkat kepercayaan merepresentasikan governed conduct, bukan sekadar identitas peer.

---

# 11. Knowledge Sovereignty

Knowledge yang dibagikan antar-cluster memiliki tiga tingkat sovereignty:

```text
PUBLIC
INTERNAL
RESTRICTED
```

Pemilik atau cluster yang mengendalikan knowledge menentukan tingkat sharing.

Knowledge `RESTRICTED` dapat memerlukan authorization atau whitelist eksplisit.

Knowledge sovereignty tetap berada di bawah kendali cluster yang memiliki knowledge tersebut.

---

# 12. Architectural Boundaries

Keputusan-keputusan di atas tidak mengubah Core Runtime Architecture.

Runtime tetap mengikuti prinsip:

```text
Citizen
   ↓
Capability
   ↓
Registry
   ↓
Contract
   ↓
Approval
   ↓
Execution
   ↓
Audit
```

Setiap layer mempertahankan responsibility dan boundary masing-masing.

Tidak boleh dibuat jalur alternatif yang melewati boundary resmi hanya untuk mempermudah implementasi.

---

# 13. Foundation Preservation

Keputusan dalam dokumen ini tidak mengubah:

* Mission;
* Constitution;
* Philosophy;
* Governance;
* Canonical Architecture;
* Canonical Specification;
* Core Runtime Model.

Dokumen ini hanya mempertahankan keputusan arsitektur Runtime dan Platform yang telah diterima sebelumnya dalam bentuk yang lebih sederhana.

---

# 14. Non-Goals

Dokumen ini tidak menentukan:

* bahasa pemrograman;
* framework;
* library;
* struktur source code;
* CI/CD;
* deployment tooling;
* test implementation;
* roadmap;
* sprint;
* task engineering;
* detail API;
* detail database;
* detail implementasi subsystem.

Hal-hal tersebut merupakan domain Development dan Engineering.

---

# 15. Decision

**ACCEPTED**

SAM menggunakan keputusan Runtime dan Platform yang dirangkum dalam dokumen ini sebagai baseline arsitektur operasional.

Keputusan yang tidak lagi relevan, bersifat sementara, bersifat engineering/toolchain, atau hanya diperlukan untuk menjelaskan sejarah pengembangan tidak menjadi bagian dari current architectural surface.

Dokumen historis yang tidak lagi memiliki nilai operasional dapat dihapus dari Source Project.

Konsolidasi ini **tidak menciptakan architecture baru**.

Tujuannya adalah menjaga SAM tetap memiliki fondasi yang cukup untuk berkembang tanpa menjadikan dokumentasi sebagai hambatan terhadap perkembangan berikutnya.

**Foundation tetap utuh.**

**Architecture tetap stabil.**

**Development tetap bebas berkembang di atasnya.**
