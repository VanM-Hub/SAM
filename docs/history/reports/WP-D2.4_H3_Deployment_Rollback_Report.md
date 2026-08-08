# WP-D2.4 — H3 Deployment Rollback — Engineering Evidence

**Program:** D (MISSION-2D — Production Readiness)
**Phase:** EA-002 — Production Readiness Implementation
**Priority:** P4 · **Gap:** H3 Deployment Rollback
**Type:** Working Report (evidence) → `reports/`
**Date:** 2026-08-08
**Status:** ✅ COMPLETE (menunggu Verdict Lead Engineer)

---

## Objective (ruang lingkup implementasi)

Menutup Gap H3 sesuai EA-001-003 (D3-G1, **High**): **"Tidak ada prosedur/artefak rollback deployment terstandar"** — rollback saat itu hanya berbasis Git source, tidak ada rollback untuk deployment/artifact/config terstandar.

1. **Riwayat deployment** ber-version (semantic versioning).
2. **Pointer aktif** — menandai deployment yang sedang berjalan.
3. **Snapshot state deployment** — representasi kanonik yang dibackup saat deploy.
4. **Rollback** ke versi deployment sebelumnya secara **deterministik & terverifikasi**.
5. **Audit** operasi deploy/activate/rollback (tanpa payload state).
6. Menjaga constraint EA-002: **tidak melakukan efek eksternal, tidak ubah runtime existing**.

---

## Gap yang Diperbaiki (H3)

Assessment EA-001-003 menemukan:
- Rollback kuat di level **source code** (Git, deterministik) dan sebagian **schema DB** (migration manager).
- **TIDAK ada rollback deployment/artifact/config terstandar** (D3-G1, High).
- Tidak ada snapshot runtime-state untuk rollback (D3-G3, Medium) & rollback boundary tidak terdokumentasi (D3-G4, Low).

Catatan penting: `src/sam/execution_runtime/rollback_runtime.py` dkk = **rollback EKSEKUSI** (metadata internal eksekusi tugas, Program C — memulihkan metadata internal, tidak membatalkan efek eksternal). Ini **BUKAN** deployment rollback — gap D3-G1 tetap valid dan tidak tumpang tindih.

---

## Desain (konservatif terhadap constraint EA-002)

Modul **`src/sam/deploy_rollback/`** dibangun sebagai **capability baru stand-alone** (pola konsisten H2):

| File | Peran |
|---|---|
| `state.py` | DTO immutable (ADR-023): `DeploymentSnapshot`, `DeploymentVersion` |
| `manifest.py` | `DeploymentIndex` — riwayat deployment, latest, active pointer, deteksi korup |
| `rollback.py` | `DeploymentManager` — deploy, activate, rollback, verify |
| `audit.py` | `DeploymentAuditLog` — catatan deploy/activate/rollback (tanpa payload) |

**Keputusan engineering:** deployment rollback dibuat **stand-alone**, konsumen dapat memakainya tanpa mengubah lapisan existing. Tidak melakukan efek eksternal (network/host) — hanya mengelola metadata deployment secara deterministik (konsisten ADR-019 Recovery Contract: rollback tidak pernah membatalkan efek eksternal; ADR-000 Deployment Topology tidak menetapkan mekanisme rollback → wilayah ini berada di lapisan Production Readiness yang sah).

**Teknik kunci:**
- **Atomic write** — tulis ke temp file → `fsync` → `os.replace` (anti file setengah-tulis).
- **Semantic version** — `DeploymentVersion` untuk urutan deterministik lintas versi.
- **Pointer aktif** — satu snapshot `active=True` per artefak; deploy/activate menggesernya atomically.
- **Sanitasi path** — `artifact_id` boleh mengandung `:` (mis. `app:web`); saat jadi nama folder karakter tidak aman Windows (`:`/`/`/`\`/`"`/`<`/`>`/`|`/`?`/`*`) disanitasi ke `_`, tapi `artifact_id` asli tetap terpelihara di metadata snapshot.

---

## Evidence Suite (otomatis, bagian CI integration)

**`tests/integration/test_deploy_rollback.py`** — 24 test, memakai `tmp_path` (bukan folder repo):

| Area | # Test | Cakupan |
|---|---|---|
| Deploy | 5 | snapshot, persist state, aktivasi latest, deaktivasi aktif lain, version parse |
| Rollback | 6 | rollback ke previous, langkah bertingkat, no-previous, no-deployment, can_rollback, activate eksplisit |
| Manifest/Index | 5 | list versions ascending, list artifacts, latest, load missing, corrupt file |
| Verify/Status | 3 | status none, verify ok, history ascending |
| Audit | 4 | track events, tanpa payload, ring buffer, by artifact |
| Round-trip deploy→rollback | 1 | v1 stabil → v2 buruk → rollback ke v1 |

---

## Bukti Verifikasi Nyata

| Uji | Hasil |
|---|---|
| `import sam.deploy_rollback` + API publik | ✅ OK (8 exports) |
| `tests/integration/test_deploy_rollback.py` | ✅ 24 passed |
| Integration suite penuh `tests/integration/` | ✅ 133 passed |
| Baseline CI scope (unit + runtimes + observation) | ✅ 4290 passed, 1 skipped, 2 xfailed |

**Tidak ada regression.** `runtime_kernel`, `execution_runtime`, dan seluruh capability existing tidak diubah.

---

## Compliance

- Foundation: tidak diubah ✅
- Constitution: tidak diubah ✅
- Governance: tidak diubah ✅
- Accepted ADR: tetap berlaku ✅ (ADR-000 topology, ADR-019 recovery contract — tidak dilanggar)
- Runtime konstitusional baru: tidak ditambah ✅
- Responsibility runtime: tidak diubah ✅ (deployment rollback = capability baru stand-alone)
- Tidak melakukan efek eksternal (network/host) ✅
- State dir default di `.gitignore` — tidak ada artefak deployment ikut commit ✅

---

## Status

H3 **Deployment Rollback** terimplementasi, ter-verifikasi, ter-test. Seluruh ruang lingkup P4 terpenuhi.

*— Engineering evidence WP-D2.4 (H3). Meneruskan ke Verdict Lead Engineer.*
