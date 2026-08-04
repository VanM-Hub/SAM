# ATLAS v2.0 — Repository Navigation System (GPS)

**Versi:** 2.0 · **Status:** Live navigation · **Owner:** Project SAM

> ATLAS adalah **GPS** seluruh Project SAM. Ia menjawab:
> *"Saya di mana?", "Untuk ubah X mulai dari mana?", "Apa authority-nya?", "Apa yang tidak boleh kusentuh?"*
> ATLAS **bukan** README, bukan documentation index, bukan arsitektur, bukan spesifikasi.
> Ia hanya menunjukkan **arah**, tidak mengulang isi dokumen lain.

---

## 1. Project Identity

```
MISSION (MISSION.md — kenapa SAM ada)
   │
   ▼
VISION (VISION.md — ke mana SAM menuju)
   │
   ▼
CHARTER (CHARTER.md — mandat/wewenang)
   │
   ├── PRINCIPLES (PRINCIPLES.md — prinsip)
   └── GOVERNANCE (GOVERNANCE.md — pembagian wewenang)
        │
        ▼
CONSTITUTION (docs/CONSTITUTION.md — apa yang TIDAK boleh berubah)
        │
        ▼
CITIZEN SPEC (docs/CITIZEN_SPECIFICATION.md — jembatan Constitution→Spec)
        │
        ▼
ARCHITECTURE (docs/architecture/SAM_ARCHITECTURE.md — Citizen, layering)
```

**Baca 1× untuk memahami identitas SAM** (30 menit): `MISSION → VISION → CHARTER → docs/CONSTITUTION.md → docs/architecture/SAM_ARCHITECTURE.md`.

> SAM = platform **governance** untuk sistem cerdas. Bukan membangun AI; mengatur bagaimana AI
> ditemukan/diseleksi/dikoordinasikan/disetujui/dieksekusi/diaudit. Detail ada di dokumen masing-masing — ATLAS tidak mengulang.

---

## 2. Repository Topology

```
SAM/          ← akar repo
│
├── *.md (root)        ← IDENTITAS + NAVIGASI (MISSION, VISION, CHARTER, ATLAS, README, ROADMAP...)
├── src\sam\           ← IMPLEMENTASI (72 folder capability/runtime — "dunia hidup")
├── tests\             ← PENGUJIAN (unit/integration/presentation/e2e/legacy)
├── docs\              ← DOKUMENTASI (authority + history)
├── scripts\           ← VALIDASI & tooling (validate_*, launcher)
├── data\              ← migrasi SQL (001..00N)
└── modules\           ← dependency extern ter-vendor (BUKAN docs SAM)
```

