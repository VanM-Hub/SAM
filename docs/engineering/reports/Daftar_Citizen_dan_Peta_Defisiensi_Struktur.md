# Daftar Citizen & Peta Defisiensi Struktur SAM

**Status:** Rujukan konsistensi kosakata Citizen / Ward / Module terhadap struktur repo.
**Tanggal:** 2026-08-14
**Bersumber dari:** Audit langsung struktur `src\sam` (98 folder domain) + folder top-level repo.
**Konteks:** Menjawab pertanyaan "apakah struktur repo sesuai dengan definisi Citizen/Ward" dan "folder mana yang belum terdefinisi".

---

## 1. Definisi kosakata (acuan model Citizen/Ward)

Dua sumbu yang **saling tegak lurus**, bukan soal "di dalam/luar" sederhana:

| Istilah | Menjelaskan | Arah | Contoh nyata |
|---|---|---|---|
| **Citizen** | Posisi participant terhadap **governance domain SAM** | *di dalam* governance SAM | provider, runtime, workflow, mission, policy, capability, service, extension |
| **Ward** | Sesuatu **di luar domain SAM** yang dipercayakan owner untuk dijaga | *entrusted external* | PC, OpenClaw, repo GitHub, Docker, layanan eksternal |
| **Module** | Lapisan dokumentasi/manajemen operasional satu platform eksternal, bukan kode governance SAM | di dalam repo, di luar eksekusi | `modules/openclaw/` |

**CitizenKind (8 jenis, setara):** provider, runtime, workflow, mission, policy, capability, service, extension.

**Nuansa penting:** satu layanan eksternal bisa punya **dua relasi** — sebagai **SAM Provider** (Citizen, yang dipakai SAM) dan sebagai **User's Ward** (dijaga SAM). Guardian bekerja pada **Ward**, bukan pada Citizen.

**Posisi OpenClaw:** OpenClaw **bukan Citizen** (berada di luar governance domain SAM — justru menampung SAM). OpenClaw = **Ward** (aset eksternal yang dipercayakan untuk dijaga).

---

## 2. Peta folder top-level repo

| Folder | Isi | Peran dalam kosakata | Status |
|---|---|---|---|
| `src/` | kode inti SAM | Citizen (kode governance) | ✅ Terdefinisi |
| `tests/` | pengujian | — | ✅ Terdefinisi |
| `docs/` | dokumentasi | — | ✅ Terdefinisi |
| `tools/`, `scripts/` | utilitas build/operasional | — | ✅ Terdefinisi |
| `modules/` | **dokumentasi operasional OpenClaw** | **Module** (lapisan ke-3) | ⚠️ Nama folder membingungkan |
| `data/` | `sam.db` (state/audit SAM) | penyimpanan Citizen | ✅ Terdefinisi |
| `workspace/` | sesi, telemetry, manifest | state runtime | ✅ Terdefinisi |
| `memory/`, `logs/` | memori + log | state | ✅ Terdefinisi |
| `examples/`, `_demo/` | contoh/demo | — | ✅ Terdefinisi |
| `build/` (3029 file) | artefak build | — | ⚠️ Artefak tertinggal |
| `_demo/`, `__pycache__/` | sampah | — | ⚠️ Artefak tertinggal |

---

## 3. Peta folder domain `src\sam` (98 folder)

### 3.1 Kolom kategori yang dipakai

| Kategori | Makna |
|---|---|
| **CITIZEN** | Kode yang mewakili salah satu dari 8 CitizenKind |
| **WARD** | Kode tata kelola subjek eksternal yang dipercayakan |
| **CORE/PLATFORM** | Fondasi lintas-domain (bukan citizen spesifik) |
| **DUPLIKAT** | Cluster yang terlihat hasil salin template / tumpang tindih tanggung jawab |
| **MENGAMBANG** | Punya fungsi tapi belum jelas posisi Citizen/Ward/Module |
| **ARTEFAK** | Bukan sumber, sisa build |

---

### 3.2 Kategori CITIZEN (kode yang mewakili CitizenKind)

| Folder | Total `.py` | Catalan |
|---|---|---|
| `providers` | 125 | Provider (Citizen). Termasuk subfolder `openclaw` (provider OpenClaw) |
| `ward` | 14 | Tata kelola Ward (adapters, entrustment, governance, identity, registry) |
| `workflow` / `workflow_runtime` | 6 / 66 | Citizen Workflow |
| `mission` / `mission_runtime` / `mission_cognition` | 3 / 70 / 3 | Citizen Mission |
| `policy_runtime` | 66 | Citizen Policy |
| `capability` (dalam `citizen/`) | — | Citizen Capability |
| `service` | 4 | Citizen Service |
| `runtime` / `runtime_kernel` / `runtime_root` | 169 / 69 / 10 | Citizen Runtime |
| `extension` | — | Citizen Extension (belum teridentifikasi folder eksplisit) |
| `citizen` | 65 | Bounded context Citizen (registry, identity, collaboration, federation, ecosystem) |

### 3.3 Kategori WARD

| Folder | Total `.py` | Catalan |
|---|---|---|
| `ward` | 14 | Tata kelola Ward terdefinisi (bukan jenis citizen) |
| `src\sam\openclaw` | 6 | Kode koneksi/health/log OpenClaw sebagai Ward (connection, discovery, health, logs, models) |

> Catatan: `src\sam\openclaw` (kode) dan `modules\openclaw` (dokumentasi) adalah dua hal berbeda yang menyangkut OpenClaw — kode vs dokumentasi belum disatukan posisinya.

### 3.4 Kategori CORE / PLATFORM (fondasi lintas-domain)

