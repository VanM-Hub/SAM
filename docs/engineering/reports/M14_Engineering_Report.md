# M14 Engineering Report — SAM Becomes Useful

**Milestone:** M14 Build (delegated authority / SAM becomes useful) + re-architecture environment-adaptive
**Rilis:** SAM 5.2.0
**Tanggal:** 2026-08-14
**Status:** Implementasi selesai, real E2E parsial PROVEN + rombak environment-adaptive selesai + M14-CLOSE bukti autonomy (autonomous mutation & governed recovery)
**Verdict resmi:** Belum dikeluarkan (menunggu acceptance M14-CLOSE penuh)

---

## 1. Ringkasan Eksekutif

M14 menghubungkan fondasi yang telah ada (AutonomyLevel, Guardrails, Approval Policy, ApprovalGate, Ward, canonical execution, verification, audit, learning) menjadi **delegated authority bridge**: approval dapat diberikan secara otomatis HANYA bila delegated authority owner mengizinkan — tetap SATU ApprovalGate, SATU canonical execution, tanpa executor kedua, tanpa self-grant, tanpa menaikkan authority lewat learning.

Pada rilis ini ditambahkan **re-architecture environment-adaptive**: SAM memahami lingkungan tanpa hardcoded application catalogue; ward spesifik (Word/PDF/OpenClaw/GitHub/Provider) direfaktor menjadi instance `CapabilityProvider` yang didaftarkan ke mesin generik.

---

## 2. Lingkup & Prinsip

### Konstitusi eksekusi (jangan dilanggar)
- Approval tetap SATU (ApprovalGate canonical).
- Execution tetap SATU (canonical execution / AutonomousRecoveryLoop).
- Tidak ada executor kedua, tidak ada self-grant, tidak ada kenaikan authority lewat learning.
- Setiap milestone wajib: unit test + integration test + real E2E + evidence artifact + audit artifact + verifikasi independen.
- Klaim PROVEN HANYA setelah bukti real E2E; jika target tidak tersedia → hasil dilaporkan jujur (`blocked`/`fail-closed`), BUKAN fake success.

### Prinsip environment-adaptive (re-architecture)
- SAM TIDAK bergantung pada hardcoded application catalogue untuk discovery/investigation/diagnosis/recovery.
- SAM boleh jujur berkata "Evidence tidak cukup", TIDAK boleh berkata "aplikasi ini tidak ada di daftar saya", TIDAK boleh mengarang diagnosis, TIDAK boleh menganggap discovery sebagai permission.
- Alur: DISCOVERY → IDENTIFICATION → ENTRUSTMENT → OBSERVATION → INVESTIGATION → DIAGNOSIS → AUTHORITY → EXECUTION → VERIFICATION.

---

## 3. Komponen Diimplementasikan

### 3.1 Delegated Authority Foundation (`src/sam/delegated_authority/`)
| Komponen | Peran |
|---|---|
| `authority.py` | `DelegationGrant` (default `requires_human_approval=True` → fail-closed), AutonomyLevel |
| `evaluation.py` | `AuthorityEvaluation`: Policy → Risk → Evidence → Autonomous Authority → Guardrails; verdict ESCALATE saat policy butuh approval manusia |
| `escalation.py` | `AutomaticEscalation` |
| `provider.py` | `DelegatedApprovalProvider` — escalate bila grant belum set `requires_human_approval=False` |
| `recovery.py` | `AutonomousRecoveryLoop` canonical + `ProviderRecovery` |
| `scope.py`, `safety_certification.py`, `operational_certification.py` | ScopedAutonomy, sertifikasi keselamatan & operasional |

### 3.2 Real Targets (`real_*` investigators)
| Target | Peran | Import |
|---|---|---|
| `real_word_investigation.py` | Investigasi struktural docx (read-only) | `DelegationGrant` |
| `real_pdf_investigation.py` | Investigasi performa PDF (read-only) | `DelegationGrant` |
| `real_openclaw_ward.py` | Health/log collector workspace | `OpenClawDiagnosis` |
| `real_project_guardian.py` | `ProjectGuardian` probe GitHub/Lokal | `ProjectProbe` |
| `real_provider_recovery.py` | `ProviderHealthProbe` | `ProviderProbe` |
| `real_windows_pc_ward.py` | Windows PC Ward | — |
| `real_credential_remediation.py` | Remediasi kredensial via boundary | — |

