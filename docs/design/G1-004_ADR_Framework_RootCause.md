# G1-004 — ADR Framework Root Cause Analysis

**Version:** 1.0
**Status:** Root Cause Analysis (Read-only — no decision, no fix, no ADR)
**Authority:** Derived from the Foundation; root-cause of the G1-003 findings, not a corrective action.
**Owner:** Project SAM
**Mode:** Read-only. Determines *whether* the three G1-003 findings are independent defects or one design fault, without changing the template, writing an ADR, or proposing a solution.

**Depends On:**
- Foundation (Mission, Constitution, Philosophy, Governance, Glossary, Canonical Architecture)
- Specification Layer (frozen)
- SPECIFICATION_FREEZE.md
- ADR_TEMPLATE.md
- G1-001 (6 facts missing → 1 core decision)
- G1-002 (Decision Discovery; F-collapse; dependency graph)
- G1-003 (ADR Architecture Audit; 3 findings)

> This document **writes no ADR, changes no template, proposes no solution**.
> It only finds the root cause, per the directive: *fix the source, not the symptom.*

---

## The Three Findings Under Analysis (from G1-003)

| ID | Finding | G1-003 Source |
|---|---|---|
| **T1** | **Authority Leakage** — ADR_TEMPLATE has no mandatory compliance gate; `Decision`/`Implementation Notes` can shift Capability / Specification without touching the freeze. | Audit 2 |
| **T2** | **Second Specification** — the freeze routes formats/protocols/schemas into ADR, but the template has no cross-ADR supersede and no contradiction detection; a large corpus hardens into an informal spec. | Audit 6 |
| **T3** | **Dependency Graph Incomplete** — missing Blueprint G0-001, SPECIFICATION_FREEZE, Model Layer, GLOSSARY, REPOSITORY_CONVENTION; Citizen/Provider/Runtime wrongly modeled as strict chain; Presentation → Runtime instead of Runtime Service. | Audit 8 |

---

## Audit 1 — Causal Graph

Tracing each finding to its immediate causes, then onward until irreducible.

### T1 → Authority Leakage
```
T1 Authority Leakage
└─ 1a · No mandatory compliance gate between Decision draft and Accepted
     └─ 1a1 · Template treats verification as a checklist item, not a gate
            ("Author Checklist" is advisory, not enforced before Status=Accepted)
     └─ 1a2 · Decision zone is not declared: no statement of who decides a
              decision's scope (architect vs. spec owner) before acceptance
└─ 1b · Implementation Notes is permitted inside an ADR
     └─ 1b1 · Template explicitly labels the section "implementation-oriented"
     └─ 1b2 · No rule isolates non-architectural content from architectural content
```

### T2 → Second Specification
```
T2 Second Specification
└─ 2a · Freeze routes detail (formats/protocols/schemas) into the ADR layer
     └─ 2a1 · Foundation/Spec no longer store a single canonical representation
              of that detail (because freeze) → detail collects in ADRs
└─ 2b · No cross-ADR supersede mechanism
     └─ 2b1 · Metadata carries only "Related ADRs", no "Supersedes: ADR-X"
     └─ 2b2 · Status is tracked per-document, not per-corpus
└─ 2c · No contradiction detection across ADRs
     └─ 2c1 · No concept of an ADR corpus as a governed whole
```

### T3 → Dependency Graph Incomplete
```
T3 Dependency Graph Incomplete
└─ 3a · Binding artifacts (Blueprint, SPECIFICATION_FREEZE, Model Layer,
        GLOSSARY, REPOSITORY_CONVENTION) are not graph nodes
     └─ 3a1 · REPOSITORY_CONVENTION / DOCUMENT_STRUCTURE treats these as
              "supporting assets", not binding dependencies
└─ 3b · Citizen/Provider/Runtime modeled as a strict linear chain
     └─ 3b1 · Template/slide does not enforce the Citizen taxonomy from Philosophy
              (Runtime is a Citizen, Provider is a Citizen…)
└─ 3c · Presentation edge points to Runtime wholesale, not Runtime Service
     └─ 3c1 · Philosophy mandates "communicate only through Runtime Service"
```

Irreducible leaf causes:
- **1a1** — verification is advisory, not a gate.
- **1a2** — decision zone (who decides scope) is undeclared.
- **1b** — implementation content is hosted inside an architectural record.
- **2a** — freeze pushes detail into ADR with no dedicated guardian layer.
- **2b** — no corpus-level supersede/state.
- **2c** — no cross-ADR contradiction check.
- **3a** — binding artifacts not recognized as dependency nodes.
- **3b** — Citizen taxonomy not enforced in the graph.

---

## Audit 2 — Root Cause Reduction

