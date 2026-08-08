# EA-001-005 — Security Readiness Report

**Program:** D (MISSION-2D — Production Readiness)
**Phase:** EA-001 — Production Readiness Assessment
**WP:** D5 — Security Assessment
**Type:** READ-ONLY ASSESSMENT (evidence only — no repository change)
**Date:** 2026-08-08
**Status:** COMPLETE

---

## Objective

Memetakan baseline security SAM: authentication, authorization, secret management, configuration exposure, dan dependency surface.

---

## Evidence: Authentication & Authorization

| Aspek | Evidence | Analisis |
|---|---|---|
| Approval Gate | `src/sam/approval/` — gate persetujuan eksekusi | Kontrol eksekusi via approval (bukan auth user murni) |
| Guardian runtime | `src/sam/guardian/` — pipeline pengaman | Layer keamanan operasional |
| Policy runtime | `src/sam/policy_runtime/` + `operations/security.py` (`_observe_policies` cek PYTHONPATH code-injection) | Ada pemeriksaan policy permisif |
| Compliance checkers | 99 checker runtime compliance (`src/sam/compliance/`) | Lembar kepatuhan |
| User authentication | **Tidak ditemukan mekanisme user auth/login** (default single-operator, host-based) | Gap — CLI/REST tanpa otentikasi user |

**Temuan:** Keamanan SAM fokus pada *operational governance* (approval, policy, compliance, guardian) — bukan *identity & access management* (user auth). Tidak ditemukan login/role manajemen user.

---

## Evidence: Secret Management & Configuration Exposure

| Aspek | Evidence | Referensi |
|---|---|---|
| Secret scanning | `operations/security.py:_observe_secrets()` — scan env-var sensitif (TOKEN, SECRET, PASSWORD, KEY, CREDENTIAL, AUTH), redaksi nilai (`val[:4]+"****"`) | `src/sam/operations/security.py` |
| Secret tidak disarm di source | `api/llm_wiring.py` — "SECURITY: tidak menyimpan credential/API key apapun" (env-only) | `src/sam/api/llm_wiring.py:88` |
| Env-based credential | Kredensial provider di-set via env saat runtime (`PROVIDER_ENV`), bukan hardcode | `api/llm_wiring.py`, `providers/` |
| File `.env` di repo | **Tidak ditemukan** file `.env` di repo root (bersih) | scan root |
| Config exposure | Konfigurasi via env-var (`SAM_WORKSPACE`, `SAM_HOST`, `SAM_SAFE_MODE`, `PYTHONPATH`); tidak ada file config berisi secret | `cli_entry.py`, `config_loader.py` |

**Temuan:** Secret management berbasis environment variable dengan redaksi saat observasi. Tidak ada file `.env` berisi secret di repo. **Kredensial LLM tidak di-persist** (env-only).

---

## Evidence: Dependency Surface

| Aspek | Evidence | Analisis |
|---|---|---|
| Dependencies inti | `structlog`, `pydantic>=1.10,<3`, `psutil` — minimal | `pyproject.toml` `dependencies` |
| Extra modular | console/desktop/server/dev — dependency opsional dipisah | `pyproject.toml` `[project.optional-dependencies]` |
| Permukaan attack | Server & desktop hanya ter-install jika extra aktif | Modular = mengurangi surface default |
| Supply chain | Tidak ditemukan lockfile/checksum dependency (tidak ada `requirements.lock`/pinned hashes) | Gap — reproduksibilitas & keamanan supply-chain |

**Temuan:** Dependency inti minimal (3 paket). Extra opsional meminimalkan permukaan attack default. **Tidak ada lockfile/pinning hash** untuk supply chain security.

---

## Gaps Teridentifikasi (D5)

> Assessment mencatat gap sebagai gap — **TIDAK diperbaiki** dalam EA-001.

| ID | Gap | Severity | Keterangan |
|---|---|---|---|
| D5-G1 | **Tidak ada user authentication/authorization (IAM)** | **High** | Single-operator tanpa login; REST/server perlu otentikasi untuk produksi |
| D5-G2 | Secret management masih env-var ad-hoc; belum ada vault/encrypted store | **Medium** | Env-var lebih baik dari hardcode, tapi belum produksi-grade (tanpa enkripsi-at-rest) |
| D5-G3 | Tidak ada lockfile/checksum dependency (supply chain) | **Medium** | Instal dependency tidak terdokumentasi-dijenuh versi persist |
| D5-G4 | Tidak ada audit trail akses user (siapa mengakses apa) | **Medium** | Ada audit runtime, tapi bukan audit akses user/identity |

---

## Kesimpulan WP-D5

Baseline security kuat di **operational governance**: approval gate, guardian, policy checks, 99 compliance checkers, secret redaksi env-scan. Secret tidak di-hardcode (env-only, tidak ada `.env` berisi secret di repo). Dependency inti minimal & modular. **Kesenjangan utama: tidak ada user IAM/auth** (High) dan secret management belum enkripsi-at-rest (Medium).

*— Assessment read-only. Evidence = file kode + konfigurasi aktual repo.*