| Folder | Total `.py` | Catalan |
|---|---|---|
| `core` | 17 | inti |
| `platform` | 27 | platform |
| `contracts` | 4 | kontrak |
| `api` / `presentation` | 15 / 66 | antarmuka |
| `cli`, `sdk`, `devx`, `launcher` | 27/10/9/20 | developer experience |
| `application` | 15 | lapisan aplikasi/UX |
| `persistence`, `storage` | 5 / 4 | penyimpanan |
| `events`, `telemetry`, `reporting` | 2/12/3 | infrastruktur |
| `compliance` | 86 | kepatuhan (lintas) |

### 3.5 Kategori DUPLIKAT (cluster salin template / tumpang tindih)

> Pola struktur identik `builder/catalog/certification/dashboard/foundation/integration/model/monitor/runtime` muncul berulang — indikasi hasil salin template, bukan 8 domain independen.

| Cluster | Total `.py` | Gejala |
|---|---|---|
| `memory` **vs** `knowledge_runtime` | 67 **vs** 67 | **Struktur identik** — mana yang resmi? |
| `cognition` **vs** `cognitive` **vs** `cognitive_runtime` | 8 / 7 / 65 | Tiga folder mirip, tanggung jawab tumpang tindih |
| `intelligence` **vs** `intelligence_runtime` | 6 / 41 | Dua folder mirip |
| `runtime` vs `runtime_kernel` vs `runtime_root` vs `runtime_service` | 169/69/10/77 | Empat "runtime" berbeda posisi |
| `audit_runtime` / `artifact_runtime` / `policy_runtime` / `workflow_runtime` / `knowledge_runtime` / `skills` | 66–67 | **Template identik** disalin |
| `governance_intelligence` (42) vs `operational_intelligence` (25) vs `intelligence` (6) | — | Cluster "intelligence" besar duplikatif |

### 3.6 Kategori MENGAMBANG (punya fungsi, posisi Citizen/Ward/Module belum jelas)

| Folder | Total `.py` | Catalan |
|---|---|---|
| `iam` | 6 | identitas/akses — belum jelas posisi |
| `dos` | 3 | — |
| `web` | 2 | — |
| `hosting` | 2 | — |
| `render` | 4 | — |
| `tuning` | 3 | — |
| `language` | 3 | — |
| `confidence` | 2 | — |
| `events` | 2 | — |
| `healing` / `recovery` | 3 / 6 | — |
| `patterns` | 3 | — |
| `recommendations` | 3 | — |
| `strategy` | 5 | — |
| `evolution` | 4 | — |
| `environment` | 12 | — |
| `adaptive_governance` / `enterprise_governance` / `governed_reasoning` | 8/7/19 | — |
| `autonomy` / `autonomous` / `autonomous_operations` | 8/7/19 | — |
| `autonomy_runtime` | 60 | — |
| `delegated_authority` | 17 | M14 — tata kelola delegasi (dekat dengan Ward) |
| `guardian` | 77 | M14 guardian (dekat dengan Ward) |
| `observation` / `operational_*` | 18/… | — |
| `desktop` | 15 | — |
| `cluster`, `federation`, `collaboration` | 8/8/7 | — |
| `plugin` vs `plugins` | 12 / 9 | **duplikat nama** |

### 3.7 Kategori ARTEFAK

| Folder | Catalan |
|---|---|
| `build/` | artefak build (3029 file) |
| `_demo/` | contoh/demo |
| `__pycache__/` | cache |

---

## 4. Temuan utama (jujur)

1. **Jumlah folder domain (98) » 8 CitizenKind** — struktur jauh lebih besar dari definisi kosakata. Mayoritas folder tidak terpetakan eksplisit ke Citizen/Ward/Module.
2. **Cluster "runtime" duplikatif** — `memory`/`knowledge_runtime`, `cognition`/`cognitive`/`cognitive_runtime`, `intelligence`/`intelligence_runtime`, `runtime`/`runtime_kernel`/`runtime_root`/`runtime_service` saling tumpang tindih; banyak pakai template struktur identik (indikasi hasil salin, bukan desain).
3. **`openclaw` dua tempat** — kode (`src\sam\openclaw`) vs dokumentasi (`modules\openclaw`) belum disatukan posisinya secara arsitektural.
4. **Banyak folder "mengambang"** — punya implementasi nyata tapi tidak jelas status Citizen/Ward/Module.
5. **Artefak build tertinggal** (`build/`, `_demo/`, `__pycache__/`) menambah kebisingan.

---

## 5. Rekomendasi (opsional, menunggu keputusan)

- **Konsolidasi cluster runtime duplikatif** — tentukan 1 folder resmi per domain, tandai sisanya sebagai alias/superseded.
- **Pindahkan/petakan folder "mengambang"** ke salah satu dari: Citizen (jika mewakili kind), Ward (jika tata kelola eksternal), Core/Platform (jika fondasi lintas).
- **Satukan posisi `openclaw`** — satu lokasi otoritatif untuk kode vs dokumentasi.
- **Bersihkan artefak build** dari repo (tambahkan ke `.gitignore` bila belum).
- **Jadikan dokumen ini rujukan** untuk memutuskan apakah folder dipertahankan, direposisi, atau dihapus.

---

## 6. Rekap cepat

| Kategori | Jumlah folder | Contoh |
|---|---|---|
| Citizen | ~10 | providers, workflow, mission, policy, runtime |
| Ward | 2 | ward, src\sam\openclaw |
| Core/Platform | ~15 | core, contracts, api, storage |
| Duplikat | ~15 | memory vs knowledge_runtime, cognitive* |
| Mengambang | ~35 | iam, dos, web, tuning, guardian, delegated_authority |
| Artefak | 3 | build, _demo, __pycache__ |
