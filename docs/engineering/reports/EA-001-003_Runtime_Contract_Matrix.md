# EA-001-003 — Runtime Contract Matrix (Program B)

**Program:** MISSION-2B / Program B · **Package:** EA-001 · **WP:** WP-03 Contract Discovery
**Mode:** Read-only · **Authority:** Lead Engineer · **Tanggal:** 2026-08-08
**Catatan:** Identifikasi kontrak runtime (public API / interface / activation entry / dependency contract). **Bukan implementasi.**

---

## 1. Ringkasan

Seluruh 12 Runtime memiliki artefak kontrak yang teridentifikasi (contract/descriptor/interface). Contract matrix berikut mencatat **kontrak publik** tiap runtime berdasarkan file kontrak yang ADA di folder masing-masing.

## 2. Contract Matrix

| Runtime | Public API / Contract File | Interface | Activation Entry |
|---|---|---|---|
| Mission Runtime | `mission_descriptor.py`, `resource_descriptor.py` | (via descriptor) | `mission_runtime/__init__.py` |
| Workflow Runtime | `workflow_contract.py`, `workflow_descriptor.py` | (via contract/descriptor) | `workflow_runtime/__init__.py` |
| Policy Runtime | `policy_contract.py`, `policy_descriptor.py` | (via contract/descriptor) | `policy_runtime/__init__.py` |
| Registry Runtime | *(registry facade, kernel)* | `sam.runtime.registry` facade | `runtime/registry/__init__.py` |
| Approval Runtime | `coordinator_interface.py` | **ADA** (`interfaces/`) | `runtime/approval_coordinator/__init__.py` |
| Execution Runtime | `execution_contract.py`, `execution_descriptor.py` | (via contract/descriptor) | `execution_runtime/__init__.py` |
| Audit Runtime | `audit_contract.py`, `audit_descriptor.py` | (via contract/descriptor) | `audit_runtime/__init__.py` |
| Artifact Runtime | `artifact_contract.py`, `artifact_descriptor.py` | (via contract/descriptor) | `artifact_runtime/__init__.py` |
| Knowledge Runtime | `knowledge_contract.py`, `knowledge_descriptor.py` | (via contract/descriptor) | `knowledge_runtime/__init__.py` |
| Memory Runtime | `memory_contract.py`, `memory_descriptor.py` | (via contract/descriptor) | `memory/__init__.py` |
| Provider Runtime | `provider_contract.py`, `provider_descriptor.py` | **ADA** (`interfaces/`) | `providers/__init__.py` |
| Runtime Service | `contract.py`, `descriptor.py`, `plugin_descriptor.py`, `secret_descriptor.py` | (via contract/descriptor) | `runtime_service/__init__.py` |

## 3. Dependency Contract (kontrak lintas runtime)

Berdasarkan analisis import (WP-04), kontrak dependency utama yang teridentifikasi:

- **Runtime Service** → bergantung (import) pada: **Audit, Memory, Policy, Artifact, Workflow, Knowledge, Execution** (sebagai orchestrator, konsisten dengan Constitution).
- **11 runtime lainnya** → **independen** (tidak ada import ke runtime lain dalam scope 12). Konsisten dengan Constitution Article IX "Runtime Independence".

## 4. Activation Entry

Setiap runtime memiliki **entry module** = `__init__.py` dari folder root-nya. Runtime yang merupakan kernel subsystem (Registry, Approval) diaktifkan melalui facade/compatibility module (`sam.runtime.registry`, `sam.runtime.approval_coordinator`).

## 5. Verifikasi Kontrak

- **Semua 12 runtime memiliki minimal 1 artefak kontrak** (contract/descriptor/interface) ✔
- **Approval & Provider** memiliki subfolder `interfaces/` eksplisit ✔
- Kontrak terdokumentasi (bukan implementasi) — hanya identifikasi lokasi & jenis kontrak ✔

---

*— Akhir EA-001-003 —*
