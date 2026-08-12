# SAM

The **Deterministic Operational Intelligence Platform** that governs intelligent systems.

**Versi:** SAM 4.1 - Universal Governance Platform (4.1.0) - MISSION-5.1..5.6 Implementation (Work In Progress)

Sejak v4.1.0, SAM memperluas platform melalui **Universal Governance (SAM 5.x)**: AI, Tool, Agent, dan Workflow diperlakukan sebagai **Citizen** yang di-govern via kontrak seragam, ditambah Enterprise Governance boundary dan Adaptive Governance (learning/simulation/impact/recommendation) di atasnya. Authority tetap di manusia.

**M9 Productization (2026-08-12):** SAM kini punya *real user-facing operational path* via `src/sam/application/ux/` (`MissionUXService`). UI (browser) memanggil `/ux` endpoint → Application Service → ApprovalGate canonical → mission canonical → real external effect (GitHub, dst), tanpa executor kedua. Lihat `CHANGELOG.md` untuk detail M9.

---

## 1. What is SAM?

SAM is a governance platform for intelligent systems. It does not build intelligence; it governs how intelligence is discovered, selected, coordinated, approved, executed, audited, and evolved.

SAM exists so that intelligent systems remain accountable — regardless of how models, providers, or technologies change.

*Authority: MISSION.md*

---

## Reading Order

If you are new to Project SAM, read the documentation in the following order:

1. Mission
2. Constitution
3. Philosophy
4. Governance
5. Canonical Architecture
6. Repository Convention
7. Roadmap
8. ADR

---

## 2. Mission

The mission of SAM is to provide a trustworthy governance platform for intelligent systems: governing intelligence rather than creating it.

> See **[MISSION.md](MISSION.md)** — the highest authority and the reason SAM exists.

---

## 3. Constitution

The Constitution defines what must never change, and derives its legitimacy from the Mission.

> See **[docs/CONSTITUTION.md](docs/CONSTITUTION.md)** — the canonical Constitution of Project SAM.

---

## 4. Architecture

The canonical architecture realizes Governance as a system: layers, responsibilities, dependencies, and deployment abstraction.

> See **[docs/architecture/SAM_ARCHITECTURE.md](docs/architecture/SAM_ARCHITECTURE.md)** — the Canonical Architecture.

---

## 5. Documentation Guide

To understand SAM, read the documents in dependency order. Each document inherits its authority from the one above it.

Documents belong to a category. Categories indicate the role of a document in the governance structure:

**Canonical · Foundational · Specification · Engineering · Historical**

Historical documents are preserved as part of the evolution lineage and are not authoritative.

> **Non-authoritative docs:** Everything under **[docs/history/](docs/history/)** (legacy sprints, archived reports) is history — it records what **was**, not what **is**. Documents marked **`Status: Draft`** or **`Status: Deprecated`** (e.g. exploratory architecture concepts like `docs/architecture/OPENCLAW_AS_MODULE.md`) are proposals/ideas, not the current state of SAM. Authoritative current state lives in the canonical documents (Mission, Constitution, Canonical Architecture, ROADMAP) plus the tagged release notes.

```
MISSION
  ↓
CONSTITUTION
  ↓
CITIZEN SPECIFICATION
  ↓
PHILOSOPHY
  ↓
GOVERNANCE
  ↓
MODELS (TRUST, RISK, DECISION, MEMORY)
  ↓
CANONICAL ARCHITECTURE
  ↓
ROADMAP
  ↓
ADR
  ↓
IMPLEMENTATION
```

Key documents:

- **Mission** — [MISSION.md](MISSION.md)
- **Constitution** — [docs/CONSTITUTION.md](docs/CONSTITUTION.md)
- **Citizen Specification** — [docs/CITIZEN_SPECIFICATION.md](docs/CITIZEN_SPECIFICATION.md) · jembatan konseptual antara Constitution dan seluruh Specification teknis
- **Philosophy** — [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md)
- **Governance** — [GOVERNANCE.md](GOVERNANCE.md)
- **Glossary** — [GLOSSARY.md](GLOSSARY.md)
- **Canonical Architecture** — [docs/architecture/SAM_ARCHITECTURE.md](docs/architecture/SAM_ARCHITECTURE.md)
- **Specification Layer (frozen)** — [docs/specifications/](docs/specifications/) · [Freeze Declaration](docs/SPECIFICATION_FREEZE.md)

