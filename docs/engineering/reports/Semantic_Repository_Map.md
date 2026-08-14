# Semantic Repository Map — SAM

**Status:** Rujukan semantic ownership setiap folder domain `src\sam\*`.
**Tanggal:** 2026-08-14
**Metode:** Klasifikasi berdasar **isi & penggunaan nyata** (semantic ownership), BUKAN kecocokan nama folder dengan CitizenKind.
**Pemicu revisi:** Koreksi Aster terhadap audit sebelumnya (yang keliru memetakan folder → Citizen berdasarkan nama). Audit sebelumnya ditarik.

---

## 1. Mengapa pendekatan ini berbeda dari audit sebelumnya

Audit awal menandai cluster seperti `runtime/runtime_kernel/runtime_root/runtime_service` dan `memory/knowledge_runtime` sebagai "duplikat" hanya karena kemiripan nama/struktur. **Itu keliru.** Pemeriksaan berdasar isi & penggunaan menunjukkan:

- `runtime_kernel` (226 referensi import), `runtime_root` (26), `runtime_service` (165) — **semuanya di-import aktif oleh modul lain**. Bukan orphan/duplicate; 4 peran berbeda.
- `memory` vs `knowledge_runtime` — **bukan duplikat identik**:
  - `memory` = Memory Runtime (Sprint 173–175, Phase XVII): entitas Entry/Record/Scope/Tag.
  - `knowledge_runtime` = Knowledge Runtime (Sprint 181–183, Phase XVIII): entitas Fact/Relation/Context/Knowledge.
  - Keduanya berbagi *pola* build/catalog/certification, tapi *isi & domain berbeda*, dan keduanya dipakai (memory: 112 ref; knowledge_runtime: 85 ref).

**Aturan baru (dipegang):** Sebuah folder **tidak menjadi Citizen hanya karena namanya sama dengan CitizenKind**, dan **tidak menjadi duplicate hanya karena namanya mirip folder lain**. Yang menentukan = semantic ownership + penggunaan nyata.

---

## 2. Vocabulary canonical (acuan)

```
                     SUBJECT
                        │
          ┌─────────────┴─────────────┐
          │                           │
       CITIZEN                       WARD
          │                           │
  internal governance        entrusted external subject
          │                           │
 ┌────────┼────────┐          ┌───────┼─────────┐
 │        │        │          │       │         │
provider runtime mission      PC    OpenClaw   GitHub
workflow policy capability   Docker  service   repository
service extension
```

- **CitizenKind (8, setara):** runtime, provider, workflow, mission, policy, capability, service, extension.
- **Hanya node di bawah Citizen yang memakai CitizenKind.** Ward punya vocabulary sendiri.
- **Provider tetap Citizen** — yang menentukan relasi governance, bukan lokasi fisik. Jangan ubah provider → Ward.
- **OpenClaw = Ward** (instance yang dititipkan user). **OpenClawProvider = Citizen** (saat SAM memakainya sebagai provider). Dua relasi tak boleh dicampur.
- **Module** = lapisan packaging/platform/documentation — bukan Citizen, bukan Ward. `modules/` berada di sini.

---

## 3. Klasifikasi folder domain `src\sam\*` (13 kategori)

Kategori: **1** CITIZEN DOMAIN · **2** WARD DOMAIN · **3** CORE GOVERNANCE · **4** APPLICATION · **5** EXECUTION · **6** INFRASTRUCTURE · **7** MODEL · **8** ADAPTER · **9** REPOSITORY · **10** RUNTIME SUBSYSTEM · **11** TEST SUPPORT · **12** LEGACY/DUPLICATE · **13** UNKNOWN.

> **UNKNOWN diperbolehkan.** Jangan memaksakan folder masuk kategori agar tabel terlihat rapi.