Can the three findings reduce to three, two, or one root cause? (Report as-is; no forcing.)

Grouping the irreducible leaves by *shared origin*:

| Leaf causes | Shared origin |
|---|---|
| 1a1 (no gate), 2b (no supersede), 2c (no contradiction), 3a (artifacts not nodes) | The template models an ADR as a **standalone, stateless document** with no formal relation to (i) the frozen documents as authority, (ii) other ADRs as a corpus, (iii) other binding artifacts. No representation of relations → no gate → no supersede → no contradiction check → binding artifacts invisible. = **Root Cause A** |
| 2a (freeze routes detail into ADR), 1b (impl. notes admitted) | The freeze policy **delegates design/format detail to the ADR layer without establishing a guardian that keeps that layer consistent**; and the template hosts such detail without a zone rule. = **Root Cause B** |

**Result of reduction: 3 findings → 2 root causes.**

- **Root Cause A — Structural (template/stateless):** ADR_Framework is built as a collection of independent documents, not as a *governed decision layer* with explicit relations to authority and to the corpus.
- **Root Cause B — Policy (freeze):** the freeze *routes design detail into* the ADR layer without simultaneously defining how that layer guards consistency; the template then hosts that detail (Implementation Notes) without an isolation rule. Root Cause B is the *upstream trigger* that gives Root Cause A its substance (a layer that holds detail must be governed — but it is not).

**On forcing one root cause (reported, not asserted):** it is *possible* to merge A and B into a single root — *"the ADR layer is not defined as a governed decision layer, yet the freeze assigns it to hold design detail"* — where A is the structural manifestation and B is the policy consequence. Per the directive *"do not force the result"*, we do **not** collapse them: B is a distinct upstream policy trigger (it originates in the freeze document), and A is a distinct structural defect (it originates in the template). Reduction to **two** is the defensible, honest verdict; the single-root collapse is noted as a possibility only.

---

## Audit 3 — Principle Violation

For each root cause, the principles (supported by the Foundation) that it violates.

### Root Cause A (template/stateless)
| Principle | Violated? | How |
|---|---|---|
| **Authority Chain** | **Yes** | No mandatory compliance gate → the chain from a decision to its frozen authority is broken; a decision can be Accepted without tie-back to authority. |
| **Single Source of Truth** | **Yes** | No contradiction detection → SSOT for design detail is ambiguous between ADR and Specification; truth is not singular. |
| **Separation of Responsibility** | **Yes** | Implementation Notes mixes architectural and implementation content with no zone → responsibilities not separated. |
| **One Decision One ADR** | **Yes** (latent) | Without corpus-level supersede, an ADR can accumulate cross-decision content; the "one ADR = one decision" discipline is unenforced. |

### Root Cause B (freeze policy)
| Principle | Violated? | How |
|---|---|---|
| **Canonical Promotion** | **Yes** | No clear path for ADR-held detail to *promote* to canonical/terminal status; detail floats in ADRs indefinitely, never consolidated. |
| **Specification Freeze** | **Yes** (implicitly) | The freeze aims to stabilize the Boundary, but by routing detail into an ungoverned layer it blurs Spec↔ADR; stabilization is undermined. |
| **Single Source of Truth** | **Yes** (aggravated) | B deepens the SSOT ambiguity introduced by A. |

No root cause maps to a principle in the directive list that does **not** fit; all map to principles genuinely supported by the Foundation. (Citizen taxonomy is relevant to T3/3b — a Foundation supported notion — but T3 reduces to A + a taxonomy-not-enforced point; see Layer Mapping.)

---

## Audit 4 — Layer Violation

For each root cause, the single layer where it is born. If cross-layer, explain why.

| Root Cause | Layer (born) | Rationale |
|---|---|---|
| **A** | **ADR Framework** | Relations to authority, corpus, and binding artifacts are all matters of the ADR structure/mechanics — the template. Born here. Not Foundation (does not alter Mission/Constitution/Philosophy), not Specification (Spec is frozen content, not mechanism). |
| **B** | **ADR Framework**, triggered upstream by **Specification Freeze** → **cross-layer** | The *hosting* defect (detail stored unguarded, Implementation Notes admitted) is in the ADR Framework. But the *cause* is the freeze policy that routes detail into that layer. Because the directive asks for one layer with an explanation when cross-layer: **B is born in ADR Framework, but its upstream trigger lives in Specification Freeze** → declare cross-layer (ADR Framework ↔ Specification Freeze), not purely one. |
| T3-specific residue (Citizen/Provider/Runtime taxonomy not enforced) | **Foundation** (partial) | The mis-modeling stems from Philosophy's Citizen taxonomy not being enforced in the graph — a Foundation-adjacent gap. Noted as *partial* Foundation component; the graph-structure part of T3 reduces to Root Cause A. |

