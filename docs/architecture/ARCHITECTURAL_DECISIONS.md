# Architectural Decisions

**Version:** v1.0.0  
**Purpose:** Record the rationale behind major architectural decisions made during SAM development.

---

## ADR-001: Standalone Python Process (No Framework Dependency)

**Date:** Sprint 0  
**Context:** SAM could have been built as an OpenClaw module or a standalone tool.  
**Decision:** Standalone Python process with optional OpenClaw integration.  
**Rationale:** Independence from any specific platform; easier to deploy, test, and distribute.  
**Status:** ✅ Implemented  

---

## ADR-002: sqlite3 as Primary Database

**Date:** Sprint 0  
**Context:** Needed a persistent store for executions, knowledge, and state.  
**Decision:** Use sqlite3 (stdlib) — no external database dependency.  
**Rationale:** Zero setup, portable, sufficient for single-node deployments; migration path to PostgreSQL exists if needed.  
**Trade-off:** Single-writer limitation; not suitable for high-concurrency multi-node.  
**Status:** ✅ Implemented; 47 migrations  

---

## ADR-003: Layered Architecture with Strict Dependency Direction

**Date:** Sprint 1  
**Context:** Need to prevent circular dependencies and ensure modularity.  
**Decision:** Four layers (CLI → Application → Domain → Persistence → Infra) with strict downward-only dependencies.  
**Rationale:** Enforces separation of concerns; makes modules independently testable.  
**Status:** ✅ Implemented; verified in architecture audit  

---

## ADR-004: Async-First API Design

**Date:** Sprint 1  
**Context:** SAM needed to handle concurrent healing loops, monitoring, and event processing.  
**Decision:** All I/O operations are async (using `asyncio`).  
**Rationale:** No thread-safety issues; efficient concurrent operation.  
**Trade-off:** Slightly more complex code (`async def` everywhere).  
**Status:** ✅ Implemented  

---

## ADR-005: In-Memory First, Database Optional

**Date:** Sprint 10  
**Context:** Many subsystems (attention, working memory, context) need fast access.  
**Decision:** Use in-memory data structures as primary storage; database as optional persistence layer.  
**Rationale:** Performance (microsecond vs millisecond); simplicity.  
**Status:** ✅ Implemented  

---

## ADR-006: 9-Phase Self-Healing Loop

**Date:** Sprint 28  
**Context:** Needed a structured healing pipeline beyond simple detect-fix.  
**Decision:** Nine phases: Observe → Diagnose → Reason → Plan → Govern → Execute → Verify → Reflect → Learn.  
**Rationale:** Covers the full OODA loop with governance and reflection.  
**Status:** ✅ Implemented  

---

## ADR-007: Evolution Policy — No Auto-Approve

**Date:** Sprint 28  
**Context:** SelfOptimizer could automatically apply parameter changes.  
**Decision:** All parameter changes go through EvolutionPolicy with PENDING status; manual or CLI approve required.  
**Rationale:** Safety; prevents harmful automatic changes.  
**Status:** ✅ Implemented  

---

## ADR-008: Attention Manager Priority Rules

**Date:** Sprint 29  
**Context:** SAM needs to decide what to focus on when multiple issues compete.  
**Decision:** First-match-wins priority rules (confidence → health → latency → cost → balanced).  
**Rationale:** Deterministic, debuggable, predictable.  
**Status:** ✅ Implemented  

---

## ADR-009: Goal Arbitration — Weighted Scoring

**Date:** Sprint 29  
**Context:** Multiple goals (HEAL, OPTIMIZE, DEPLOY, etc.) need prioritization.  
**Decision:** Score = (priority × 0.3) + (urgency × 0.4) + (1 - resource/100) × 0.3, with context adjustments.  
**Rationale:** Simple, configurable, explainable.  
**Status:** ✅ Implemented  

---

## ADR-010: Five-Level Autonomy Model

**Date:** Sprint 32  
**Context:** Needed graduated autonomy rather than binary on/off.  
**Decision:** OBSERVE → RECOMMEND → ASSIST → SUPERVISE → AUTONOMOUS.  
**Rationale:** Allows graceful transitions; maps to real-world ops maturity models.  
**Status:** ✅ Implemented  

---

## ADR-011: Trust-Based Federation (Not Identity-Based)

**Date:** Sprint 31  
**Context:** Clusters need to decide which peers to trust.  
**Decision:** Dynamic trust scoring with decay (not static identity/ certificates).  
**Rationale:** Adaptive; penalizes unreliable peers automatically.  
**Status:** ✅ Implemented  

---

## ADR-012: Knowledge Sovereignty (PUBLIC/INTERNAL/RESTRICTED)

**Date:** Sprint 31  
**Context:** Not all clusters want to share all knowledge.  
**Decision:** Three-tier sovereignty with optional whitelist for RESTRICTED.  
**Rationale:** Respects cluster autonomy; necessary for multi-tenant deployments.  
**Status:** ✅ Implemented  

---

## ADR-013: Python 3.8+ Compatibility (with Polyfill)

**Date:** Sprint 28  
**Context:** Development team uses Python 3.8; `asyncio.to_thread` is 3.9+.  
**Decision:** Provide polyfill for `asyncio.to_thread` in `database.py`; support 3.8–3.12.  
**Rationale:** Maximum compatibility; polyfill is trivial.  
**Status:** ✅ Implemented  

---

## ADR-014: CLI-First Interaction Model

**Date:** Sprint 0  
**Context:** SAM needs a user interface.  
**Decision:** CLI-only for v1.0 (no REST API, no GUI).  
**Rationale:** Simplest to implement and test; enough for ops use.  
**Status:** ✅ Implemented; 10 sub-apps  

---

*Document prepared for SAM v1.0.0 release.*
