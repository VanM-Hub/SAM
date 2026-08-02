# G1-001 — ADR Candidate C-02 (Capability Resolution)

**Version:** 1.0
**Status:** ADR Preparation (Read-only analysis — no decision)
**Authority:** Derived from the Foundation; derives from the Canonical Architecture and the Specification Layer; analyzes Candidate ADR C-02 of Blueprint G0-001.
**Owner:** Project SAM
**Mode:** Read-only. Analyzes alternatives without selecting implementation.

**Depends On:**
- MISSION
- CONSTITUTION (esp. Art. III, IV, VII, IX)
- GOVERNANCE
- GLOSSARY
- Canonical Architecture (SAM_ARCHITECTURE.md)
- Specification Layer (CAPABILITY, REGISTRY, CONTRACT)
- Blueprint G0-001 (Candidate ADR C-02)

> This document is **preparation only**. It does not create an ADR and does not take a decision.
> It collects constraints, identifies the valid design space, analyzes trade-offs, checks foundation compliance, and states whether an ADR can be written now.

---

## Audit 1 — Problem Statement

### 1.1 Why does the Runtime need Capability Resolution?

From the Canonical Architecture, Citizens must never assume another Citizen exists; all collaboration occurs through Capability-based discovery via the Registry (Article IV: "Citizens discover, never assume"). Capabilities are the universal language (Article III). The Registry makes Capabilities discoverable and resolvable (Registry Specification Purpose).

Capability Resolution is the step that turns a **Capability Request** into a **specific, bound, usable Capability** that the requesting Citizen can interact with. Without it, a Citizen may know *that* capabilities exist but cannot determine *which one* it will actually get.

Resolution is the **bridge** between discovery (what matches) and use (what is bound). It is the single point where the Runtime decides the effective target of an interaction. Every downstream component — Approval (approves an operation on a resolved Capability), Execution (performs the operation), Audit (records what happened) — depends on the outcome of resolution being correct and stable.

### 1.2 What breaks if there is no resolution mechanism?

- **Indeterminacy**: two identical requests could yield different Capabilities, violating Article VII ("Same input, same contracts, same policies, same output") and the Registry requirement that resolution be deterministic.
- **Direct coupling**: without a resolution step, a Citizen would have to know exactly which Citizen/provider to reach, reintroducing the direct dependency the Constitution forbids (Article IV violations).
- **Unsafe Interaction**: Approval and Execution would operate on an ambiguous target — "which Capability am I approving/executing in?" — breaking the Golden Rule (Mission → Governance → Approval → Execution → Verification → Audit) and the traceability chain to Audit.
- **Broken Contract binding**: a Contract exists between specific participants; without resolution, the immutable Contract cannot be reliably associated with the correct Capability, undermining Contract Enforcer and version negotiation.

**Conclusion**: Resolution is not optional. It is the mandatory bridge that preserves determinism, de-coupling, and the correctness of the Approval–Execution–Audit chain.

---

## Audit 2 — Existing Constraints

Collected verbatim (no interpretation added) from the frozen documents.

### From MISSION
- Every capability becomes discoverable. *(Success Criteria)*
- Every governed interaction should be: deterministic where governance is concerned, explainable, auditable, certifiable, replaceable, evolvable. *(What SAM Governs)*

### From CONSTITUTION
- **Art. III (Capability is the Universal Language)**: Citizens communicate through capabilities, never through implementation details. Discovery, Registry, Selection, Routing, Planning, Scheduling, and Coordination operate on capabilities.
- **Art. IV (Registry over Direct Dependency)**: Citizens discover, never assume. A Citizen should never know another Citizen directly. Communication happens through Registry and Discovery.
- **Art. VII (Deterministic by Default)**: Same input, same contracts, same policies, same output. Determinism has higher priority than convenience. Runtime behavior must be reproducible. Violations: hidden randomness, implicit context, time-dependent logic without explicit contract.
- **Art. IX (Runtime Independence)**: Every Runtime is independently evolvable. Runtime communication occurs through contracts. Violations: circular Runtime dependency.