| Folder src\sam | Kelas | Bukti semantic ownership (ringkas) | Status canonical |
|---|---|---|---|
| `providers` | 1 Citizen | Registry provider (anthropic, deepseek, gemini, ollama, openai, docker, filesystem, shell, sqlite...) | canonical |
| `ward` | 2 Ward | Tata kelola Ward (identity/entrustment/governance/registry/capability/adapters) | canonical |
| `openclaw` | 2+1 Ward/Citizen | Koneksi/health/log OpenClaw; berpotensi Provider bila dipakai SAM | canonical (dual) |
| `runtime` | 10 Runtime-subsystem | RuntimeState, Coordinator, Bootstrap, workflow, recovery | canonical |
| `runtime_kernel` | 10 Runtime-subsystem | Kernel runtime (226 ref): conversation_*, health_*, scheduler, event_bus, security, telemetry | canonical |
| `runtime_root` | 3 Core/assembly | Composition Root (RuntimeBuilder→RuntimeRoot); 26 ref | canonical |
| `runtime_service` | 4 Application/service | Entry point service (165 ref); "Sprints 261-271 v27" | canonical |
| `execution` | 5 Execution | adapters/connectors/dispatch/engine/providers/runtime (104 py) | canonical |
| `execution_runtime` | 10 Runtime-subsystem | execution engine, approval_gate, pipeline, credential boundary (99 py) | canonical |
| `operations` | 5 Execution | brain/engine/models/orchestrator/providers/rca/reasoning (350 py) | canonical |
| `connectors` | 8 Adapter | connector bridge | canonical |
| `memory` | 7+10 Memory domain | Memory Runtime (Sprint 173-175); 112 ref; entitas Entry/Record/Scope/Tag | canonical |
| `knowledge_runtime` | 7+10 Knowledge domain | Knowledge Runtime (Sprint 181-183); 85 ref; entitas Fact/Relation/Context | canonical |
| `cognition` | 7 Model | CognitiveState, WorkingMemory, manager, session | canonical |
| `cognitive` | 3 Core/governance | Goal, Goal Tree, Autonomy Levels, Cognitive Budget, Self-Healing | canonical |
| `cognitive_runtime` | 10 Runtime-subsystem | Menyatukan output runtime → representasi kognitif (bukan AI/inferensi) | canonical |
| `intelligence` | 7 Model | Incident, RootCause, Recommendation, Detector, RCA, recommender | canonical |
| `intelligence_runtime` | 10 Runtime-subsystem | Registry→Graph→Context→Validation→Assembly→Report (preview-only) | canonical |
| `governance_intelligence` | 3 Core | analyzers, api_v2, reasoning, recommendation, reference_graph, trust (42) | canonical |
| `citizen` | 1 Citizen | Bounded context Citizen (registry/identity/collaboration/federation/ecosystem) | canonical |
| `mission` | 1 Citizen | Mission | canonical |
| `mission_runtime` | 10 Runtime-subsystem | Mission runtime (70 py) | canonical |
| `mission_cognition` | 7 Model | Mission cognition (result, runtime) | canonical |
| `policy_runtime` | 10 Runtime-subsystem | Policy citizen runtime | canonical |
| `workflow` / `workflow_runtime` | 1+10 | Citizen Workflow + runtime | canonical |
| `service` | 1 Citizen | Citizen Service | canonical |
| `compliance` | 3 Core | Kepatuhan lintas (86 py) | canonical |
| `approval` | 3+5 Core/Execution | Approval, delegation, policy, workflow (49 py) | canonical |
| `autonomy` / `autonomous` / `autonomous_operations` | 3+5 Core/Execution | Autonomy, escalation, recovery ops | canonical |
| `autonomy_runtime` | 10 Runtime-subsystem | Autonomy runtime (60 py) | canonical |
| `governed_reasoning` | 5 Execution | LLM abstraction, reasoning, confidence, compliance (19) | canonical |
| `delegated_authority` | 3 Core | M14 delegated authority (authority/escalation/evaluation/recovery/guardian) | canonical |
| `guardian` | 2+3 Ward/Core | Guardian (77 py), live self-healing | canonical |
| `environment` | 10 Runtime-subsystem | Environment adaptive (providers, pipeline, graph, remediation) | canonical |
| `recovery` | 5 Execution | Recovery | canonical |
| `healing` | 3 Core | Self-heal reflection | canonical |
| `adaptive_governance` | 3 Core | Adaptive certification, impact, learning, recommendation | canonical |
| `enterprise_governance` | 3 Core | Enterprise policy, multitenant, org foundation | canonical |
| `application` | 4 Application | Lapisan aplikasi/UX (15 py) | canonical |
| `api` | 4 Application | REST routes/presentation/static | canonical |
| `presentation` | 4 Application | Dashboard/UI/viewmodel | canonical |
| `model_runtime` | 10 Runtime-subsystem | Model runtime (89 py) | canonical |
| `observation` | 3 Core | Operational learning, publication, recommendation | canonical |
| `operational_*` (brain/intelligence/learning/workspace/alerting) | 3+5 Core/Execution | Operasional SAM | canonical |
| `cli`, `sdk`, `devx`, `launcher`, `desktop` | 4 Application | Developer/user surface | canonical |
| `persistence`, `storage` | 9 Repository | Penyimpanan, migrations | canonical |
| `core`, `platform`, `contracts` | 3 Core | Fondasi | canonical |
| `cluster`, `federation`, `collaboration` | 3 Core | Federasi/kolaborasi | canonical |
| `events`, `telemetry`, `reporting`, `render` | 6 Infrastructure | Infrastruktur | canonical |
| `iam` | 3 Core | Identity/access | canonical |
| `dos` | 3 Core? | (perlu cek isi) | UNKNOWN |
| `web` | 6 Infrastructure | static/templates | canonical |
| `hosting` | 6 Infrastructure | hosting | canonical |
| `confidence` | 7 Model | confidence assessment | canonical |
| `tuning` | 3 Core | tuning | canonical |
| `language` | 7 Model | language | canonical |
| `patterns` | 3 Core | patterns | canonical |
| `recommendations` | 3 Core | recommendation | canonical |
| `strategy` | 3 Core | strategy | canonical |
| `evolution` | 3 Core | evolution | canonical |
| `integration` | 8 Adapter | integration | canonical |
| `plugin` vs `plugins` | 12 LEGACY/DUPLICATE? | Dua nama mirip — **perlu verifikasi isi**; kandidat konsolidasi | **VERIFIKASI** |
| `knowledge` | 7+10 | (6 py) — perlu cek hubungan dgn knowledge_runtime | VERIFIKASI |