### 3.3 Environment-Adaptive Core (`src/sam/environment/`) — re-architecture
| Komponen | Peran |
|---|---|
| `entity.py`, `discovery.py` | Model entitas generik + enumerasi environment tanpa katalog |
| `graph.py` | Model relasi antar-entitas |
| `confidence.py` | Confidence berbasis evidence; jujur INSUFFICIENT/LOW/MEDIUM |
| `diagnosis.py`, `remediation.py` | Strategi investigasi/root-cause + remediation tanpa asumsi jenis aplikasi |
| `pipeline.py` | Mesin generik; pilih ward candidate berdasar entity health facts (BUKAN nama aplikasi) |
| `learning.py` | AdaptiveMemory statistik observasi; TIDAK mengubah authority |
| `adaptor.py` | `AdaptiveCanonicalBridge` → canonical `AutonomousRecoveryLoop` |
| **`providers.py`** (baru) | `CapabilityProvider` + `ProviderRegistry` + `ProviderObservation` — instance capability; remediate HANYA menandai avail, tidak mengeksekusi |
| **`capabilities.py`** (baru) | Factory bungkus ward spesifik jadi provider instance; `register_default_instances` |

### 3.4 Rombak environment-adaptive (Opsi B — rombak habis)
Ward spesifik dirombak menjadi **instance `CapabilityProvider`** pada mesin generik, BUKAN hardcoded application catalogue. Mesin generik tetap berjalan penuh TANPA provider; provider hanya menambah observasi bila didaftarkan (registry default kosong).

---

## 4. Real E2E (bukti nyata, jujur)

| Tool | Bukti | Status |
|---|---|---|
| `m14_environment_adaptive_real_e2e.py` | 429 entitas, 57 graph edges, confidence jujur (INSUFFICIENT/LOW/MEDIUM), diagnosis generik pada proses nyata, pipeline verdict = `escalate` | REAL PROVEN (discovery ≠ permission) |
| `m14_pc_word_pdf_real_e2e.py` | Investigasi Word/PDF pada file nyata | REAL PROVEN (parsial) |
| `m14_project_guardian_real_e2e.py` | `ProjectGuardian` detect pada target GitHub/Lokal nyata | REAL PROVEN |
| `m14_provider_recovery_real_e2e.py` | Probe health provider + alur delegated (observasi/failover fail-closed) | REAL PROVEN (parsial) |
| `m14_008_credential_remediation_real_e2e.py` | Remediasi kredensial NYATA via `CredentialBoundary` (NVIDIA provider): deteksi key valid AVAILABLE, env kosong MISSING/BLOCKED, remediasi MISSING→AVAILABLE (owner-supplied, SAM tidak menebak secret), fail-closed tanpa otorisasi→ESCALATED, no self-grant, raw token tidak bocor ke output, audit boundary 6 entries | **REAL PROVEN** |

### M14-CLOSE — bukti autonomy (gap kritis yang ditutup)
| Tool | Bukti | Status |
|---|---|---|
| `m14_close_002_autonomous_mutation_real_e2e.py` | **Real Autonomous Mutation**: provider `nvidia` unhealthy → `DelegationGrant` owner AUTONOMOUS bounded (`requires_human_approval=False`, `allowed_mutations=("protect")`, `blast_radius=PROVIDER_CONNECTION`) → `auto_approve` (source `delegated`, approver `delegated:nvidia`) → switch nyata ke `ollama` → verifikasi ok. Skenario fail-closed (grant OBSERVE) → `escalate`, TIDAK switch. Fase penuh observe→investigate→diagnose→plan→authority→execute→verify. Mutation terjadi TANPA campur tangan user. | **REAL PROVEN** |
| `m14_close_003_failure_recovery_real_e2e.py` | **Governed Recovery / ESCALATE**: A) tanpa alternatif sehat → FAILED, `switched_to=None`, `loops_attempted=1` (tidak retry tak terbatas); B) switch B sukses tapi verification gagal → `escalated` utk review (`esc_...`), bounded attempt, bukan automated action. | **REAL PROVEN** |
| `m14_close_006_tahan_banting_degradation_e2e.py` | **Tahan banting**: observer A/B/C sengaja dirusak (throw) → partial evidence → confidence dihitung ulang jujur → verdict `escalate` (tidak eksekusi saat evidence tak cukup); credential unavailable → boundary MISSING/BLOCKED; no `evidence_missing→assume→execute`. Temuan jujur: `ConfidenceAssessor` menghitung evidence failed (0.0) sbg lemah (bias permisif) — SAM tetap aman. | **REAL PROVEN** |