### From CAPABILITY Specification
- Capabilities are: immutable, versioned, uniquely identifiable, discoverable, certifiable, auditable, implementation independent, backward compatible whenever practical. *(Constitutional Principles)*
- Capabilities are discovered through Registry, never through implementation. *(Discovery)*
- Registry provides: lookup, filter, version resolution, compatibility checks, dependency analysis. Registry never executes capabilities. *(Registry)*
- Citizens shall never assume another Citizen exists. Citizens request Capabilities. Registry resolves providers. This eliminates direct architectural coupling. *(Capability Discovery Rules)*
- A Capability may receive a new implementation provided: Contract remains compatible, Certification succeeds, Descriptor remains valid, Identity remains unchanged. Replacing implementation should not affect consumers. *(Capability Replacement)*
- Capabilities evolve through extension, not replacement. Preferred order: Patch → Minor → Major. Breaking compatibility requires explicit architectural review. *(Capability Evolution)*
- Each Capability possesses a globally unique identifier, recommended `<domain>.<category>.<capability>`. *(Capability Identity)*

### From REGISTRY Specification
- Registry holds references to objects defined elsewhere (Citizen, Capability, Descriptor, Version, Contract Reference). Registry never stores implementation. It stores the minimum information required to discover and resolve. *(Registry Object)*
- **Discovery Protocol**: input = Capability Request; output = Capability Descriptor + Contract Reference. Failures: Not Found, Version Mismatch, Error. Discovery SHALL be idempotent. An identical request SHALL produce an identical result. Discovery SHALL NOT have side effects on registered objects. *(Discovery Protocol)*
- **Resolution Rules**: a candidate SHALL match the requested Capability; SHALL have a compatible version; a non-deprecated candidate SHALL be preferred over a deprecated candidate; a suspended or removed object SHALL NOT be a candidate; when multiple candidates are equally valid, the Registry SHALL select exactly one deterministically so that two registries given the same input select the same result. Resolution SHALL be deterministic given the same registry content and the same request. *(Resolution Rules)*
- **Version Compatibility**: Registry SHALL resolve to a version compatible with the request; if multiple compatible versions exist, apply resolution rules; major version changes indicate contract incompatibility; Registry SHALL NOT satisfy a request with a contract-incompatible version; if no compatible version exists, return Version Mismatch. *(Version Compatibility)*
- **Failure Behaviour**: Citizen missing → Error; Capability not found → Not Found; Descriptor corrupted → treated as Failed, Error; Version not compatible → Version Mismatch. All failures observable and defined. *(Failure Behaviour)*
- **Interoperability**: two independently implemented Registries SHALL produce the same resolution result given the same registry content and the same request. *(Interoperability)*
- **Boundaries**: Registry is discovery and resolution only; NOT Approval, Execution, Runtime, Audit, Contract. *(Boundaries)*

### From CONTRACT Specification
- A Contract SHALL declare its compatibility relative to its predecessor. A Consumer SHALL NOT assume compatibility that the Contract does not declare. *(Compatibility Rules)*
- **Version Negotiation**: Both Citizens SHALL agree on a single version before interaction proceeds. A version compatible with both participants SHALL be chosen. If no mutually compatible version exists, negotiation SHALL fail with a defined failure, and no interaction SHALL occur. Preference SHALL be given to a non-deprecated version when available. *(Version Negotiation)*
- Failures: Unknown Contract, Unsupported Version, Invalid Contract, Malformed Payload, Missing Field, Incompatible Contract. *(Failure Behaviour)*
- Boundaries: Contract is NOT Registry; does not discover or resolve. *(Boundaries)*

### From Blueprint G0-001
- **Discovery Resolver**: responsible for discovering and resolving Capabilities on request; returns the Capability that satisfies a request; must not store implementation or redefine identity. *(Component Map / Responsibility Matrix)*
- **Candidate C-02** (open): "how the Discovery Resolver chooses when multiple Capabilities satisfy one request (exact match vs. version-compatible match)" — trade-off between precision and availability.
- Dependency direction: linear, single, no cycle; components depend only toward their frozen source of truth.

---

## Audit 3 — Design Space

Alternatives that remain within the documented constraints. **Not selected; merely enumerated. No decision.**

| # | Alternative | Characterization (within constraints) |
|---|---|---|
| A-01 | **Eager resolution** | Resolution happens at request time and the result is bound immediately, before any downstream Approval/Execution. |
| A-02 | **Lazy resolution** | The Capability is only resolved when it is actually needed (e.g., at Execution), allowing Approval to reference a Capability without binding. |
| A-03 | **Cached resolution** | The outcome of a resolution (for a given request) is retained and reused for identical subsequent requests, subject to registry content changing. |
| A-04 | **Deterministic resolution** | Exact-match-first policy: when candidates are equally valid, selection is fully determined by a repeatable rule (spec already mandates deterministic tie-break; this is the "precision-over-availability" posture). |
| A-05 | **Delegated resolution** | The Registry delegates the final selection decision (or part of it) back to a Citizen/provider context rather than deciding alone. |
| A-06 | **Compatibility-preferred resolution** | Version-compatibility-first policy: a compatible (non-exact) version is preferred over exact-match when availability matters. |
| A-07 | **Administrator-governed resolution** | A governance/policy dimension influences which candidate is preferred (e.g., precedence rules) in addition to match and compatibility. |

