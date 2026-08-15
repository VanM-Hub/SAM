# REPOSITORY_STRUCTURE.md — Peta Struktur Repository (detail)

**Status:** Rujukan struktur repo (detail). **ATLAS menunjuk ke sini** untuk peta folder.
**Prinsip:** Folder/paket/modul/adapter BUKAN identitas governance. Identitas mengikuti domain model & kontrak authoritative.

> Dokumen ini menggantikan kebutuhan menaruh daftar folder satu-per-satu di ATLAS (ATLAS harus tetap ramping).

---

## SEMANTIC MAP (governance identity)

```
SUBJECT
├── CITIZEN — entitas di DALAM governance domain SAM
│     Provider · Runtime · Workflow · Mission · Policy · Capability · Service · Extension
└── WARD — entitas EKSTERNAL yang dipercayakan kpd SAM (observe/protect/govern)

IMPLEMENTATION
├── CORE / PLATFORM — mesin governance SAM
├── CITIZEN IMPLEMENTATION — implementasi Citizen
├── WARD IMPLEMENTATION — adapter/connector/integration
└── MODULE — packaging/operational layer (BUKAN Citizen, BUKAN Ward)
```

> **Folder ≠ Semantic Identity.** Repository structure does not define governance identity.
> A folder/package/module/adapter/provider implementation is not itself a Citizen or Ward.
> Classification follows the authoritative domain model and contracts.

### Contoh canonical

| Entitas | Identity |
|---|---|
| Provider | **Citizen** |
| OpenClaw instance (system eksternal) | **Ward** |
| `src/sam/openclaw/` (kode) | **implementation boundary** (bukan otomatis Ward) |
| OpenClaw adapter/provider implementation | **adapter/integration** (bukan Citizen/Ward) |
| GitHub repository instance | **Ward** |
| GitHub connector | **adapter/integration** |
| SAM GitHub capability | **Capability Citizen** |

---

## Struktur folder (rumpun, bukan daftar 98)

```
src/sam/
├── world (AKTIF, jalur resmi)
│     runtime_service · observation · execution_runtime · presentation
│     web/desktop · knowledge_runtime · workflow_runtime · artifact_runtime
│     memory · policy_runtime · audit_runtime
│
├── 4.0 (SAM 4.0 Federated Governance Platform)
│     operational_intelligence · operational_learning · governed_reasoning
│     autonomous_operations · operational_workspace
│
├── application/   (APPLICATION LAYER M9 — ux/ = product entry point)
├── api/           (REST API host + UI canonical)
│
├── 5.x (SAM 5.x Universal Governance)
│     universal_ai · universal_tool · universal_agent · universal_workflow
│     enterprise_governance · adaptive_governance
│
├── M14 (delegated authority)  delegated_authority · environment
│
├── legacy (HISTORIS)   operations · execution · runtime · reasoning
├── backlog (belum aktif)   intelligence_runtime · agent · model_runtime · ...
└── infra/core   cli · api · launcher · core · storage · telemetry · contracts · ...
```

---

## Peta ownership semantik lengkap (13 kategori)

Untuk **klasifikasi semantic ownership per-folder** (98 folder → 13 kategori, UNKNOWN diizinkan),
lihat dokumen authority-nya:

→ **`docs/architecture/Semantic_Repository_Map.md`**

ATLAS tidak menyalin daftar itu; ATLAS hanya menunjuk ke sini, dan dokumen ini menunjuk ke peta ownership.

---

## Aturan navigasi (When in doubt → inspect repository)

```
ARCHITECTURAL QUESTION  ("apa sebenarnya X di SAM?")
        │
        ▼
Apakah definisi eksplisit di authoritative documentation?
        │
   ┌────┴────┐
   │         │
  YES        NO
   │         │
   ▼         ▼
ikuti      inspect repository
definition │
           ├── source
           ├── tests
           ├── contracts
           ├── decisions
           └── actual state
                │
                ▼
           jangan berasumsi
```

> Jangan menjawab "apa itu X" berdasarkan nama folder, ingatan percakapan, atau asumsi.
> Periksa ATLAS → lalu sumber otoritatif/repo bila masih ambigu.
