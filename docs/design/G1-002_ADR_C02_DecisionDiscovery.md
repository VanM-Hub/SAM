# G1-002 — ADR Candidate C-02 Decision Discovery

**Version:** 1.0
**Status:** Architectural Decision Discovery (Read-only analysis — no decision)
**Authority:** Derived from the Foundation; derives from the Canonical Architecture, the Specification Layer, Blueprint G0-001, and Analysis G1-001.
**Owner:** Project SAM
**Mode:** Read-only. Tests whether six "missing facts" (F1–F6) require new architectural decisions or are largely implied by existing documents.

**Depends On:**
- MISSION
- CONSTITUTION (esp. Art. III, IV, VII, IX)
- PHILOSOPHY
- GOVERNANCE
- GLOSSARY
- Canonical Architecture (SAM_ARCHITECTURE.md)
- ALL Specification Layer
- Blueprint G0-001
- Analysis G1-001

> This document **creates no ADR, selects no alternative, and proposes no solution**.
> It discovers the *decision structure* hidden inside C-02, tests quality of the architecture, and reports which facts are independent, which are implied, and which belong elsewhere.

---

## The Six Facts (from G1-001, Audit 6)

| # | Fact | Question |
|---|---|---|
| F1 | Exact vs. compatible match priority | When both an exact and a compatible candidate exist, which is preferred? |
| F2 | Deterministic tie-break basis | What ordering basis makes the mandated deterministic selection concrete? |
| F3 | Availability semantics | Is a compatible-but-not-exact version an acceptable resolution outcome? |
| F4 | Re-resolution trigger | When may a resolved binding be re-evaluated? |
| F5 | Context scope | May any input beyond the Capability Request inform resolution? |
| F6 | Observation point | At which point in the chain is the resolved Capability observed/bound? |

---

## Audit 1 — Decision Independence

For each fact: is it truly independent, or an automatic consequence of existing documents?

| Fact | Independent? | Assessment (evidence-based) |
|---|---|---|
| **F1** | **Yes — genuinely open** | Registry mandates resolving to "a version compatible with the request" and "non-deprecated preferred", but **does not state** exact-first vs. compatible-first when both exist. Not implied. Requires a decision. |
| **F2** | **Partially — reduced** | Determinism itself is **mandated** by Registry ("exactly one deterministically") and Article VII. What remains open is only the *ordering basis*. The natural basis (unique identifier + version) is **already defined** as inherent Capability properties (Capability Identity, Versioned). So F2's *substance* is largely implied; only its *affirmation* is a decision. |
| **F3** | **No — collapses into F1** | Registry defines failures for "no compatible version" (Version Mismatch) but is silent on whether a compatible-non-exact result is accepted. This is the *flip side* of F1: "accept compatible when exact absent" ↔ "availability". It is not a separate question; it is the same priority decision seen from availability. |
| **F4** | **Partially — largely implied** | Registry: Discovery is idempotent, has no side effects, deterministic "given the same registry content and the same request". This implies: re-resolution is always safe, and validity is governed by *content change*, not by a new configuration rule. The only residual is *how content change is observed* — a mechanism, not a new architectural decision. |
| **F5** | **No — strong textual consequence** | Registry defines Discovery input as the **Capability Request** (singular). Article VII names "implicit context" a **violation**. Philosophy: "Registry makes dependencies explicit… Everything becomes visible." Together these strongly imply resolution accepts only the Capability Request. F5 is more an *affirmation of Specification compliance* than a new decision. |
| **F6** | **Yes — but not purely C-02** | Registry defines Discovery output as **Capability Descriptor + Contract Reference** (binding happens before proceeding), which points to *front-loading*. But *where* the resolved Capability is observed (at Approval vs. Execution) is open and is coupled to Candidate ADRs C-01 (ordering) and C-08 (verification point). F6 is a real open point, but it does **not** belong solely to C-02. |

**Summary:** Of six facts, F1 is genuinely independent; F2 and F4 are largely implied (only mechanism/affirmation remains); F3 is not independent (collapses into F1); F5 is a textual consequence (Spec-compliance affirmation); F6 is genuinely open but belongs partly outside C-02.

---

## Audit 2 — Hidden Constraint Discovery

Constraints found in Foundation/Specification that may resolve one of the six facts (collected as evidence, not inference):