**`docs\` — peta navigasi dokumentasi:**

```
docs\
├── CONSTITUTION.md          ← satu-satunya Constitution (canonical)
├── CITIZEN_SPECIFICATION.md ← jembatan Constitution → spec
├── PHILOSOPHY.md            ← reference (filosofi)
├── SPECIFICATION_FREEZE.md  ← batas spesifikasi
├── architecture\            ← Architecture canonical + rulebook + DTO catalog
├── adr\                     ← SATU ADR = SATU file (ADR-###)
├── specifications\          ← spec resmi per-fungsi (approval, audit, contract...)
├── runtime\                 ← Reference Runtime (R-series + I-series + E-series + P)
├── compliance\              ← Compliance suite (P1-001..P1-008)
├── design\                  ← design docs & design recovery (D0,D1,E0,O0,A0,C0,G,R...)
├── releases\                ← release notes + manifest (CURRENT version)
├── history\                 ← ARSIP (report, sprint, program, legacy) — BUKAN authority
└── (lainnya: core, models, security, operations, knowledge, user, templates...)
```

**`src\sam\` — peta navigasi implementasi (72 folder; kelompok utama):**

```
src\sam\
│
├── WORLD BARU (jalur activation resmi, S01-S10):
│   ├── runtime_service\      ← GATEWAY (WebRuntimeService + consumers: knowledge/workflow/artifact/memory/policy/audit)
│   ├── execution_runtime\    ← Execution Runtime (preview, ADR-024)
│   ├── presentation\         ← Presentation Layer (entry UI; memakai RuntimeService)
│   ├── web\                  ← Web Dashboard (entry, memakai jalur resmi)
│   └── knowledge_runtime\ workflow_runtime\ artifact_runtime\ memory\
│       policy_runtime\ audit_runtime\  ← 6 capability AKTIF (Activation Pattern)
│
├── WORLD LAMA (legacy/historis):
│   ├── operations\           ← terbesar; jalur legacy (conversation_api, brain)
│   ├── execution\            ← legacy execution (Deprecate; jalur resmi = execution_runtime)
│   ├── runtime\              ← RuntimeCoordinator + kernel legacy
│   ├── reasoning\            ← reasoning legacy (Deprecate; terikat execution/)
│   └── guardian\ approval\ autonomous\ cognitive\ ...
│
├── ARCH BACKLOG (belum aktif; butuh AD):
│   └── intelligence_runtime\ agent\ model_runtime\ connectors\ orchestrator\ skills\...
│
└── INFRA/CORE: cli\ api\ launcher\ core\ storage\ telemetry\ events\ contracts\ dos\ models\...
```

---

## 3. Authority System (hierarchy + siapa boleh mengubah siapa)

```
 MISSION ─────────────  TIDAK BOLEH diubah oleh siapa pun (kecuali amandemen konstitusional)
    ▼
 VISION
    ▼
 CONSTITUTION ───────── "apa yang tidak pernah berubah" — Engineering TIDAK boleh mengubahnya
    ▼
 CITIZEN SPEC
    ▼
 ARCHITECTURE ──────── Engineering TIDAK boleh mengubah; keputusan di sini = Architecture Session
    ▼
 ADR ──────────────── keputusan arsitektur ter-record; ubah via ADR baru, bukan edit
    ▼
 SPECIFICATION ─────── SPECIFICATION_FREEZE — tidak diubah utk memudahkan implementasi
    ▼
 REFERENCE RUNTIME ──── (docs/runtime)
    ▼
 COMPLIANCE ────────── (docs/compliance)
    ▼
 ENGINEERING ───────── implementasi & activation — zona kerja engineer
    ▼
 IMPLEMENTATION (src/) ── yang paling sering diubah
    ▼
 COMPLIANCE CHECK / CERTIFICATION ── validasi akhir
```

**Aturan "siapa mengubah siapa":**

| Layer | Boleh diubah oleh | TIDAK boleh diubah oleh |
|---|---|---|
| Mission | Amandemen konstitusional | Source code, Engineering |
| Constitution | Amandemen | Engineering, Runtime |
| Architecture | Architecture Session (keputusan arsitektur) | Engineering, Runtime |
| ADR | ADR baru (record) | Edit langsung |
| Specification | Process spesifik (freeze) | Engineering "biar gampang" |
| Runtime/Code | Engineering | Mission/Architecture |
| History | No (arsip) | Siapa pun (read-only audit) |

---

## 4. Knowledge Flow (dari ide → operasional → history)

```
 IDEA ──────────┬───────────────
               ▼
           MISSION ─ (apakah ini mendukung mission?)
               ▼
           VISION / CHARTER
               ▼
           ARCHITECTURE ─ (masuk layer mana?)
               ▼
            ADR ────────── 1 keputusan = 1 file
               ▼
        SPECIFICATION ──── freeze
               ▼
         REFERENCE RUNTIME (docs/runtime)
               ▼
        ENGINEERING / CODE (src/) ─── Activation Pattern (Consumer→Registry→Bridge)
               ▼
        COMPLIANCE / CERTIFICATION (99 checker, verdict)
               ▼
           OPERATIONAL (jalur resmi aktif)
               ▼
            HISTORY (docs/history — arsip, BUKAN authority)
```

> Setiap perubahan hidup: lahir dari Mission → mengalir ke kode → diverifikasi compliance → aktif → lalu jadi history.

---

## 5. Engineering Flow (kalau mau mengubah X, mulai dari mana)

```
 MAU TAMBAH RUNTIME CAPABILITY:
 ADR-ENG-002 (Activation Pattern) → sudah ada registry? bridge? DI?
   → docs/runtime R4/R5/I-series → src/sam/... → Consumer + Registry + Bridge
   → LULUS AD-ENG-001 (Activation Readiness)? ya = Engineering Session; tidak = Architecture Backlog

 MAU BUAT PROVIDER:
 SAM_ARCHITECTURE (Provider/Connector layer) → ADR-006 (External Access)
   → src/sam/providers/ + connector → ExecutionRuntime (preview, ADR-024)
   → LARANG: provider baru tanpa consumer (EC/AD-ENG)

 MAU PERBAIKI DASHBOARD:
 docs/architecture (Entry_Points) → src/sam/presentation/ → src/sam/web/ (template)
   → Presentation PRINCIPLE (Article XVI): tanpa business logic
   → hubungkan via RuntimeService, bukan coordinator langsung

 MAU PERBAIKI PRESENTATION:
 Article XVI (Presentation Principle) → src/sam/presentation/ + runtime_service (gateway)
   → presentation hanya visualisasi/komposisi; komunikasi via RuntimeService

 MAU PERBAIKI COMPLIANCE:
 docs/compliance (P1-001..008) → src/sam/compliance/ → scripts/validation/
   → jangan ubah checkers tanpa baseline (P1-007)
```

---

## 6. Runtime Navigation (hubungan, bukan isi)

```
 REFERENCE RUNTIME PRODUK ENGINEERING:
 Reference Runtime (ide)
   → R4 (Architecture) → R5 (Engineering Model)
   → I-series (I0 blueprint → I1 skeleton → I2 implementation 7 unit)
   → P0 (Certification)
   → E1 (Composition Root: runtime_root) → E1-002 (Executable)

 IMPLEMENTASI RUNTIME:
 docs/runtime ──► src/sam/runtime_root (Composition Root, 7 unit)
                    ──► src/sam/runtime_kernel (kernel flat 69 file)
                    ──► src/sam/runtime (RuntimeCoordinator — legacy)
                    ──► src/sam/presentation (UI entry)

 Jalur activation (jalur RESMI sekarang):
 Conversation → runtime_service (gateway) → execution_runtime (preview)
   → Consumer → Registry → Bridge → STOP
```
> Rintis diri: "Runtime" yang mana? Reference (docs/runtime), kernel (runtime_kernel),
> coordinator (runtime), atau activation (runtime_service/execution_runtime)? — ATLAS menunjuk, bukan menjelaskan isi.

---

## 7. Operational Flow (posisi SAM sekarang)

```
 MISSION → ARCHITECTURE → ENGINEERING → ACTIVATION → OPERATIONAL RUNTIME → PRODUCTION
                                                        (jalur resmi)        (ADR-024 batas)

 POSISI SEKARANG (2026-08, pasca S01-S10):
   ● Foundation + 6 capability AKTIF via Activation Pattern (Knowledge/Workflow/
     Artifact/Memory/Policy/Audit)
   ● ExecutionRuntime = PREVIEW-ONLY (ADR-024) — belum production
   ● Model/Intelligence/Agent = Architecture Backlog (belum layak activation)
   ● Web Dashboard + Presentation berjalan di jalur resmi (post-fix S10)
   ● Fase: Product Integration & Operationalization (Tahap 2), menuju production
```
> SAM kini di **jalur resmi aktif**, tapi **bukan production execution** (ADR-024, preview-only).
> Menuju Production = butuh keputusan ADR-024 diubah (Architecture Session), bukan Engineering.

---

## 8. Reading Paths (flowchart tujuan, bukan daftar)

```
 INGIN MENGERTI SAM           → MISSION → VISION → CHARTER → CONSTITUTION → SAM_ARCHITECTURE
 INGIN MENJADI KONTRIBUTOR    → README → ATLAS → GOVERNANCE → CONTRIBUTING → REPOSITORY_CONVENTION
 INGIN PERBAIKI RUNTIME       → docs/runtime R4/R5 → I-series → src/sam/runtime_root|runtime_kernel → compliance
 INGIN BUAT RUNTIME CAPABILITY→ AD-ENG-001/002/003 → docs/runtime → src/sam → Activation Pattern → EC-025
 INGIN PERBAIKI PRESENTATION  → Article XVI → src/sam/presentation → runtime_service
 INGIN BUAT DASHBOARD         → Entry_Points → src/sam/presentation + web → Article XVI
 INGIN MENGERTI CITIZEN       → docs/CITIZEN_SPECIFICATION.md → SAM_ARCHITECTURE (Citizen)
 INGIN MENGERTI COMPLIANCE    → docs/compliance P1-001 → src/sam/compliance → scripts/validation
 INGIN MENGERTI RUNTIME       → ATLAS §6 → docs/runtime R4/R5/I-series → runtime_root
 INGIN MENGERTI ENGINEERING   → ATLAS §5 → docs/design → AD-ENG-* → reports (histori sesi)
```

---

## 9. Repository Rules (aturan navigasi — yang tidak boleh dilanggar)

```
 • Source code TIDAK boleh mengubah Mission/Constitution/Architecture.
 • Engineering TIDAK boleh mengubah Constitution; keputusan arsitektur = Architecture Session.
 • History BUKAN authority (read-only; hanya audit/forensik).
 • ADR BUKAN Specification (ADR = keputusan; spec = kontrak).
 • Runtime BUKAN Mission (runtime menjalankan, bukan mendefinisikan).
 • Presentation BUKAN business logic / BUKAN coordinator (Article XVI).
 • Provider BUKAN governance (governance di atas provider).
 • Approval TIDAK boleh dilewati; eksekusi preview-first (ADR-024).
 • Capability TIDAK boleh diaktifkan jika gagal AD-ENG-001/002/003 (→ Architecture Backlog).
 • Catatan internal engineer tidak pernah di-commit. History/laporan publik → docs/history.
 • Jangan tambah runtime baru sebelum capability existing punya consumer.
```

---

## 10. Maintenance (menjaga ATLAS tetap kecil & akurat)

**Ukuran:** maks ~15 halaman — jika lebih, potong deskripsi, bukan menambah.

**Isi ATLAS hanya:**
- Arah (→ ke dokumen/folder mana), diagram, hubungan, rule.
- **Bukan** isi/ringkasan Mission/Runtime/ADR.

**Siapa yang boleh mengubah ATLAS:**
- **Chief Repository Architect** (perubahan struktur/navigasi besar).
- **Maintenance Session** (update kecil: folder baru, authority baru, status sesi).

**Kapan diperbarui (auto-ritual):**
- Ada folder/dokumen/runtime baru → tambah ke Topology (§2) & Reading Path (§8).
- Authority berubah / ADR baru → update Authority System (§3).
- Status aktivasi berubah → update Operational Flow (§7) + EC-025.
- Jangan biarkan ATLAS tertinggal setelah sesi engineering (cegah "README outdated").

**Uji keakuratan tiap update:** *"Bisakah engineer baru menavigasi ke dokumen/folder yang tepat hanya dari ATLAS, tanpa tebak-tebakan?"* — jika ya, ATLAS sehat.

---

*ATLAS adalah GPS. Dokumen lain adalah isi. ATLAS menunjuk jalan, tidak membawa muatan.*
*Untuk kebijakan arsip & dokumen lama: docs/HISTORY_POLICY.md.*