> ⚠️ **Baris yang ditandai VERIFIKASI** belum ditentukan statusnya; perlu investigasi isi sebelum diklasifikasi final (sesuai prinsip "jangan paksa rapi").

---

## 4. Masalah sebenarnya (bukan "folder bukan Citizen")

Temuan yang benar dari audit (mendukung Aster):

1. **Vocabulary Citizen|Ward sudah konsisten** setelah M13/M14 (SUBJECT → Citizen | Ward).
2. **Repository structure belum konsisten secara semantic mapping** — bukan karena "98 folder vs 8 CitizenKind", melainkan karena **ada beberapa vocabulary/layer runtime yang tampak sama-sama canonical** dan ownership-nya belum didokumentasikan eksplisit per folder.
3. **Belum ada canonical ownership yang tegas** untuk tiap domain, sehingga bernama-mirip sulit dibedakan canonical vs duplicate.
4. `modules/` = Module layer (bukan Citizen/Ward) — sudah tepat.
5. `plugin` vs `plugins`, `knowledge` vs `knowledge_runtime` — **kandidat yang perlu diverifikasi** (bukan dihapus dulu).

---

## 5. Rekomendasi (sebelum konsolidasi)

1. **Lengkapi Semantic Repository Map ini** — untuk tiap folder pastikan kolom: Apa ini? / Siapa pemilik authority? / Layer? / Citizen|Ward|Core|Infrastructure? / Canonical atau duplicate? / Dipakai siapa? / Boleh dihapus?
2. **Verifikasi kandidat overlap** (`plugin` vs `plugins`, `knowledge` vs `knowledge_runtime`) berdasar isi + referensi, sebelum memutuskan canonical/deprecated.
3. **JANGAN langsung hapus** folder mana pun. Konsolidasi hanya setelah peta selesai & ownership ditetapkan.
4. **Dokumentasikan canonical authority** per domain runtime agar vocabulary idak tampak "bersaing".
5. **Samakan dengan Clean Architecture labels** (canonical / historical / deprecated / delete) setelah audit isi selesai.

---

## 6. Rekap singkat status

| Kategori klasifikasi | Catatan |
|---|---|
| 1 CITIZEN DOMAIN | providers, citizen, mission, workflow, service, policy_runtime |
| 2 WARD DOMAIN | ward, openclaw (dual), guardian |
| 3+5 CORE/EXECUTION | approval, autonomy, delegated_authority, compliance, governance_* |
| 4 APPLICATION | application, api, presentation, cli, sdk, launcher |
| 6 INFRASTRUCTURE | events, telemetry, hosting, web |
| 10 RUNTIME SUBSYSTEM | runtime*, execution_runtime, cognitive_runtime, intelligence_runtime |
| 12 LEGACY/DUPLICATE | `plugin`/`plugins` (VERIFIKASI), `knowledge` (VERIFIKASI) |
| 13 UNKNOWN | `dos` (perlu cek) |

> Status ini **bukan final** untuk baris VERIFIKASI — menunggu investigasi isi.
