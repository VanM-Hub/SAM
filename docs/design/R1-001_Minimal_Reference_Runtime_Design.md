# R1-001 — Minimal Reference Runtime Design

**Version:** 1.0
**Status:** Read-only Design (defines the minimal conceptual shape of the first Reference Runtime, derived strictly from frozen baseline; **not** implementation, **not** coding, **not** technology selection)
**Authority:** Derived from the Constitution; realizes the Reference Runtime Blueprint (G0-001) as validated by R0-001 (A — Ready).
**Mode:** Read-only design. Uses ONLY: Mission, Constitution, Philosophy, Governance, Glossary, Canonical Architecture, Specification Layer (CITIZEN/CAPABILITY/REGISTRY/CONTRACT/APPROVAL/EXECUTION/AUDIT + SPECIFICATION_FREEZE), G0-001 Blueprint, R0-001 Validation.

> This is **not** implementation and **not** coding.
> It **creates no ADR, no code, no pseudocode, no interface, no class, no namespace, no API, no payload, no data format, no algorithm; selects no language/framework/storage/transport/runtime platform; changes no Foundation/Specification/Blueprint.** It only derives the minimal conceptual shape and reports.
> Where the description cannot proceed without naming a mechanism (e.g., how Approval decides), that mechanism is **not** chosen here — it is deferred to the Candidate ADR (C-01…C-08) layer already declared open by the Blueprint.

---

## Source Anchors (verbatim, read in full)

| Source | Anchor |
|---|---|
| GOVERNANCE | "Governance allocates authority." · Runtime Governance: "own one bounded responsibility / publish capabilities / expose immutable contracts / support certification / expose health / participate in auditing" · "Runtime independence is mandatory." · Runtime Creation Rules: a new Runtime exists only if it "governs an independent capability domain / owns a distinct responsibility / can evolve independently / benefits from constitutional isolation" |
| SAM_ARCHITECTURE | Responsibility Matrix: "**Runtime** | Govern one bounded capability domain | **Must not** take strategic decisions" · Layering Model: "Citizens / Runtimes (capability units)" · "Each layer has one primary responsibility" · "Layers communicate only through Contracts and Capability-based discovery (Registry), never through implementation knowledge" · Approved Execution Flow: "Mission → Governance check → Approval → Execution → Verification → Audit" |
| SPECIFICATION_FREEZE | "**Specification Layer** — Citizen, Capability, Registry, Contract, Approval, Execution, Audit." · "Evolution through ADR" |
| G0-001 Blueprint | Component Map (7 components) · Responsibility Matrix · Dependency Diagram (linear single-direction acyclic) · 8 Candidate ADRs (C-01…C-08) |
| R0-001 Validation | All 7 components realizable (YES×7); A — Ready; final readiness gate passed |

> **Mapping note:** SPECIFICATION_FREEZE names exactly seven Specification concepts, and G0-001 names exactly seven Runtime components, 1:1 in the same order (Citizen → Capability → Registry → Contract → Approval → Execution → Audit). The Minimal Reference Runtime is therefore **the realization of the Specification Layer for one bounded capability domain**, no more and no less. This mapping is the load-bearing fact of this design.

---

# Audit 1 — Runtime Boundary

**Question:** what is inside Runtime, what is outside Runtime, and what is the boundary?

### What is inside the Runtime

The Minimal Reference Runtime contains exactly the seven responsibility containers that realize the Specification Layer for its own bounded capability domain:

| Inside (conceptual, per Spec) | Realizes Spec |
|---|---|
| Citizen Host | CITIZEN (identity, lifecycle, capability publication, contracts, audit identity, health, certification) |
| Capability Manager | CAPABILITY (lifecycle, immutability, replacement) |
| Discovery Resolver | REGISTRY (discovery, deterministic resolution) |
| Contract Enforcer | CONTRACT (structure, compatibility, version negotiation) |
| Approval Coordinator | APPROVAL (decision states, lifecycle) |
| Execution Scheduler | EXECUTION (approved operations, idempotency) |
| Audit Recorder | AUDIT (traceability records) |

### What is NOT inside the Runtime

Per Layer Model and each Spec's "Boundaries", the Runtime does **not** contain:

- **Strategic decision** — SAM_ARCHITECTURE: Runtime "Must not take strategic decisions" (belongs to Mission/Governance/Model Layer).
- **External access** — Providers/Connectors implement external access; Runtime does not.
- **User interface / business logic** — Presentation layer; outside Runtime.
- **Any governance/authority creation** — Runtime neither allocates authority nor defines identity (Governance "does not define identity"; Runtime "Must not take strategic decisions").
- **Any behavior of the other Spec domains it only references** — e.g., Registry is not executed by the Runtime's Execution; Audit does not decide; Approval does not run.

### What is the boundary

The boundary between the Runtime and everything else is **the two and only two mechanisms the frozen baseline permits** (SAM_ARCHITECTURE L89):

1. **Contracts** — the shape of communication; immutable.
2. **Capability-based discovery (Registry)** — how a capability is found.

No implementation knowledge crosses this boundary. A component "inside" communicates with other Runtimes/Citizens only through these two mechanisms; the boundary is **structural (what kind of interaction), not a physical border or a firewall**, and it imposes no topology (deployment topology is explicitly out of scope — GOVERNANCE Long-Term Governance: governance "should remain valid regardless of … deployment topology, runtime distribution", and CONTRACT evolution "does not create a Runtime lifecycle").

**Boundary verdict:** the Runtime is the realization of the Specification Layer for one bounded capability domain; its outer surface is Contracts + Registry; everything else (strategic decision, external access, presentation, governance/authority creation) is outside.

---

# Audit 2 — Runtime Responsibility

**Requirement:** total derived responsibility; no duplication, no missing, no new.

### Derivation rule

From GOVERNANCE Runtime Governance ("Every Runtime shall: own one bounded responsibility, publish capabilities, expose immutable contracts, support certification, expose health, participate in auditing") + SAM_ARCHITECTURE ("Govern one bounded capability domain; must not take strategic decisions") + the seven Specifications' behavior. Each responsibility has **one and only one owning component** (Blueprint §2 "one domain / one owner"); no two components own the same responsibility; no responsibility lacks an owner.

### Runtime Responsibility Matrix

| # | Responsibility (derived) | Owning component | Source (anchor) | Duplicated? | Missing? | New? |
|---|---|---|---|---|---|---|
| R1 | Own the Runtime's bounded capability domain | Citizen Host (as the Runtime's governing unit) | GOV: "own one bounded responsibility"; SAM: "Govern one bounded capability domain" | No | No | No |
| R2 | Publish capabilities (explicitly, discoverable, immutable) | Capability Manager | GOV: "publish capabilities"; CITIZEN: "SHALL explicitly publish every capability" | No | No | No |
| R3 | Expose immutable contracts | Contract Enforcer | GOV: "expose immutable contracts"; CONTRACT: "interoperable agreement" | No | No | No |
| R4 | Discover & resolve capabilities | Discovery Resolver | REGISTRY: "purpose … discoverable and resolvable", "Resolution SHALL be deterministic" | No | No | No |
| R5 | Produce authorization decision before execution | Approval Coordinator | APPROVAL: "produce a binding authorization decision", lifecycle | No | No | No |
| R6 | Apply only approved operations (idempotent) | Execution Scheduler | EXECUTION: "perform an operation that has been approved"; idempotency rules | No | No | No |
| R7 | Make activity traceable (backward chain) | Audit Recorder | AUDIT: "Traceability Rules" | No | No | No |
| R8 | Support certification | Citizen Host | GOV: "support certification"; CITIZEN certification section | No | No | No |
| R9 | Expose health | Citizen Host | GOV: "expose health"; CITIZEN health section | No | No | No |
| R10 | Participate in auditing | Audit Recorder (observes) + all components (expose audit identity) | GOV: "participate in auditing"; CITIZEN Audit Identity | No | No | No |

