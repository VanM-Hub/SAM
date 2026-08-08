# SAM

The **Deterministic Operational Intelligence Platform** that governs intelligent systems.

**Versi:** SAM 1.0 Foundation 

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

```bash
# Clone
git clone https://github.com/VanM-Hub/SAM.git
cd SAM

# Setup (Windows PowerShell)
$env:PYTHONPATH = "./src"
$env:PYTHONIOENCODING = "utf-8"

# Install dependencies
pip install -e ".[dev,console]"
```

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
# Baseline CI (7 runtime suites + unit tests)
python -m pytest tests/unit/ tests/knowledge_runtime/ tests/memory_runtime/ tests/policy_runtime/ tests/workflow_runtime/ tests/artifact_runtime/ tests/audit_runtime/ tests/mission_runtime/ -q --tb=short

# Semua test (termasuk di luar baseline)
python -m pytest tests/ -q --tb=short
```

Baseline CI: 3,808 tests passed, 1 skipped (8 folder, 7 runtime suites + unit). The test suite runs locally and in CI. Metrics history was archived to **[docs/history/reports/Repository_Metrics.md](docs/history/reports/Repository_Metrics.md)**.

---

## 10. Roadmap

The roadmap defines the ordering of implementation evolution that serves the Mission — not an independent statement of direction.

> See **[ROADMAP.md](docs/foundation/ROADMAP.md)** — the ordering of implementation phases.

---

## 11. License / Contribution

- **License:** Apache-2.0 — see [LICENSE](LICENSE).
- **Contribution:** see [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/development/Contributor_Checklist.md](docs/development/Contributor_Checklist.md).