> The Registry Specification already mandates **determinism** and **non-deprecated preference**. A-04 and A-06 are therefore not conflicting; they probe how the (already-required) deterministic selection is *positioned* (exact vs. compatible priority). A-07 reflects that Governance/Policy is part of the chain, but the Registry boundary says it does not take Approval's authority — so admin-governed selection must stay inside Registry's discovery/resolution role, not cross into Approval.

---

## Audit 4 — Trade-off Matrix

Per alternative: advantages, disadvantages, impact on Runtime, Registry, Contract. **No decision.**

### A-01 — Eager resolution
| Aspect | Analysis |
|---|---|
| Advantage | Deterministic and simple: the target is fixed before Approval/Execution; supports article VII reproducibility; clear traceability. |
| Disadvantage | Binds early; if the bound Capability becomes unavailable before Execution, requires re-resolution or failure. |
| Runtime impact | Runtime holds an unambiguous target for Approval/Execution from the start. |
| Registry impact | Registry resolves once per request at the front of the chain. |
| Contract impact | Contract can be fixed early, aligned with the resolved version. |

### A-02 — Lazy resolution
| Aspect | Analysis |
|---|---|
| Advantage | Only pays resolution cost when actually needed; tolerates change between Approval and Execution. |
| Disadvantage | The target can differ between what was approved and what is executed — risks the Golden Rule (was the *right* thing approved?); Article VII reproducibility harder to guarantee. |
| Runtime impact | Runtime delays binding; Execution needs its own resolution step. |
| Registry impact | Registry may be queried again later in the chain (or resolution deferred). |
| Contract impact | Version negotiation may be re-done at execution time. |

### A-03 — Cached resolution
| Aspect | Analysis |
|---|---|
| Advantage | Efficiency for repeated identical requests; can still be deterministic if cache invalidation is correct. |
| Disadvantage | Risk of stale binding if registry content changes; must define when cache is invalid (registry content is not static). Determinism requires cache to be content-consistent. |
| Runtime impact | Runtime sees faster repeated resolution; must trust cache consistency. |
| Registry impact | Registry must expose identity/version of the content so cache validity is observable. |
| Contract impact | A cached Contract reference must remain the correct one for the resolved Capability. |

### A-04 — Deterministic resolution (exact-match-first)
| Aspect | Analysis |
|---|---|
| Advantage | Highest precision; exactly what the Registry mandates ("identical request, identical result"); minimal ambiguity. |
| Disadvantage | Lower availability when an exact match is absent but a compatible match exists. |
| Runtime impact | Runtime always gets the exact Capability requested; failures surface as Not Found / Version Mismatch. |
| Registry impact | Selection rule reduces to exact match, then deterministic tie-break. |
| Contract impact | Contract is version-exact; negotiation is straightforward. |

### A-05 — Delegated resolution
| Aspect | Analysis |
|---|---|
| Advantage | Allows the requester/provider context to influence the choice; flexible. |
| Disadvantage | Risks violating Article IV (Citizen never assumes/knows another directly) and Article VII (implicit context = violation) if delegation re-introduces context beyond the request. |
| Runtime impact | Runtime consumes a selection that may depend on delegated context. |
| Registry impact | Registry must decide how much of selection it delegates while keeping the mandated determinism. |
| Contract impact | Contract binding depends on delegated context; must remain observable. |

### A-06 — Compatibility-preferred resolution
| Aspect | Analysis |
|---|---|
| Advantage | Higher availability; a compatible version can satisfy the request when exact is missing. |
| Disadvantage | Weaker precision; the consumer gets *a* compatible version, not necessarily the exact one. |
| Runtime impact | Runtime obtains a usable compatible Capability more often. |
| Registry impact | Registry applies version-compatibility rules as the primary selection. |
| Contract impact | Contract version negotiation becomes more central; must agree a single compatible version. |

