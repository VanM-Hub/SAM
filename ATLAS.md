# ATLAS

**Status:** Live navigation
**Version:** 1.0
**Date:** 2026-08-03

> **ATLAS adalah "GPS" Project SAM.** Ia menunjukkan apa yang ada di repository,
> menjelaskan hubungan antarbagian, menentukan dokumen authority, memberi urutan
> membaca, dan mengarahkan engineer ke dokumen yang tepat tanpa kebingungan.
>
> **ATLAS bukan dokumen spesifikasi.** Ia tidak berisi isi ADR, Runtime, Constitution,
> atau Specification. Ia hanya menjawab satu pertanyaan:
> *"Kalau ingin mengetahui X, buka dokumen Y."*

---

## 1. Project Overview

**SAM (System Autonomous Monitor)** adalah *Knowledge-Driven Autonomous Operations
Framework* untuk OpenClaw: sebuah sistem yang mengintegrasikan manajemen pengetahuan,
observasi operasional, diagnostik, eksekusi terkelola, verifikasi berkelanjutan,
pembelajaran institusional, dan pemulihan otonom dalam satu kerangka arsitektur.

Unit dasar arsitektur SAM adalah **Citizen**: peserta konstitusional yang memublikasikan
Capabilities, mematuhi Contracts, berpartisipasi dalam Governance, dan tetap auditable.
SAM dibangun di atas prinsip *approval-gated execution*: tidak ada yang dieksekusi
sebelum mendapat persetujuan eksplisit.

---

## 2. Repository Topology

Peta folder tingkat atas — **bukan daftar isi file**:

| Folder / File | Isi (peran) |
|---|---|
| `ATLAS.md` | **Dokumen ini** — navigasi / GPS repository |
| `README.md` | Pintu depan repository |
| `MISSION.md` `VISION.md` `CHARTER.md` `PRINCIPLES.md` `GOVERNANCE.md` | Identitas proyek (Level 1) |
| `docs/` | Seluruh dokumentasi (lihat hierarki Bab 3) |
| `src/` | Implementasi Python (kode) |
| `tests/` | Pengujian |
| `tools/` (jika ada) / `scripts/` | Utilitas & validasi |
| `modules/` | Library keahlian ter-vendor (dependency) — bukan bagian SAM docs |

> `modules/` adalah dependency eksternal yang di-vendor, bukan dokumentasi SAM.
> Jangan diperlakukan sebagai dokumen otoritas proyek.

---

## 3. Authority Hierarchy

Hierarki ini menentukan **siapa yang menang jika terjadi konflik**.
Baca dari atas ke bawah: dokumen di atas lebih tinggi otoritasnya.

```
Mission
   ↓
Vision
   ↓
Constitution          (docs/CONSTITUTION.md)
   ↓
Citizen Specification (docs/CITIZEN_SPECIFICATION.md)
   ↓
Architecture          (docs/architecture/SAM_ARCHITECTURE.md)  + Philosophy (ref)
   ↓
ADR                   (docs/adr/ADR-###_*.md)
   ↓
Specification         (docs/specifications/ + docs/SPECIFICATION_FREEZE.md)
   ↓
Runtime               (docs/runtime/)
   ↓
Compliance            (docs/compliance/)
   ↓
Engineering           (REPOSITORY_CONVENTION.md, CONTRIBUTING.md)
```

> **Citizen Specification** adalah kontrak konseptual antara `Constitution` dan
> seluruh Specification teknis. Ia *bukan* bagian dari kumpulan specification
> teknis, tetapi menjadi landasan bagi semuanya — jembatan dari fondasi
> proyek menuju seluruh spesifikasi turunan.

Setiap dokumen diklasifikasikan sebagai salah satu dari tiga status:

| Status | Arti | Boleh dipakai untuk |
|---|---|---|
| **Live authority** | Otoritas aktif — sumber keputusan saat ini | Implementasi & pengembangan baru |
| **Reference** | Acuan teknis yang masih berguna | Konsultasi, bukan keputusan baru |
| **History** | Arsip — bukan otoritas | Audit, forensik, evolusi desain saja |

### Ringkasan Otoritas per Topik (Authority Map)

| Topik | Authority (Live) |
|---|---|
| Mission | `MISSION.md` |
| Vision | `VISION.md` |
| Charter | `CHARTER.md` |
| Principles | `PRINCIPLES.md` |
| Governance | `GOVERNANCE.md` |
| Constitution | `docs/CONSTITUTION.md` |
| Citizen Specification | `docs/CITIZEN_SPECIFICATION.md` |
| Architecture | `docs/architecture/SAM_ARCHITECTURE.md` |
| Philosophy | `docs/PHILOSOPHY.md` (Reference) |
| Spesifikasi | `docs/specifications/` + `docs/SPECIFICATION_FREEZE.md` |
| Keputusan (ADR) | `docs/adr/ADR-###_*.md` |
| Runtime | `docs/runtime/` (+ `src/sam/`) |
| Compliance | `docs/compliance/` (+ `src/sam/compliance/`) |
| Konvensi Repository | `REPOSITORY_CONVENTION.md` |
| Panduan Kontribusi | `CONTRIBUTING.md` |
| Development | `docs/development/` (Reference) |
| User Guide | `docs/user/` (Reference) |
| Templates | `docs/templates/` (Reference) |
| Arsip | `docs/history/**` (History) |