**Layer summary:** Root Cause A = ADR Framework. Root Cause B = ADR Framework ↔ Specification Freeze (cross-layer). A partial Foundation component (Citizen taxonomy) surfaces only through T3.

---

## Audit 5 — Historical Simulation

Imagine G1-003 was never performed. Simulate 100 ADRs written with the current template. Focus on *documentation evolution*, not implementation.

Most likely outcome over the 100-ADR lifecycle:

1. **Consistency collapse under volume.** At 1–2 ADRs the corpus looks fine. By ~20–30, redundancies and the freeze-routed detail (formats/protocols) start to disagree between ADRs; by 100, the corpus is internally inconsistent.
2. **An informal parallel Specification hardens.** Because detail lives in ADRs (freeze) with no supersede/contradiction check, the ADR corpus gradually *becomes* a de-facto specification coexisting with — and occasionally contradicting — the frozen Specification. Boundary Spec↔ADR dissolves.
3. **Authority fragments.** Several ADRs "re-define" the same term (e.g. descriptor, discovery) in slightly different ways; with no compliance gate, Accepted ADRs that contradict the freeze remain live. No reliable way to know which decision governs.
4. **Zones blur; records balloon.** Implementation Notes accumulates into large, partially-architectural documents; ADRs swell; reading any decision requires diffing several overlapping records.
5. **Trust in the corpus erodes.** As inconsistencies accumulate unnoticed, engineers and later architects lose confidence in "the ADRs" as a trustworthy record — the exact anti-outcome of an architecture-as-history record.

**Conclusion:** the failures escalate *with count* — a small-corpus problem becomes a documentation crisis at scale. The G1-003 findings, being structural, would not have been discovered by any single ADR review; they surface only as the corpus grows. (This is documentation-scope only; nothing here concerns implementation.)

---

## Audit 6 — Repair Scope

Without offering a *how*, identify the *minimum layer(s)* that must be touched to remove **all** root causes.

| Root Cause | Minimum layer that must change |
|---|---|
| **A** (template/stateless) | **ADR_TEMPLATE + ADR Process** — the template must represent relations (authority gate, corpus supersede, artifact linkage); the process must enforce corpus governance. Template alone is insufficient because corpus governance is a process concern. |
| **B** (freeze policy) | **Specification Freeze Document** — the freeze itself must be repositioned (what detail may legally live at the ADR layer, and the promotion path to canonical). This lives at the freeze layer, not the template. |

**Verdict — Minimal Repair Scope:** **more than one layer.** Removing all root causes requires at least:
- **ADR_TEMPLATE (ADR Framework)** *and*
- **ADR Process** *and*
- **Specification Freeze Document**

(REPOSITORY_CONVENTION may also need to recognize binding artifacts as dependency nodes — tied to Root Cause A / T3 — reinforcing that the scope spans more than one layer.)

> Per directive: we identify the scope minimum only. We do **not** select the repair method.

---

## Audit 7 — Architectural Severity

