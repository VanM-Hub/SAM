# EA-001-004 — Runtime Dependency Matrix (Program B)

**Program:** MISSION-2B / Program B · **Package:** EA-001 · **WP:** WP-04 Dependency Mapping
**Mode:** Read-only · **Authority:** Lead Engineer · **Tanggal:** 2026-08-08
**Catatan:** Mencatat kondisi dependency aktual. **Tidak membuat dependency graph baru.**

---

## 1. Metode

Analisis deterministik berbasis **import statement `sam.<runtime>`** pada seluruh file `.py` di `src/` dan `tests/`. Dihitung per target runtime: file mana yang mengimpornya dari luar folder runtime itu sendiri (inbound) dan ke runtime mana file di dalam folder runtime itu mengimport (outbound).

## 2. Dependency Matrix (12 Runtime)

| Runtime | Outbound (import ke runtime lain) | Inbound (di-import dari luar) |
|---|---|---|
| Mission Runtime | — (tidak ada) | tests/10 |
| Workflow Runtime | — (tidak ada) | tests/9, src/1 |
| Policy Runtime | — (tidak ada) | tests/9, src/1 |
| Registry Runtime | — (tidak ada) | tests/2 |
| Approval Runtime | — (tidak ada) | (tidak terdeteksi dari luar) |
| Execution Runtime | — (tidak ada) | tests/23, src/2 |
| Audit Runtime | — (tidak ada) | tests/10, src/2 |
| Artifact Runtime | — (tidak ada) | tests/9, src/1 |
| Knowledge Runtime | — (tidak ada) | tests/10, src/1 |
| Memory Runtime | — (tidak ada) | tests/10, src/2 |
| Provider Runtime | — (tidak ada) | tests/25 |
| **Runtime Service** | **→ Audit(5), Memory(5), Policy(3), Artifact(3), Workflow(3), Knowledge(3), Execution(1)** | tests/25, src/5 |

## 3. Analisis Dependency

### Outbound Runtime Dependency
- **11 runtime** bersifat **independen** — tidak ada file di dalam folder-nya yang mengimport runtime EA-001 lain.
- **Runtime Service** adalah **satu-satunya yang memiliki outbound dependency** (6 runtime). Ini konsisten dengan peran konstitusionalnya: *"All runtime orchestration belongs to Runtime Service."*

### Inbound Runtime Dependency
- Mayoritas runtime **di-import dari `tests/`** (konsumsi uji) dan sebagian kecil dari `src/`.
- **Approval Runtime** tidak terdeteksi di-import dari luar (kernel/internal → konsisten sebagai subsystem kernel yang dijalankan internal).

### External Dependency (antar-runtime saja, non-EA-001)
- Analisis ini berfokus pada dependency **antar 12 runtime EA-001**. Dependency ke paket eksternal (bukan runtime EA-001) tidak menjadi scope inventaris dependency matrix ini untuk baseline Program B.

## 4. Verifikasi
- Tidak ada dependency **sirkular** antar 12 runtime yang terdeteksi (Runtime Service hanya mengimport, tidak diimport oleh runtime lain yang terdeteksi; runtime lain saling independen).
- Tidak dibuat graph baru; hanya mencatat kondisi aktual sesuai WP-04.

---

*— Akhir EA-001-004 —*
