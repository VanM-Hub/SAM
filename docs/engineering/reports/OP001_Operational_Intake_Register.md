# Operational Intake Register — OP-001

**Owner:** Lead Engineer · **Date:** 2026-08-06 · **Sumber tunggal evidence operasional.**
**Prinsip:** tidak ada pekerjaan tanpa evidence yang tervalidasi & terklasifikasi.

---

## Register Evidence

| ID | Sumber | Deskripsi | Reproducible | Owner | Klasifikasi | Aksi |
|---|---|---|---|---|---|---|
| B1 | Bug report | `import sam.reasoning` → ImportError (S10-TDR-001) | Ya | Engineering | E-2 (untuk fix penuh) | Triage; fix = TD-3 (arsitektur) |
| B2 | Bug report | `test_two_runs_same_structure` flaky (ENG-BUG-001) | Sebagian (pass saat isolasi) | Engineering | E-1 (backlog) | Backlog; jangan diperbaiki sekarang |
| B3 | Bug report | dead module `sam/runtime/discovery.py` (ENG-DEBT-001) | Ya | Engineering | E-2 (removal butuh keputusan) | Deferred |
| B4 | Bug report | `validate_layers.py` SIGKILL (VAL-001) | Ya | Engineering | E-2 (tooling, butuh scoping) | Backlog TD-2 |
| R1 | Regression | stabil (3483+ passed) — tiada regression | — | — | E-0 | No action |
| C1 | CI failure | auto-rerun secret (eks-tertiari) | Eksternal | Repo-owner | E-3 (bukan engineering kode) | Konfigurasi GitHub eksternal |
| S1 | Security | 0 secret leakage (EM-003) | — | — | E-0 | No action |
| P1 | Performance | startup variasi 0.31–0.45s (lingkungan) | Tidak (variasi run) | — | E-0 | No action (bukan regresi) |
| I1 | Incident | none | — | — | E-0 | No action |
| M1 | Mission/roadmap | MISSION-001 (mode operational, bukan fitur); tiada roadmap lain | — | — | E-0 (mandat mode) | Terapkan kebijakan operasional |

---

## Ringkasan Klasifikasi (menunggu OP-2)
- **E-0 (No Action):** R1, S1, P1, I1, M1
- **E-1 (Engineering Task):** B2 (backlog)
- **E-2 (Architecture Escalation):** B1, B3, B4 (fix/removal menyentuh ownership/tooling arsitektur)
- **E-3 (Mission Escalation):** C1 (konfigurasi eksternal, bukan kode engineering)

## Aturan
- Register ini adalah sumber tunggal evidence operasional.
- Tidak membuka paket implementasi tanpa evidence tervalidasi & klasifikasi jelas.
- Untuk tiap evidence: klasifikasi (E-0..E-3), owner, aksi.