**Verdict: 10 responsibilities derived; 10 owned; 0 duplicated; 0 missing; 0 new.** Every derived responsibility maps to a verbatim Foundation/Spec requirement; none is invented (R10's "participate" is spread across every component exposing audit identity, matching AUDIT Traceability Rules referencing Execution/Approval/Contract/Capability — a single shared mechanism, not duplicated ownership).

> R8/R9 map to Citizen Host because CERTIFICATION and HEALTH are properties of the Citizen/Runtime governing unit (CITIZEN certifies "constitutional compliance"; health excludes business meaning), not of a Capability or a message. This is consistent with GOVERNANCE Runtime Governance listing them as *Runtime* requirements.

---

# Audit 3 — Component Interaction

**Rule:** only *who talks to whom, when, why* — never *how*.

### Derivation rule

From the Blueprint's linear single-direction chain (Citizen → Capability → Registry → Contract → Approval → Execution → Audit) + the Approved Execution Flow (`Mission → Governance check → Approval → Execution → Verification → Audit`) + each Spec's "Relationship with" sections. Interaction is a **linear causality along the chain**; the only cross-boundary mechanism is Contracts + Registry.

### Component Interaction Matrix

| From | To | When | Why (derived) |
|---|---|---|---|
| Citizen Host | Capability Manager | upon Citizen registration | to publish/expose capabilities (R2) |
| Capability Manager | Discovery Resolver | when a capability must be found | to make the capability discoverable (R4) |
| Discovery Resolver | Contract Enforcer | upon successful resolution | to engage the contract governing the capability (R3) |
| Contract Enforcer | Approval Coordinator | before any operation on the contract | Authorization must precede execution (R5; APPROVAL "gate between intent and execution") |
| Approval Coordinator | Execution Scheduler | only after Approval decision | Execution begins after Approval completes (R6; APPROVAL/EXECUTION "Relationship with Execution") |
| Execution Scheduler | Audit Recorder | after execution produces activity | to make the activity traceable (R7; EXECUTION "produces operational information that Audit may record") |
| (All components) | Registry | on every external interaction | the only permitted discovery mechanism (boundary: Registry reduces coupling) |

**Verdict:** communication is linear and `who→whom` is unambiguous from the Specs; `when` is fixed by the lifecycle/relationship sections; `why` is the responsibility transfer (R1→R7). **No additional interaction is invented** (e.g., Audit does not feed back; Execution does not bypass Approval; Registry never executes). The one recurrent edge — every external interaction goes through Registry — re-states the boundary mechanism, not a new behavior.

---

# Audit 4 — Runtime Invariants

**Requirement:** extract only invariants already present in the frozen baseline; **create none**.

### Invariant register (extraction map)

Per SPECIFICATION_FREEZE, invariants are settled by the Specification; the Runtime must preserve, not invent.

| # | Invariant (extracted verbatim / near-verbatim) | Source |
|---|---|---|
| I1 | Approval always precedes Execution — "Execution begins after Approval completes"; "may be executed only after its Approval has produced a decision" | APPROVAL "Relationship with Execution" + EXECUTION |
| I2 | Registry does not execute — "Registry never executes capabilities" | CAPABILITY / REGISTRY boundaries |
| I3 | Audit does not affect outcome — "Audit does not affect the outcome of Execution"; "Audit has no influence over what Execution produces" | AUDIT "Relationship with Execution" |
| I4 | Registry never decides; Approval is a decision not a discovery — Approval "is not discovery (Registry)"; Registry never decides authorization | APPROVAL + CONTRACT boundaries |
| I5 | Discovery only through Registry — "Citizens SHALL NOT discover each other directly" | CITIZEN |
| I6 | Execution performs only after approval — Execution "does not determine whether the operation is permitted" | EXECUTION |
| I7 | Contract defines structure only — "does not define who runs it, who approves it, who discovers it, or who executes it" | CONTRACT scope |
| I8 | Approval completes at decision; does not run — "Approval completes at the decision. Execution begins after Approval completes" | APPROVAL "Relationship with Execution" |
| I9 | Execution performs, does not record — "Execution has no responsibility to record, retain, or report" | EXECUTION "Relationship with Audit" |

**Verdict: nine invariants extracted; zero created.** Each traces to a verbatim statement. The set is minimal and complete for the chain's correctness: they guarantee (a) authorization ordering, (b) separation of the role boundaries (no component exceeds its Spec "Boundaries"), and (c) non-interference by Audit. **No new invariant is proposed.**

---

# Audit 5 — Runtime States

**Question:** does Foundation support a *whole-Runtime* conceptual state?

### Honest finding first

The frozen baseline specifies **lifecycles for each component's artefacts** — CITIZEN lifecycle (Declared→Registered→Certified→Available→Active→Suspended→Deprecated→Retired), CAPABILITY/REGISTRY/CONTRACT/APPROVAL/EXECUTION/AUDIT lifecycles, each with terminal states. It does **not** declare a single whole-Runtime state machine, and SPECIFICATION_FREEZE does not add one.

Per the audit rule ("If Foundation does not support, report"), I report: **the Foundation specifies component- and artefact-level states, but does not define a whole-Runtime aggregate state.** Any composite "Runtime state" (e.g., a single status combining health, lifecycle, certification) would be an **invention**, not an extraction.

### Runtime State Model (derived only from what is specified)

What *is* derivable without invention is that the Runtime's observable condition is **constituted** — not aggregated — from the specified sub-states:

| Constituting observable (specified) | Specified states (verbatim source) |
|---|---|
| Citizen/Runtime lifecycle | Declared, Registered, Certified, Available, Active, Suspended, Deprecated, Retired (CITIZEN; "may extend … may not remove constitutional states") |
| Health | Healthy, Warning, Unavailable, Degraded, Unknown (CITIZEN; "SHALL NOT include business meaning") |
| Certification | Certification verifies compliance; certifiable per Citizen Specification (CITIZEN) |
| Approval lifecycle | Created…Archived (APPROVAL) |
| Execution lifecycle | Created…Archived (EXECUTION) |
| Audit lifecycle | Recorded, Verified, Archived (AUDIT) |

**Constraint honored:** citizenship lifecycle states "may not remove constitutional states" — so the Runtime's own lifecycle is a **subset** of the constitutional Citizen states, never a new state. The Runtime does **not** invent a parallel state machine.

**Verdict:** the Foundation supports an **observable, component-constituted Runtime condition** (via Citizen lifecycle + health + the 7 audit/execcomponent lifecycles), but does **not** supply a single whole-Runtime aggregate state, and this design does **not** invent one. Where a design phase later needs a unified status, that is a Candidate-ADR decision (C-06/C-08 domain), not a frozen fact.

---

# Audit 6 — Runtime Failure Boundary

**Question:** what failures does the Runtime handle; what failures are not the Runtime's responsibility?

### Failures the Runtime handles (each defined in its Spec)

| Failure | Owning component | Source |
|---|---|---|
| Capability not found / version mismatch / registry error | Discovery Resolver | REGISTRY failure types |
| Unknown / unsupported / invalid / incompatible contract, malformed payload, missing field | Contract Enforcer | CONTRACT failure types |
| Missing/unknown capability, resolution failed, invalid/expired request, approval conflict | Approval Coordinator | APPROVAL failure types |
| Missing/invalid approval, capability unavailable, timeout, execution failure | Execution Scheduler | EXECUTION failure types |
| Missing/broken/incomplete/invalid/duplicate reference, archived reference | Audit Recorder | AUDIT failure types |

### Failures NOT the Runtime's responsibility

Per each Spec's boundaries and the Layer Model:

| Failure | Why not Runtime |
|---|---|
| Strategic/architectural decision errors | Runtime "Must not take strategic decisions" (SAM_ARCHITECTURE) |
| External-access / communication failures with the outside world | Provider/Connector layer (outside Runtime) |
| Business-usefulness of a capability | Certification "SHALL NOT evaluate business usefulness" (CITIZEN) |
| Governance/authority/config errors | Governance is outside Runtime; Runtime does not create governance |
| Presentation/UI failures | Presentation layer (outside Runtime) |

**Verdict:** the Runtime handles exactly the failures defined by its seven Specifications (failures are "observable and defined by this specification" in each); it does **not** assume responsibility for strategic, external, presentation, business-usefulness, or governance errors — consistent with its boundary (Audit 1). **No extra failure responsibility is added; none is dropped.**

---

# Audit 7 — Runtime Minimality

**Question:** could one component be removed? If yes → Blueprint too large; if no → Blueprint truly minimal.

### Removal test (one at a time)

| If removed | What breaks (derived) | Verdict |
|---|---|---|
| Citizen Host | No governing unit to "own one bounded responsibility", publish/health/certify — the Runtime's *raison d'être* (GOV R1/R8/R9) | **Cannot remove** |
| Capability Manager | No capabilities published → nothing to discover; chain collapses at step 2 | **Cannot remove** |
| Discovery Resolver | Capabilities could not be resolved deterministically; "Citizens SHALL NOT discover each other directly" violated | **Cannot remove** |
| Contract Enforcer | No immutable contract shape → interoperation and version negotiation undefined; CONTRACT boundary lost | **Cannot remove** |
| Approval Coordinator | No authorization gate → violates I1 "approval always before execution"; Execution "act without approval" is the *must-not* (SAM_ARCHITECTURE: Execution "Act without approval") | **Cannot remove** |
| Execution Scheduler | No application of approved operations → R6 lost; whole "apply approved work" responsibility missing | **Cannot remove** |
| Audit Recorder | No traceability → violates "Audit is mandatory. Not optional" (GOV Audit Governance) | **Cannot remove** |

**Verdict:** removing **any** component breaks a frozen responsibility or invariant. The Blueprint is **truly minimal** — the seven components are the least decomposition that realizes the Specification Layer without violating a Foundation/Spec requirement. **The Blueprint is not too large.**

> Note on the boundary pinning: this is consistent with G2-001 (verdict B — no governance domain is missing) and G0-001/G2-003 (framework stable, complete). The seven components do **not** add governance/authority; they are the minimal realization of what the frozen baseline already requires.

---

# Audit 8 — Runtime Stability

**Question:** does the conceptual Runtime structure change at 100 / 1000 / 10000 capabilities?

### Simulation

| Capability scale | Structure | Verdict |
|---|---|---|
| 100 | 7 components; linear chain; boundary = Contracts + Registry | **NO change** |
| 1000 | same 7 components; same chain; same boundary | **NO change** |
| 10000 | same 7 components; same chain; same boundary | **NO change** |

### Reason

The structure is **not** a function of capability count. It is fixed by:
1. **SPECIFICATION_FREEZE L18** — the Specification Layer names seven concepts, independent of how many Capabilities are instantiated. One Capability or ten thousand, the same seven concepts realize them.
2. **Registry resolution is deterministic given content** (REGISTRY) — scale changes the *registry content*, never the resolver's role; scale is a content/volume property, not a structural property.
3. **Lifecycle/failure/invariant set** — defined per concept, not per Capability; scale affects instances, not the state machines.
4. **Constitution layer is count-independent** — trust/product goals do not change with volume (Mission/Constitution are not volumetric).

Scale raises **only content- and mechanism-level concerns** (e.g., how Registry handles very large register content) — precisely the kind of decision that belongs to **Candidate ADRs (C-02 resolution policy, C-06 deployment topology)** at the design phase, **not** a reshaping of the conceptual structure.

**Verdict: NO.** The conceptual Runtime structure is stable across 100 / 1000 / 10000 capabilities: **YES — structurally unchanged.**

---

## Output

1. **Runtime Boundary** — Audit 1: inside = 7 Specification-realizing containers; outside = strategic decision/external access/presentation/authority creation; boundary = **Contracts + Registry** (the two permitted mechanisms, no implementation knowledge across).
2. **Runtime Responsibility Matrix** — Audit 2: **10 responsibilities (R1–R10), 10 owners, 0 duplicated, 0 missing, 0 new.**
3. **Component Interaction Matrix** — Audit 3: linear `From→To→When→Why` along the chain; only cross-boundary mechanism = Contracts + Registry; **no invented interaction.**
4. **Runtime Invariant Register** — Audit 4: **9 invariants (I1–I9) extracted, 0 created.**
5. **Runtime State Model** — Audit 5: **component-constituted observable condition** (Citizen lifecycle subset + health + 7 artefact lifecycles); **no whole-Runtime aggregate state invented**; Foundation does not support one, reported honestly.
6. **Runtime Failure Boundary** — Audit 6: Runtime handles the 7-vector defined failure set; does **not** assume strategic/external/presentation/business-usefulness/governance failures.
7. **Runtime Minimality Verdict** — Audit 7: **truly minimal** — removing any component breaks a frozen responsibility/invariant; **Blueprint not too large.**
8. **Runtime Stability Verdict** — Audit 8: **NO structural change** at 100/1000/10000; **YES, stable** — structure is count-independent (content/mechanism-only scale concerns are Candidate-ADR matters).
9. **STOP Condition** — see below. ✅

---

## STOP Condition

**Tidak aktif.** Hentikan segera bila:

| Trigger | Present? | Evidence |
|---|---|---|
| Runtime membutuhkan **domain baru** | **Tidak** | 7 komponen memetakan 1:1 ke Specification Layer (Citizen, Capability, Registry, Contract, Approval, Execution, Audit) — tidak ada domain baru. |
| Runtime membutuhkan **authority baru** | **Tidak** | Setiap authority dialokasikan eksplisit (Audit 2); Runtime "Must not take strategic decisions"; tidak ada authority baru yang dituntut. |
| Runtime membutuhkan **perubahan Specification** | **Tidak** | Semua responsibility/failure/state/invariant diekstrak dari Specification yang ada, tanpa modifikasi. |
| Runtime membutuhkan **perubahan Foundation** | **Tidak** | Tidak ada temuan yang mengharuskan ubah Mission/Constitution/Philosophy/Governance; minimality & stability mengonfirmasi kecukupan. |
| Runtime **tidak dapat dijelaskan tanpa memilih teknologi** | **Tidak** | Seluruh desain di atas menggambarkan Runtime secara konseptual (komponen, responsibility, interaksi, invariant, state, failure) tanpa menyebut bahasa/framework/storage/transport/platform. Satu-satunya tempat mekanisme dibutuhkan (Approval decision computation, Registry scale handling) secara eksplisit **didefer ke Candidate ADR C-01…C-08**, dan tidak wajib dipilih untuk mendeskripsikan struktur. |

→ **Karena tidak ada kondisi STOP yang terpenuhi, STOP tidak aktif.**

**Akibat (per arahan):**
- **Tidak memberi solusi.**
- **Tidak membuat ADR.**
- Hanya melaporkan model konseptual minimal.

---

## Final Statement

R1-001 menurunkan **bentuk konseptual Runtime paling minimal** yang tetap memenuhi seluruh Foundation, Specification, dan Blueprint, berbasis dokumen:

**Model minimal:** *The Minimal Reference Runtime is the realization of the Specification Layer for one bounded capability domain.* Tujuh komponen (Citizen Host, Capability Manager, Discovery Resolver, Contract Enforcer, Approval Coordinator, Execution Scheduler, Audit Recorder) memetakan 1:1 ke tujuh konsep Specification (CITIZEN, CAPABILITY, REGISTRY, CONTRACT, APPROVAL, EXECUTION, AUDIT) — persis yang dinyatakan SPECIFICATION_FREEZE, dan persis rantai G0-001.

**Bukti minimalitas & stabilitas:**
- **10 responsibility, 10 owner, 0 ganda, 0 hilang, 0 baru** (Audit 2).
- **9 invariant diekstrak, 0 diciptakan** (Audit 4) — menjaga otorisasi (I1), batas peran (I2–I6), non-interferensi (I7–I9).
- **7 komponen semuanya tidak dapat dihapus** (Audit 7) → Blueprint **benar-benar minimal**, bukan terlalu besar.
- **Struktur stabil** pada 100/1000/10000 capability (Audit 8) — struktur konseptual tidak berubah; isu volume/mechanism adalah urusan Candidate ADR, bukan reshaping struktur.
- **Boundary bersih:** di dalam = 7 container; di luar = strategic decision, external access, presentation, authority creation; permukaan = **Contracts + Registry** (satu-satunya mekanisme yang diizinkan baseline, tanpa knowledge implementasi menyeberang).

**Arti strategis (menjawab arahan Chief Architect):** R1-001 mencapai tujuan Anda — menghasilkan **model konseptual Runtime minimum yang stabil**. Karena model ini kini terdefinisi dan tervalidasi minimal, **delapan Candidate ADR (C-01…C-08) dapat mulai diputuskan satu per satu dengan konteks yang jauh lebih jelas**: tiap keputusan (Approval decision computation, Registry scale handling, idempotency realization, failure propagation, deployment topology, external-access boundaries, verification point) kini punya anchor komponen, invariant, dan boundary yang eksplisit. Keputusan-keputusan tersebut tetap **didefer ke lapisan ADR**, bukan di selesaikan di dokumen ini (read-only design).

**STOP tidak aktif** — tidak ada kebutuhan domain/authority baru, tidak ada perubahan Specification/Foundation, dan model dapat dijelaskan sepenuhnya tanpa memilih teknologi. Sesuai arahan: **tidak memberi solusi, tidak membuat ADR, tidak mengubah Foundation/Specification/Blueprint — hanya melaporkan model konseptual minimal.**