| # | Hidden Constraint | Source | Resolves |
|---|---|---|---|
| H-01 | "Registry is the authoritative source for discovery." | GOVERNANCE (Registry Governance) | Framework for F6 (Registry owns discovery/resolution; elsewhere in the chain is not Registry's role) |
| H-02 | "Determinism has higher priority than convenience." | CONSTITUTION Art. VII | F1/F3: availability may not override determinism |
| H-03 | "Same input, same contracts, same policies, same output." + "Hidden randomness… implicit context" = violations | CONSTITUTION Art. VII | F5: extra implicit context is a constitutional violation |
| H-04 | Discovery input = "a Capability Request (a reference to a requested Capability)". | REGISTRY (Discovery Protocol) | F5: singular defined input |
| H-05 | "Discovery SHALL be idempotent… SHALL NOT have side effects." + deterministic "given the same registry content and the same request". | REGISTRY (Discovery Protocol / Resolution Rules) | F4: re-resolution safe; validity tied to content change |
| H-06 | Output of Discovery = "Capability Descriptor + Contract Reference". | REGISTRY (Discovery Protocol) | F6: binding produces descriptor + contract up front → front-loaded |
| H-07 | Resolution failure when "no compatible version exists" → Version Mismatch. | REGISTRY (Failure Behaviour) | F1/F3: only the absence of *any* compatible version is a defined failure; presence of exact-vs-compatible choice is unaddressed |
| H-08 | "non-deprecated SHALL be preferred over deprecated"; "suspended or removed SHALL NOT be a candidate". | REGISTRY (Resolution Rules) | F2: two precedence axes already defined (deprecation, availability-of-object); only the residual ordering basis is open |
| H-09 | Capability is "uniquely identifiable" and "versioned". | CAPABILITY (Constitutional Principles + Identity) | F2: natural deterministic ordering keys already exist |
| H-10 | "Capabilities are discovered through Registry, never through implementation." | CAPABILITY (Discovery) | F5/F6: resolution is a Registry concern, not a Consumer/implementation concern |
| H-11 | "Citizens discover, never assume… A Citizen should never know another Citizen directly." | CONSTITUTION Art. IV | F5: resolution must not reintroduce direct/contextual knowledge of another Citizen |
| H-12 | "Citizens communicate through capabilities, never through implementation details." | CONSTITUTION Art. III | F5/F6: resolution operates on capabilities as the universal language |
| H-13 | Registry "does not decide whether an operation is approved" (boundary). | REGISTRY (Boundaries) | F6: Approval observes the resolved Capability, but resolution itself is Registry's — a separation already drawn |
| H-14 | "Resolution is the selection of a candidate from those that matched discovery." | REGISTRY (Resolution Rules) | F2/F6: selection happens after match, within Registry, before output |
| H-15 | Capability "backward compatible whenever practical", evolves via Patch→Minor→Major, "Breaking compatibility requires explicit architectural review". | CAPABILITY (Evolution/Principles) | F1/F3: version compatibility is designed to be honored (supports accepting a compatible version), but does not decide exact-vs-compatible priority |

---

## Audit 3 — Dependency Graph

```
F1 (exact vs compatible priority)
   └─(independent, relies on Registry silent point) — leaf

F3 (availability semantics)
   └─ depends on F1   (same decision, availability side)

F2 (deterministic tie-break basis)
   └─ depends on F1   (after priority is set, order the remaining candidates)
   └─ constrained by H-08, H-09 (axes + keys already exist)

F4 (re-resolution trigger)
   └─ depends on idempotency/content-determinism (H-05) — largely implied
   └─ depends on C-01 (ordering) and C-03 (content-change observation, mechanism)

F5 (context scope)
   └─(constitutional/textual consequence: H-03, H-04, H-11) — effectively resolved by documents

F6 (observation point)
   └─ depends on C-01 (ordering) and C-08 (verification point)
   └─ constrained by H-01, H-13, H-14 (Registry owns resolution; Approval/Execution observe)
```

**Reported dependencies:**
- F3 **depends on** F1 (same decision).
- F2 **depends on** F1 (ordering follows priority), and is further *constrained, not freed*, by existing axes (H-08/H-09).
- F4 **depends on** existing idempotency/content-determinism (implied) **and** on C-01/C-03 (outside C-02).
- F6 **depends on** C-01/C-08 (outside C-02).
- F5 has **no real dependency to resolve** — it is already answered by textual consequence.

---

## Audit 4 — Decision Collapse

Possible merges (reported, not merged):

| Candidate Collapse | Rationale | Strength |
|---|---|---|
| **F1 + F3 → one decision** | "Accept compatible when exact absent" and "prioritize exact vs compatible" are the **same priority decision seen from two angles** (choice vs. outcome availability). Registry's silence covers both. | **Strong** — likely one decision |
| **F2 → into F1-decision** | Once priority (F1/F3) is decided, the residual ordering basis is *affirmation* of using the inherent Capability identity+version keys (H-09). F2 does not need a separate decision; it is part of specifying the single deterministic selection rule. | Strong |
| **F4 + C-03** | Re-resolution mechanism (observing content change) is not an architectural decision; it is a mechanism (Candidate ADR C-03 of Blueprint) / Implementation concern. | Moderate — it *leaves* C-02 |
| **F5 → no collapse needed** | F5 is a Specification-compliance affirmation (H-03/H-04/H-11), not a separate decision to merge. It drops out of the decision set entirely. | Strong |
| **F6 + C-01/C-08** | Observation point in the chain is an ordering/verification concern belonging to C-01 and C-08, not C-02. | Strong — it *leaves* C-02 |

**Conclusion:** F1, F2, F3 are likely three faces of **one** resolution-selection decision. F4 migrates to mechanism (C-03/Implementation). F5 drops out (Spec affirmation). F6 migrates to C-01/C-08.

---

## Audit 5 — Decision Layer Classification

Where each decision *should* be born (no decision on content):

| Fact | Layer | Rationale |
|---|---|---|
| **F1** | **ADR** | Genuinely open; not implied by any frozen document. New architectural decision. |
| **F3** | **ADR** (same decision as F1) | Same layer as F1; part of the same ADR. |
| **F2** | **ADR** (affirmed within F1-ADR) | Mandate (determinism) is Specification; the residual *ordering basis affirmation* belongs to the same ADR, not a new layer. |
| **F4** | **Specification (implied) + Implementation (mechanism)** | The *rule* (idempotent, content-validity) is already Specification; the *observation mechanism* is Implementation / Candidate ADR C-03. Not a new Foundation/Spec change. |
| **F5** | **Specification / Foundation (already affirmed)** | The Constitution (Art. VII), Philosophy (explicitness), and Registry (input = request) already resolve it. No new decision — an affirmation of compliance. |
| **F6** | **ADR** (but C-01/C-08, not C-02) | Observation point is a real architectural decision, but its home is the ordering/verification ADR family, not C-02 alone. |

**Summary:** After classification, only **F1/F3/F2 (one selection-priority decision)** truly belongs to a C-02 ADR. F5 is already Specification-affirmed. F4 is Specification-implied + Implementation-mechanism. F6 belongs to C-01/C-08.

---

## Audit 6 — Minimal Decision Set

```
6 facts (F1..F6)
    │
    ├─ F5  → Specification affirmation (drops out; no ADR)
    ├─ F4  → Specification-implied rule + Implementation mechanism (drops to C-03/Impl)
    ├─ F6  → migrates to C-01/C-08 (not C-02)
    └─ F1 + F3 + F2 → collapse into ONE selection-priority decision (the true C-02)
```

**Result: the six facts reduce to a single architectural decision for C-02:**

> **How the Registry selects exactly one candidate when multiple valid (compatible, non-deprecated, available) candidates match a Capability Request — i.e., the priority order (exact vs. compatible) plus the deterministic ordering basis (affirming inherent identity+version keys).**

Not forced to a round number: the analysis yields **1 core ADR** (C-02, focused) after removing one affirmation (F5), one mechanism (F4), and one migrated concern (F6). F2 does not add a separate ADR; it is part of specifying that one selection rule.

---

## Audit 7 — ADR Boundary

Is C-02 one ADR or several mixed?

**Verdict: C-02, as scoped so far, is a mixture — not a single clean decision.**

Applying the principle *one architectural decision = one ADR*, C-02 currently holds:
1. **One core decision** that truly belongs: the selection-priority rule (F1/F3/F2) — a single architectural decision about how to choose among matching candidates.
2. **One affirmation, not a decision** (F5 — context input): already answered by Specification/Constitution; does not belong in an ADR as a new decision.
3. **One mechanism, not a decision** (F4 — re-resolution): Specification-implied rule + Implementation/C-03 mechanism.
4. **One migrated concern** (F6 — observation point): belongs to C-01/C-08 (ordering/verification), not C-02.

**Therefore:** the *intended* C-02 ADR should be scoped to the single core decision (#1). The other elements must be stripped (F5 — affirmed elsewhere), delegated (F4 — mechanism), or moved (F6 — C-01/C-08) so that C-02 satisfies *one architectural decision = one ADR*.

---

## Output Summary

1. **Independence Matrix** — F1 independent; F3 depends on F1; F2/reduced-implied; F4/largely implied; F5 textually resolved; F6 open-but-outside-C-02. ✅
2. **Hidden Constraint Register** — H-01…H-15 collected (GOVERNANCE, Constitution Art. III/IV/VII, Registry, Capability, Philosophy). ✅
3. **Dependency Graph** — F3→F1, F2→F1, F4→(impl + C-01/C-03), F6→(C-01/C-08), F5→(resolved). ✅
4. **Decision Collapse Analysis** — F1+F3+F2 → one decision; F4→mechanism; F5→dropped; F6→migrated. ✅
5. **Decision Layer Matrix** — F1/F3/F2 → ADR; F4 → Spec+Impl; F5 → Spec/Foundation affirmed; F6 → ADR (C-01/C-08). ✅
6. **Minimal Decision Set** — 6 facts → 1 core C-02 decision (+1 migrated, +1 mechanism, +1 affirmation). ✅
7. **ADR Boundary Verdict** — C-02 is currently a mixture; must be scoped to one core decision. ✅

---

## STOP Condition

**Aktiv — dalam mode pembersihan scope (bukan blokade total).**

| Criterion | Status |
|---|---|
| C-02 bukan satu keputusan | **Ya** — C-02 mengandung campuran: 1 keputusan inti + 1 afirmasi (F5) + 1 mekanisme (F4) + 1 concern pindah (F6). Boundary terlanggar. |
| Sebagian keputusan milik Foundation | **Ya (parsial)** — F5 sudah tersirat Constitution (Art. VII) + Philosophy + Registry (input=request). F2 mandatnya adalah Specification (determinism). |
| Sebagian keputusan milik Implementation | **Ya (parsial)** — F4 mekanisme observasi perubahan content (→ C-03/Implementation). |
| Specification ternyata belum cukup | **Tidak** — Specification cukup untuk mengimplikasikan F5 dan aturan F4; yang terbuka hanyalah keputusan seleksi inti (F1/F3/F2), yang memang spectrum ADR. |

**Akibat STOP:** Per arahan:
- **JANGAN membuat ADR.**
- **JANGAN memilih alternatif.**
- Hanya laporkan struktur keputusan yang ditemukan (di atas).

---

## Final Statement

G1-002 menemukan bahwa enam "fakta yang hilang" dari G1-001 **tidak seluruhnya merupakan keputusan arsitektur baru**:

- **Tiga di antaranya (F1, F3, F2) adalah satu keputusan** : aturan seleksi tunggal Registry untuk memilih satu kandidat dari banyak yang cocok — prioritas exact-vs-compatible plus base urutan deterministik yang mengafirmasi kunci identitas+versi yang sudah menjadi properti inherent Capability.
- **Satu (F5) sudah tersirat** oleh Constitution (Art. VII), Philosophy (explicitness), dan Registry (input = Capability Request) — menjadi afirmasi kepatuhan Specification, bukan keputusan baru.
- **Satu (F4) menyisakan mekanisme** (observasi perubahan konten) yang menjadi masalah Implementasi / Candidate ADR C-03, bukan keputusan arsitektur C-02.
- **Satu (F6) berpindah** ke keluarga ADR C-01/C-08 (ordering/verification point), bukan C-02.

**C-02 ternyata adalah campuran, bukan satu keputusan bersih.** Prinsip *one architectural decision = one ADR* (yang dijaga Project SAM) menuntut C-02 dipersempit menjadi **satu keputusan inti** sebelum ADR ditulis. Keputusan-keputusan lain harus dilepas (F5 — affirmation), didelegasikan (F4 — mechanism C-03), atau dipindah (F6 — C-01/C-08).

Hasil ini menunjukkan kualitas arsitektur yang sehat: dari enam titik yang tampak "kurang informasi", hanya **satu keputusan arsitektural sesungguhnya** yang perlu lahir sebagai ADR C-02. ADR itu nanti akan kecil, fokus, dan mudah dipelihara — persis sebagaimana prinsip yang dipegang Project SAM.

TIDAK ada ADR dibuat. TIDAK ada alternatif dipilih. Hanya struktur keputusan dilaporkan.