### A-07 — Administrator-governed resolution
| Aspect | Analysis |
|---|---|
| Advantage | Governance can set precedence, aligning resolution with policy. |
| Disadvantage | Must stay inside Registry's discovery/resolution role; must not become Approval; adds a governance input that must be deterministic and explicit (no implicit context). |
| Runtime impact | Runtime resolves per governed precedence. |
| Registry impact | Registry honors governed precedence within resolution; boundary to Approval must be explicit. |
| Contract impact | Contract selection may be policy-influenced but still Contract-consistent. |

---

## Audit 5 — Foundation Compliance

Each alternative checked against Mission, Constitution, Governance, Specification, Canonical Architecture. **Elimination of alternatives that violate.**

```
Legend: ✅ compliant · ⚠️ conditional (compliant only under stated conditions) · ❌ violates
```

| Alternative | Mission | Constitution | Governance | Specification | Canonical Arch | Verdict |
|---|---|---|---|---|---|---|
| A-01 Eager | ✅ | ✅ (Art. III, IV, VII) | ✅ | ✅ (Registry deterministic) | ✅ | **Valid** |
| A-02 Lazy | ⚠️ must keep determinism & traceability | ⚠️ Art. VII reproducible needs care | ⚠️ | ⚠️ Approval-vs-Exec target may differ | ⚠️ | **Conditional** |
| A-03 Cached | ✅ if determinism preserved | ⚠️ must avoid "implicit context" / stale | ✅ | ⚠️ deterministic requires content-consistent cache | ✅ | **Conditional** |
| A-04 Deterministic | ✅ | ✅ (Art. VII core) | ✅ | ✅ (Registry mandates) | ✅ | **Valid** |
| A-05 Delegated | ⚠️ | ❌ risk Art. IV + Art. VII (implicit context) | ⚠️ | ⚠️ risk Registry determinism | ⚠️ | **Conditional / at risk** |
| A-06 Compatibility-preferred | ✅ | ⚠️ Art. VII needs explicit rule | ✅ | ✅ (Registry version rules) | ✅ | **Valid** |
| A-07 Admin-governed | ✅ if governed rule explicit | ⚠️ must avoid overlapping Approval / implicit context | ⚠️ must stay in Registry role | ⚠️ must not cross Registry boundary | ⚠️ | **Valid only if boundary respected** |

**Elimination judgment (no final selection):**
- **A-05 (Delegated)** is at the highest compliance risk: delegating selection re-introduces context that Article VII names as a violation ("implicit context") and Article IV names as forbidden direct/knowledge coupling. It is not eliminated absolutely, but it carries the largest constitutional risk and, if pursued, must demonstrably keep resolution deterministic and context-explicit.
- **A-02 (Lazy)** and **A-03 (Cached)** are not eliminated but are conditional: each must preserve determinism and reproducibility (Art. VII) and must not let the resolved target differ from the approved target (Golden Rule / traceability).
- **A-04 and A-06** are the two postures with the clearest compliance: both are explicitly compatible with the Registry Specification (which mandates determinism and version-compatibility handling and non-deprecated preference). They differ in *priority* (exact vs. compatible), which is precisely the open design question of Candidate C-02.

---

## Audit 6 — ADR Readiness

### Is the available information sufficient to write a final C-02 ADR now?

**Not yet.** The constraints are sufficient to bound the design space, and they strongly constrain *how* resolution must behave (deterministic, non-deprecated preferred, suspended/removed excluded, contract-compatible, idempotent, no side effects). However, the information is **insufficient to pick a final posture** without further facts.

### Facts still missing (no solution proposed)
1. **Exact-match vs. compatible-match priority**: the Specification mandates both determinism and version-compatibility handling, but does **not** state whether an exact match must be preferred over a compatible match, or vice versa. This is the core of C-02 and is not resolved by the frozen documents.
2. **Precedence source**: how "non-deprecated preferred" and any equal-validity tie-break interact when multiple non-deprecated compatible candidates exist — the deterministic tie-break rule is mandated but its *ordering basis* is not specified.
3. **Availability semantics**: the Registry defines Not Found / Version Mismatch but does not define whether a compatible-but-not-exact version is an acceptable *resolution outcome* for the requester, or whether the requester must always receive exactly what it asked for.
4. **Re-resolution triggers**: whether and when a resolved binding may be re-evaluated (relevant to A-03 Cached) is not defined; the Registry only says discovery is idempotent with no side effects.
5. **Scope of delegated/contextual input**: there is no frozen statement on whether any context beyond the Capability Request may inform selection; Article VII cautions against implicit context, but the boundary is not explicitly drawn.
6. **Interaction of Resolution with Approval/Execution ordering**: which component observed the resolved Capability at which point (eagerly at Approval vs. lazily at Execution) is an open design decision (ties to Candidate ADRs C-01 and C-08) and is not fixed by the frozen baseline.