> Seluruh bukti menggunakan provider nyata (NVIDIA token dari env, Ollama lokal); token tidak di-commit, tidak bocor ke output (no_leak), evidence eksternal.

### Status BLOCKED (jujur)
- **OpenClaw Ward real E2E** — jembatan `health.json` ke runtime belum tersambung penuh.
- **M14-CLOSE-004/005** (Guardian environment-adaptive + continuous guard) — belum dieksekusi sebagai bukti nyata (menunggu jadwal).

---

## 5. Sertifikasi

- **Autonomous Safety Certification** — 8 larangan keras: tidak menghapus approval semantics, tidak memberi diri sendiri authority, tidak menaikkan authority lewat learning, tidak mengubah credential di luar CredentialBoundary, tidak mengeksekusi connector langsung, tidak membuat executor kedua, tidak melakukan mutation di luar Ward scope. **PASS.**
- **Real Operational Certification** — jujur, tanpa klaim PROVEN tanpa real E2E. **PASS (dengan status BLOCKED dicatat jujur).**

---

## 6. Pengujian

| Area | Jumlah | Status |
|---|---|---|
| `tests/environment/` (mesin generik + rombak B) | 17 | PASS |
| `tests/delegated_authority/` (M14) | 67 | PASS |
| `tests/ward/` (M13) | 47 | PASS |
| **Gabungan environment + M14 + M13** | **131** | **PASS** |
| `tests/platform/` | 141 | PASS |
| `tests/execution_runtime/` | 359 | PASS (1 flaky network browser pre-existing) |
| `tests/application/` | 124 | PASS |

Rombak B TIDAK merusak M13/M14.

---

## 7. Delivery

| Artefak | Commit |
|---|---|
| M14 foundation (001-006): delegated authority bridge | `0946245` |
| M14-009..010: OpenClaw Ward + Windows PC Ward | `bd7f6e5` |
| M14-011..012: Word + PDF investigation | `2686ad8` |
| M14-013: Project Guardian | `8aad9fa` |
| M14-014..015: Safety + Operational Certification | `7b45117` |
| M14 real E2E (PC/Guardian/Provider) | `1072235` |
| **Rombak B: CapabilityProvider registry** | `eba15bd` |
| Docs README/CHANGELOG/ATLAS (opsi B) | `3994130` |
| M14-008 real E2E: Credential Remediation PROVEN | `934d64e` |
| Update laporan M14 (M14-008 PROVEN) | `71312c7` |
| M14-CLOSE-002/003/006: autonomous mutation + governed recovery + tahan banting | `7bd84b2` |

Semua commit ter-push ke `main`.

---

## 8. Lingkup Perubahan Terkait (riwayat terverifikasi)

- M13 Universal Governance of External Wards — CERTIFIED (17/17).
- M12 Self-Preservation — CERTIFIED (M12-001..017 PASS).
- Environment-adaptive menambah folder `src/sam/environment/` (ATLAS & README telah diperbarui).
- M14-008 (Credential Remediation) kini REAL PROVEN via provider NVIDIA nyata (token dari env, tidak di-commit; evidence eksternal).

---

## 9. Catatan Jujur & Dampak

- Error collection pada suite penuh `tests/` (`import file mismatch` pada `test_wp*`) berasal dari **duplikasi nama file** pada folder test — kondisi pre-existing, bukan dari rombak environment.
- Satu regression network test (`test_m6browser_fetch_real`) rentan flaky akibat timeout koneksi eksternal — perilaku harness `honest-fail`, bukan regresi.
- **Temuan M14-CLOSE-006:** `ConfidenceAssessor` menghitung evidence *source failed* (strength 0.0) sebagai evidence lemah sehingga beberapa evidence gagal bisa menghasilkan confidence MEDIUM (bias permisif). SAM tetap aman (verdict `escalate`, tidak mengeksekusi), tapi assessor layak diperbaiki agar evidence gagal dihitung sebagai pengurang, bukan penambah. Direkomendasikan utk iterasi berikutnya.
