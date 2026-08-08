# WP-D2.2 — H5 User Identity & Access Management (IAM) — Engineering Evidence

**Program:** D (MISSION-2D — Production Readiness)
**Phase:** EA-002 — Production Readiness Implementation
**Priority:** P2 · **Gap:** H5 User Identity & Access Management
**Type:** Working Report (evidence) → `reports/`
**Date:** 2026-08-08
**Status:** ✅ COMPLETE (menunggu Verdict Lead Engineer)

---

## Objective (ruang lingkup implementasi)

Menutup Gap H5 sesuai EA-001-005: **"Tidak ada user authentication/authorization (IAM) — default single-operator tanpa login; REST/server perlu otentikasi untuk produksi."**

1. Menyediakan **user identity** (principal/role) yang sebelumnya tidak ada.
2. Menyediakan **authentication** — verifikasi kredensial user (bukan plaintext).
3. Menyediakan **authorization (RBAC)** — role/permission terhadap resource.
4. Menyediakan **audit akses user** (sukses/gagal).
5. Menjaga constraint EA-002: **tidak mengubah responsibility runtime existing**.

---

## Gap yang Diperbaiki (H5)

Sebelumnya SAM beroperasi sebagai **single-operator tanpa login**: tidak ada user store, tidak ada autentikasi kredensial, tidak ada RBAC user, tidak ada audit akses user. Keamanan fokus pada *operational governance* (approval gate, guardian, compliance) — bukan *identity & access management*.

---

## Desain (konservatif terhadap constraint EA-002)

Modul **`src/sam/iam/`** dibangun sebagai **capability baru stand-alone**:

| File | Peran |
|---|---|
| `principal.py` | Model Identity: `User`, `Principal`, `Role`, `CredentialHash` (immutable) |
| `registry.py` | `UserRegistry` — user store (kredensial sebagai hash, bukan plaintext) |
| `authenticator.py` | `Authenticator` — verifikasi kredensial (PBKDF2, constant-time) |
| `authorizer.py` | `Authorizer` — RBAC (subject/resource/permission) |
| `audit.py` | `AccessAuditLog` — catatan akses user (append-only, ring buffer) |

**Keputusan engineering (didokumentasikan):** IAM dibuat **stand-alone**, TIDAK di-wire otomatis ke approval gate / guardian / runtime_kernel. Integrasi IAM ke lapisan tersebut adalah **keputusan arsitektur terpisah** (di luar scope H5) dan tidak dilanggar sekarang untuk menghormati constraint EA-002 ("no change runtime responsibility"). Foundation / Constitution / Governance / Accepted ADR tidak diubah.

**Kompatibilitas:** `Authorizer` memakai pola `subject/resource/permission` yang **kompatibel dengan model `runtime_kernel.runtime_security.AccessControl`** — sehingga hasil keputusan IAM dapat dipetakan ke lapisan akses existing bila integrasi diputuskan di masa depan.

---

## Implementasi Detail

### Authentication (anti plaintext & anti timing-attack)
- Kredensial disimpan sebagai `CredentialHash` — PBKDF2-SHA256, salt unik per user, **120.000 iterasi**, disimpan `salt_hex` + `digest_hex` (BUKAN plaintext).
- Verifikasi memakai `hmac.compare_digest` (**constant-time**, anti timing attack).
- Gagal login untuk user tidak dikenal memberi **reason yang sama** dengan kredensial salah (anti user-enumeration).

### Authorization (RBAC)
- `Resource` = `kind:name` (mis. `api:health`).
- `Permission` = action (`read|write|execute|admin`).
- Role `admin` = wildcard penuh; wildcard per-kind (`action:kind:*`) dan global (`action:*`) didukung.
- Default deny — tanpa role/principal → ditolak.

### Audit
- `AccessAuditLog` mencatat event `authenticate`/`authorize` + outcome `success`/`failure`.
- **Tidak pernah menyimpan kredensial** — hanya username, resource, action, reason.
- Ring-buffer (default 1000) untuk mencegah pertumbuhan tak terbatas.

---

## Evidence Suite (otomatis, bagian CI integration)

**`tests/integration/test_iam.py`** — 30 test, masuk CI integration job:

| Area | # Test | Cakupan |
|---|---|---|
| Registry | 9 | create, normalize, duplicate, not-found, **hash-not-plaintext**, assign role, disable, list, no-plaintext-repr |
| CredentialHash | 4 | verify benar/salah/none, salt unik |
| Authenticator | 5 | sukses, salah, **anti user-enumeration**, user nonaktif, normalize |
| Authorizer (RBAC) | 8 | admin wildcard, no-role deny, viewer read, kind-wildcard, write-deny, editor, resource parse, none-principal deny |
| Audit | 3 | success/failure, **tanpa kredensial**, ring-buffer |

Setiap test memverifikasi properti keamanan yang menutup gap H5.

---

## Bukti Verifikasi Nyata

| Uji | Hasil |
|---|---|
| `import sam.iam` + API publik | ✅ IAM import OK |
| `tests/integration/test_iam.py` | ✅ 30 passed |
| Integration suite penuh `tests/integration/` | ✅ 86 passed |
| Baseline CI scope (unit + runtimes + observation) | ✅ 4290 passed, 1 skipped, 2 xfailed |

**Tidak ada regression.** Runtime, approval, guardian, dan seluruh capability existing tidak berubah.

---

## Compliance

- Foundation: tidak diubah ✅
- Constitution: tidak diubah ✅
- Governance: tidak diubah ✅
- Accepted ADR: tetap berlaku ✅
- Runtime konstitusional baru: tidak ditambah ✅
- Responsibility runtime: tidak diubah ✅ (IAM = capability baru stand-alone)
- Kredensial tidak plaintext ✅

---

## Status

H5 **User Identity & Access Management** terimplementasi, ter-verifikasi, ter-test. Seluruh ruang lingkup P2 terpenuhi.

*— Engineering evidence WP-D2.2 (H5). Meneruskan ke Verdict Lead Engineer.*