| Root Cause | Severity | Reason |
|---|---|---|
| **A** (template/stateless) | **Structural** | It is a defect in the *mechanism* of the decision framework (the template's structure), not in the text of the Constitution or Specification. It causes pervasive, systemic error in how decisions get recorded — worse than cosmetic, but not a Constitutional/Foundational text defect. |
| **B** (freeze policy) | **Foundational** | It touches the *frozen declaration that governs the entire Specification layer* (what may live where). As a policy that shapes the boundary between Spec and ADR, it underpins everything downstream — Foundational severity. Not Constitutional (it does not alter Mission/Constitution text). |

(Final verdict severity carries Root Cause A = Structural, Root Cause B = Foundational.)

---

## Output

1. **Causal Graph** — provided in Audit 1 (full leaf-level trace for T1, T2, T3). ✅
2. **Root Cause Tree** — 3 findings collapsed into 2 roots: **A** (template/stateless, governed-decision-layer missing) + **B** (freeze policy routes detail without a guardian). Single-root collapse noted but not forced. ✅
3. **Principle Mapping** — A violates Authority Chain, SSOT, Separation of Responsibility, One-Decision-One-ADR; B violates Canonical Promotion, Specification Freeze, SSOT (aggravated). No unmapped principle. ✅
4. **Layer Mapping** — A born in ADR Framework; B born in ADR Framework, triggered by Specification Freeze (cross-layer); partial Foundation component via T3 Citizen-taxonomy. ✅
5. **Historical Simulation** — 100-ADR outcome: consistency collapse, informal second Spec, authority fragmentation, record bloat, eroding trust; failures escalate with count. ✅
6. **Minimal Repair Scope** — more than one layer: ADR_TEMPLATE + ADR Process + Specification Freeze (and possibly REPOSITORY_CONVENTION). ✅
7. **Severity Assessment** — A = Structural; B = Foundational. ✅
8. **Final Root Cause Verdict** — see below. ✅
9. **STOP Condition** — see below. ✅

---

## Final Root Cause Verdict

**The three G1-003 findings are NOT three independent defects. They reduce to TWO root causes.**

| Finding | Reduces to |
|---|---|
| T1 · Authority Leakage | Root Cause A (no gate = relation to authority not represented) |
| T2 · Second Specification | Root Cause B (freeze routes detail) + Root Cause A (no corpus governance) |
| T3 · Dependency Graph | Root Cause A (binding artifacts not nodes) + partial Foundation (Citizen taxonomy) |

**Root Cause A (Structural):** the ADR layer is designed as *standalone, stateless documents* with no formal relation to authority, to a corpus, or to binding artifacts — i.e., it is **not a governed decision layer**.

**Root Cause B (Policy):** the **freeze** assigns design/format detail to the ADR layer, but neither the freeze nor the template establishes a guardian layer to keep that detail consistent — the upstream policy trigger that makes Root Cause A consequential.

**Interpretation for SAM:** a single conceptual shift — defining the ADR layer as a *governed decision layer* with explicit relations (to the frozen authority and to the corpus) and a defined promotion path — addresses both roots. Because the *trigger* lives in the freeze, and the *mechanism* lives in the template/process, **no change confined to the template alone is sufficient**.

---

## STOP Condition

**Aktif.**

| Criterion | Status |
|---|---|
| Root cause berada di Foundation? | **Parsial.** Root Cause A dan B lahir di ADR Framework; tetapi T3 memunculkan komponen taksonomi Citizen dari Philosophy/Foundation yang tidak ditegakkan di graph. Foundation tersentuh hanya parsial, bukan murni. |
| Specification Freeze ternyata tidak cukup? | **Ya.** Root Cause B adalah freeze yang melempar detail ke lapisan tanpa penjaga — freeze dalam bentuknya sekarang **tidak cukup** untuk mencegah korpus ADR jadi Specification kedua. |
| Lebih dari satu lapisan harus berubah sebelum ADR dapat dipakai? | **Ya.** Minimal Repair Scope = ADR_TEMPLATE + ADR Process + Specification Freeze (>satu lapisan). |

**Akibat STOP (per arahan):**
- **JANGAN mengusulkan solusi.**
- **JANGAN mengubah template.**
- Hanya laporkan hasil analisis (di atas).

---

## Final Statement

G1-004 melakukan analisis akar masalah over tiga temuan G1-003. Verdict: **tiga temuan itu bukan tiga cacat independen — mereka reduksi menjadi DUA akar masalah:**

1. **Akar A (struktural):** lapisan ADR dirancang sebagai kumpulan dokumen mandiri tanpa relasi formal ke otoritas, ke korpus, maupun ke artefak pengikat — ia **bukan lapisan keputusan yang diatur (governed decision layer)**.
2. **Akar B (kebijakan):** **freeze** menugaskan detail desain/format ke lapisan ADR tanpa sekaligus membentuk penjaga konsistensi — **pemicu hulu** yang membuat Akar A menjadi berdampak.

**Reduksi jujur:** 3 → **2** akar. Kemungkinan penggabungan ke 1 akar ("lapisan ADR tidak didefinisikan sebagai governed decision layer, padahal freeze menugaskannya menyimpan detail") **dicatat tetapi tidak dipaksakan**, sesuai arahan.

**Severity:** Akar A = **Structural**; Akar B = **Foundational**.

**Minimal Repair Scope:** **lebih dari satu lapisan** — ADR_TEMPLATE (ADR Framework) + ADR Process + Specification Freeze Document (dan kemungkinan REPOSITORY_CONVENTION untuk mengakui artefak pengikat sebagai node dependensi).

**Makna:** perbaikan yang hanya menyentuh template **tidak cukup**; karena pemicunya (Akar B) ada di freeze, perubahan harus menjangkau lapisan ADR + freeze secara bersama. Satu perubahan konseptual — *mendefinisikan lapisan ADR sebagai lapisan keputusan yang diatur* — dapat menyelesaikan A dan B sekaligus; tetapi karena itu menyentuh lebih dari satu lapisan, **STOP aktif dan kita tidak mengubah apa pun sekarang**.

TIDAK ada ADR ditulis. TIDAK ada solusi diusulkan. TIDAK ada template diubah. Hanya hasil analisis yang dilaporkan.
