# EA-003-006 — Runtime Risk Assessment (Program B)

**Program:** MISSION-2B / Program B · **Package:** EA-003 · **WP:** WP-06 Runtime Risk Assessment
**Mode:** Planning (blueprint, read-only) · **Authority:** Lead Engineer · **Tanggal:** 2026-08-08
**Basis:** gap EA-002-007 · Tiap risiko: severity, probability, mitigation, verification.

---

## 1. Risk Register

| ID | Risiko (kategori) | Runtime | Severity | Probability | Mitigation | Verification |
|---|---|---|---|---|---|---|
| R1 | **Network call placeholder** (Missing capability) | Provider | **High** | High | aktivasi provider network + secret mgmt terisolasi; fallback preview saat key tidak ada | integration e2e (mock-safe) + config validity |
| R2 | **Preview runtime tanpa operational mode** (Preview runtime) | Workflow, Policy, Audit, Artifact, Knowledge, Memory | Medium | High | definisikan operational exec path via RS bertahap (cohort Fase 1) | runtime verification per runtime |
| R3 | **Knowledge tanpa suite test dedicated** (Missing tests) | Knowledge | Medium | Medium | ciptakan `tests/knowledge_runtime/` dari test tersebar yang ada | suite lulus + coverage |
| R4 | **Registry/Approval/Memory/Mission test tersebar/rendah** (Missing tests) | 4 runtime | Low | Medium | konsolidasi test ke folder dedicated | suite terpusat |
| R5 | **Cakupan test Runtime Service penuh belum ada** (Missing evidence/operational) | Runtime Service | Medium | Low | tambah e2e + operational verification | CI hijau + operational proof |
| R6 | **Operational dependency pada Secret** (Operational/External dependency) | Provider | Medium | Medium | secret via env/manager, tidak di-commit; key optional di test | secret presence check |
| R7 | **Korelasi promotion menyentuh Kernel** (Operational dependency) | Registry, Approval, Execution | Low | Low | kernel activation bertahap + rollback per-runtime | kernel runtime test |
| R8 | **Dokumentasi belum selaras readiness** (Missing evidence) | semua | Low | Low | dokumentasi per promotion dalam laporan | doc lint |

## 2. Ringkasan

- **Risiko terbesar (High):** R1 — Provider network capability inaktif (sejalan dengan gap P1 EA-002).
- **Risiko kategori dominan:** Preview runtime (R2) & Missing tests (R3,R4) — sesuai gap EA-002-007.
- **Severity/probability mayoritas Medium/Low** — tidak ada risiko yang memerlukan perubahan Architecture.

## 3. Kesimpulan

- Seluruh risiko telah diklasifikasikan (6 kategori gap) dengan severity + probability + mitigation + verification.
- **Tidak ada risiko arsitektural** → tidak ada Stop Condition Architecture.
- Mitigasi semuanya berbentuk realisasi/evidence (sesuai guardrail), bukan perubahan Runtime.

---

*— Akhir EA-003-006 —*
