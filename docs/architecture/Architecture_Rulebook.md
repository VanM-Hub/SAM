# Architecture Rulebook

> **SAM 1.0 Foundation** - Architecture Governance Baseline
> **File:** `docs/architecture/Architecture_Rulebook.md`

---

## 1. Dependency Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| DR-01 | Subsystem hanya boleh depend ke layer di bawahnya (top-down) | `validate_layers.py` |
| DR-02 | Dilarang import sesama runtime (Guardian → Decision langsung) | `validate_imports.py` |
| DR-03 | Semua komunikasi antar runtime via bridge DTO | Manual review |
| DR-04 | DTO package tidak boleh import runtime package | `validate_imports.py` |
| DR-05 | Infrastructure package tidak boleh import presentation | `validate_imports.py` |
| DR-06 | `asyncio`, `threading`, `multiprocessing`, `socket` hanya di izinkan di `sam/cli/`, `sam/desktop/`, `sam/hosting/`, `sam/web/` | `validate_imports.py` |
| DR-07 | `subprocess` hanya di `sam/launcher/version.py` | `validate_imports.py` |
| DR-08 | Core subsystem harus bebas dari `requests`, `http.client`, `urllib` | `validate_imports.py` |

## 2. DTO Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| DT-01 | Semua DTO harus `@dataclass(frozen=True)` | `validate_dto.py` |
| DT-02 | DTO hanya boleh import dari `typing`, `dataclasses`, `datetime`, `enum` | `validate_dto.py` |
| DT-03 | DTO tidak boleh punya method `process()`, `execute()`, `run()` | `validate_dto.py` |
| DT-04 | DTO harus ada di `__all__` milik package-nya | Manual review |
| DT-05 | DTO tidak boleh punya mutable default value | `validate_dto.py` |

## 3. Runtime Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| RT-01 | Runtime tidak boleh auto-execute action | Manual review |
| RT-02 | Runtime hanya boleh generate output (DTO), tidak boleh invoke eksekusi nyata | Manual review |
| RT-03 | Runtime tidak boleh import sesama runtime | `validate_imports.py` |
| RT-04 | Runtime harus synchronous (tidak pakai async/thread) | `validate_imports.py` |
| RT-05 | Runtime harus deterministic (no random, no time-dependent) kecuali di simulation | Manual review |
| RT-06 | Runtime hanya boleh punya satu entry point (`runtime.py` atau `__init__.py`) | `validate_structure.py` |

## 4. Conversation Bridge Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| CB-01 | Bridge hanya transform DTO, tidak boleh ada business logic | Manual review |
| CB-02 | Bridge harus `@dataclass(frozen=True)` untuk output | `validate_dto.py` |
| CB-03 | Bridge hanya boleh import dari package sendiri + events/base | `validate_imports.py` |
| CB-04 | Bridge tidak boleh import runtime lain | `validate_imports.py` |

## 5. Dashboard Bridge Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| DB-01 | Dashboard bridge hanya produce ExecutionCards | Manual review |
| DB-02 | ExecutionCards harus frozen dataclass | `validate_dto.py` |
| DB-03 | Cards tidak boleh import runtime engine | `validate_imports.py` |
| DB-04 | Dashboard bridge hanya boleh read state, tidak boleh modify | Manual review |

## 6. Approval Boundary

| Rule | Description | Enforcement |
|------|-------------|-------------|
| AB-01 | Approval Runtime adalah subsystem independen, tidak tergabung dengan Decision | Manual review |
| AB-02 | Approval hanya menghasilkan verdict, tidak menentukan eksekusi | Manual review |
| AB-03 | Approval tidak boleh mengubah decision content | Manual review |
| AB-04 | Approval pipeline: Intake → Policy → Workflow → Multilevel → History → Dashboard | `validate_pipeline.py` |

## 7. Execution Boundary

| Rule | Description | Enforcement |
|------|-------------|-------------|
| EB-01 | Execution Runtime hanya preview — tidak boleh eksekusi nyata | Manual review |
| EB-02 | Execution pipeline: Strategy → Resource → Dependency → Timeline → Budget → Quality → Simulation → Assembly | `validate_pipeline.py` |
| EB-03 | Execution hanya menghasilkan ExecutionAssembly, tidak invoke | Manual review |
| EB-04 | Simulation engine tidak boleh mengeksekusi side effects | Manual review |

## 8. Plugin Boundary

| Rule | Description | Enforcement |
|------|-------------|-------------|
| PB-01 | Plugin harus terdaftar di PluginRegistry | Manual review |
| PB-02 | Plugin tidak boleh import runtime secara langsung | `validate_imports.py` |
| PB-03 | Plugin lifecycle: Discover → Validate → Load → Enable → Execute → Disable → Uninstall | Manual review |
| PB-04 | Plugin dijalankan di sandbox (terisolasi dari core) | Manual review |

## 9. Layering Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| LR-01 | Presentation layer (CLI, Desktop, API, Hosting) boleh akses semua layer di bawah | `validate_layers.py` |
| LR-02 | Conversation layer hanya transform — tidak boleh business logic | Manual review |
| LR-03 | Runtime layer hanya interact via DTO | `validate_imports.py` |
| LR-04 | DTO layer tidak boleh import layer di atas | `validate_imports.py` |
| LR-05 | Infrastructure layer (adapter, plugin, persistence) tidak boleh import runtime | `validate_imports.py` |
| LR-06 | Coordinator layer (Runtime Kernel) boleh akses semua layer di bawah | `validate_layers.py` |

## 10. Naming Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| NR-01 | Package name harus snake_case | `validate_structure.py` |
| NR-02 | File name harus singular (`runtime.py`, bukan `runtimes.py`) | `validate_structure.py` |
| NR-03 | Bridge files: `conversation_<subsystem>.py` dan `dashboard_<subsystem>.py` | `validate_structure.py` |
| NR-04 | DTO classes diakhiri dengan DTO atau nama domain (bebas) | Manual review |
| NR-05 | File test: `test_<module>.py` atau `test_sprint<number>.py` | `validate_structure.py` |

## 11. Testing Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| TR-01 | Setiap subsystem harus punya minimal 100 test | `validate_structure.py` (report only) |
| TR-02 | Test tidak boleh bergantung pada network | Manual review |
| TR-03 | Test harus synchronous, deterministic | Manual review |
| TR-04 | Test harus bisa dijalankan tanpa Qt/PySide | Manual review |
| TR-05 | Test harus `pytest` style (class-free, assertion-based) | Manual review |
| TR-06 | Test coverage minimal 80% untuk core logic | Manual review |

## 12. Documentation Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| DR-01 | Setiap subsystem harus punya dokumentasi di `docs/architecture/` | `validate_docs.py` |
| DR-02 | Setiap release harus punya CHANGELOG entry | `validate_docs.py` |
| DR-03 | Setiap release harus punya tag di git | `validate_docs.py` |
| DR-04 | Architecture diagram harus ada minimal 1 per subsystem | `validate_docs.py` |
| DR-05 | README harus up-to-date dengan versi terakhir | `validate_docs.py` |
| DR-06 | pyproject.toml version harus match tag terakhir | `validate_docs.py` |