---

## 6. Repository Structure

```
SAM/
├── src/sam/                 # Python source
├── tests/                   # Test suite
├── docs/                    # Documentation
│   ├── CONSTITUTION.md      # Canonical Constitution
│   ├── CITIZEN_SPECIFICATION.md  # Bridge Constitution -> Specifications
│   ├── GOVERNANCE.md / GLOSSARY.md / PHILOSOPHY.md
│   ├── architecture/        # Canonical Architecture
│   ├── models/              # Model Layer (trust, risk, decision, memory)
│   └── specifications/      # Specifications
├── MISSION.md               # Mission
├── VISION.md                # Vision
├── foundation/ROADMAP.md     # Implementation evolution ordering
└── .github/workflows/       # CI
```

---

## 7. Quick Start

Jalur cepat **end-to-end** untuk early adopter - panduan lengkap ada di
**[`docs/user/quickstart.md`](docs/user/quickstart.md)**.

```bash
# 1. Clone & masuk
#    git clone https://github.com/VanM-Hub/SAM.git && cd SAM
#    (atau pakai shortcut SAM_Run.bat di Windows)

# 2. Rencana instalasi (dry-run, tidak mengubah apa pun)
python -m sam.cli.main onboarding init

# 3. Instalasi sungguhan (otomatis: venv + install editable)
python -m sam.cli.main onboarding init --apply

# 4. Verifikasi versi & kesehatan
python -m sam.cli.main onboarding version
python -m sam.cli.main onboarding doctor

# 5. Jalankan
python -m sam.cli.main health
```

> Command `onboarding init / doctor / version` (WP-E2.2) memandu early adopter
> dari install sampai contoh pertama - cepat, non-destruktif, dan tidak
> memerlukan pemahaman arsitektur internal.

---

## 8. Development

```powershell
# Jalankan test
python -m pytest tests/ -q --tb=short
```

Contributions follow the repository conventions and the governance lifecycle. See **[REPOSITORY_CONVENTION.md](REPOSITORY_CONVENTION.md)** and **[CONTRIBUTING.md](CONTRIBUTING.md)**.

---

## 9. Testing

```powershell
# Baseline CI (8 runtime suites + unit tests, 4,017 tests)
python -m pytest tests/unit/ tests/knowledge_runtime/ tests/memory_runtime/ tests/policy_runtime/ tests/workflow_runtime/ tests/artifact_runtime/ tests/audit_runtime/ tests/mission_runtime/ tests/execution_runtime/ -q --tb=short

# Semua test (termasuk di luar baseline)
python -m pytest tests/ -q --tb=short
```

Baseline CI: 4,017 tests passed, 1 skipped, 2 xfailed (9 folder, 8 runtime suites + unit). The test suite runs locally and in CI. Metrics history was archived to **[docs/history/reports/Repository_Metrics.md](docs/history/reports/Repository_Metrics.md)**.

SAM 4.0 (bonus): 3,543 passed, 1 skipped (unit + 5 BC 4.x baru + observation); regression 571 passed, 2 xfailed; compliance 559; 362 test baru mission 4.1..4.6; lint & ASCII bersih.

---

## 10. Roadmap

The roadmap defines the ordering of implementation evolution that serves the Mission — not an independent statement of direction.

> See **[ROADMAP.md](docs/foundation/ROADMAP.md)** — the ordering of implementation phases.

---

## 11. License / Contribution

- **License:** Apache-2.0 — see [LICENSE](LICENSE).
- **Contribution:** see [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/development/Contributor_Checklist.md](docs/development/Contributor_Checklist.md).