---

## Candidate Recommendation

> **No single-remaining valid alternative can be recommended as "the only" option.**
>
> The design space is **not reduced to one** valid path. After compliance checking, at least **A-04 (Deterministic/exact-first)** and **A-06 (Compatibility-preferred)** remain independently valid and constitutional, and the Specification does not establish precedence between them. A-01 (Eager), A-02 (Lazy), A-03 (Cached), and A-07 (Admin-governed, boundary-respecting) also remain conditionally available.
>
> Therefore the ADR remains **open** and no final selection is made in this preparation. More facts (Audit 6 items) are required before a responsible ADR can be written.

---

## STOP Condition

**Aktiv menurut pembacaan saat ini? — TIDAK sepenuhnya; dua kondisi pantau:**

| STOP Condition | Status |
|---|---|
| Blueprint tidak cukup | ⚠️ Sebagian: Blueprint cukup untuk memetakan desain space, tapi tidak menentukan prioritas exact-vs-compatible. |
| Specification saling bertentangan | ❌ Tidak ada kontradiksi eksplisit ditemukan antar Specification (Registry/Contract/Capability selaras). |
| Foundation belum memberi constraint yang cukup | ⚠️ Sebagian: konstrain kuat namun tidak *mengambil keputusan* exact-vs-compatible; ini bukan cacat Foundation, melainkan keputusan arsitektural yang memang sengaja dibuka (C-02). |
| Tidak mungkin memilih secara arsitektural | ⚠️ Saat ini ya — hanya tersisa satu alternatif valid? Tidak. Lebih dari satu tetap terbuka. |

**Kesimpulan STOP:** STOP **tidak aktif sebagai blokade** (tidak ada kontradiksi, tidak harus berhenti total), tetapi **ADR tidak dapat ditulis final sekarang** karena memerlukan keputusan atas fakta yang belum tersedia (Audit 6). Dengan demikian:
- **TIDAK membuat ADR.**
- **TIDAK mengambil keputusan.**
- Hanya melaporkan bukti di bawah ini.

---

## Evidence / Output Summary

1. **Problem Statement** — Resolution adalah jembatan wajib (discovery→binding) yang menjaga determinisme (Art. VII), de-coupling (Art. IV), dan kebenaran rantai Approval–Execution–Audit.
2. **Constraint Register** — dikumpulkan dari Mission, Constitution (Art. III/IV/VII/IX), Capability Spec, Registry Spec, Contract Spec, Blueprint G0-001. Termasuk mandat: deterministik, idempotent, no side effect, non-deprecated preferred, suspended/removed excluded, exact-one deterministic, contract-compatible, no direct coupling.
3. **Design Space** — 7 alternatif (A-01…A-07), termasuk yang dicontohkan (eager/lazy/cached/deterministic/delegated) plus compatible-preferred dan admin-governed.
4. **Trade-off Matrix** — untuk setiap alternatif: keuntungan, kelemahan, dampak Runtime/Registry/Contract.
5. **Compliance Matrix** — verifikasi 7 alternatif terhadap Mission/Constitution/Governance/Spec/Canonical Arch; tidak ada eliminasi mutlak, tapi A-05 berisiko tertinggi, A-02/A-03 kondisional.
6. **ADR Readiness** — Belum siap: 6 fakta masih kurang.
7. **Candidate Recommendation** — Lebih dari satu alternatif valid tetap terbuka (minimal A-04 & A-06); ADR tetap open.
8. **STOP Condition** — Tidak menjadi blokade, tapi ADR tidak dibuat sekarang.

### Final Statement

G1-001 menyelesaikan **persiapan penuh** untuk ADR C-02: problem statement dirumuskan, seluruh constraint yang ada dikumpulkan, design space diidentifikasi, trade-off dianalisis, compliance diverifikasi, dan kesenjangan informasi didaftarkan. **Keputusan tidak diambil.** ADR C-02 akan layak ditulis ketika fakta-fakta di Audit 6 tersedia (khususnya prioritas exact-vs-compatible, basis urutan tie-break, dan titik observasi resolution dalam rantai Approval/Execution).