> Ada hanya **satu** Constitution (`docs/CONSTITUTION.md`) dan **satu** canonical
> architecture (`docs/architecture/SAM_ARCHITECTURE.md`). Dokumen sejenis lain di
> history bukan otoritas aktif.

---

## 4. Reading Paths

Jalur baca untuk tujuan umum — bukan daftar dokumen, melainkan arah.

### ...memahami SAM (onboarding 30 menit)

```
README
  ↓
ATLAS
  ↓
MISSION
  ↓
VISION
  ↓
CHARTER
```

### ...mengubah Runtime

```
ATLAS
  ↓
Runtime          (docs/runtime/)
  ↓
R4  (Reference Runtime Architecture)
  ↓
R5  (Reference Runtime Engineering Model)
  ↓
I-series  (I0..I2 implementations)
  ↓
src/sam/runtime
```

### ...mengubah Compliance

```
ATLAS
  ↓
Compliance       (docs/compliance/)
  ↓
P1  (Runtime Compliance suite)
  ↓
Compliance Engine  (src/sam/compliance/)
  ↓
Checker
```

### ...mengembangkan fitur baru

```
ATLAS
  ↓
Architecture  (docs/architecture/SAM_ARCHITECTURE.md)
  ↓
Engineering   (REPOSITORY_CONVENTION.md, CONTRIBUTING.md)
  ↓
src/
```

### ...membuat keputusan arsitektur baru

```
ATLAS
  ↓
ADR           (docs/adr/)
  ↓
ADR_TEMPLATE  (docs/templates/ADR_TEMPLATE.md)
```

### ...memahami spesifikasi

```
ATLAS
  ↓
Citizen Specification  (docs/CITIZEN_SPECIFICATION.md)
  ↓
Specification         (docs/specifications/)
  ↓
SAM_FRAMEWORK_v1.0_SPECIFICATION
```

---

## 5. Engineering Entry Points

Titik masuk nyata ke kode — bukan penjelasan panjang, hanya peta.

| Entry Point | Lokasi |
|---|---|
| CLI | `src/sam/.../cli/` |
| Desktop / Presentation | `src/sam/presentation/` (+ `src/sam/web/`) |
| Runtime Root | `src/sam/runtime_root/` |
| API | `src/sam/...` (lewat Capability/Registry) |
| Operations | `src/sam/operations/` |

> Implementasi aktual: `src/sam/`. Validasi: `scripts/validation/`.

---

## 6. Runtime Map

Ringkasan 7 Unit Reference Runtime — peta, bukan penjelasan implementasi.

```
Citizen Host
   ↓
Capability Manager
   ↓
Discovery Resolver
   ↓
Contract Enforcer
   ↓
Approval Coordinator
   ↓
Execution Scheduler
   ↓
Audit Recorder
```

Rujukan implementasi: `docs/runtime/` + `src/sam/runtime/`.

---

## 7. History Policy

Seluruh kebijakan arsip dijelaskan pada **`docs/HISTORY_POLICY.md`**.
Intinya: **History bukan authority** — dokumen arsip tidak dipakai untuk implementasi baru,
hanya untuk audit, forensik, evolusi desain, dan referensi keputusan lama.

---

## 8. Maintenance Rules

Aturan menjaga ATLAS agar tetap berguna dan kecil:

1. **Jangan menjelaskan implementasi** — cukup tunjuk dokumen yang benar.
2. **Jangan menyalin Specification, ADR, Runtime, Constitution** — hanya tautkan.
3. **Hanya menunjuk authority** — satu sumber per topik, hindari duplikasi.
4. **Maksimal 10–15 halaman** — jika lebih, kurangi deskripsi, bukan menambah.
5. **ATLAS adalah navigasi (GPS)** — bukan super-document dan bukan dokumentasi teknis.
6. **Perbarui ATLAS setiap kali struktur/authority berubah** — jangan biarkan ketinggalan.
7. **Jika ada dokumen baru, tambahkan ke hierarki** (Bab 3) agar peta tetap utuh.

---

*ATLAS adalah dokumen navigasi tingkat repository.*
*Untuk kebijakan perlakuan dokumen lama, lihat `docs/HISTORY_POLICY.md`.*
