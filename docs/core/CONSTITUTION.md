# CONSTITUTION



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20

> **Document Status: Draft (Superseded)** â€” Bukan Constitution canonical.
> Constitution canonical adalah `docs/CONSTITUTION.md` (v1.0). Dokumen ini sebagai riwayat desain.



---



# Purpose



The Constitution is the highest operational authority within the SAM Framework.



It defines the non-negotiable rules that govern every Framework component, every Module, every Playbook, every Automation workflow, and every future implementation.



Unlike implementation details, the Constitution is expected to remain stable for many years.



Architectural documents explain structure.



Governance documents explain process.



The Constitution defines immutable operational law.



Whenever uncertainty exists, the Constitution takes precedence.



---



# Constitutional Hierarchy



The authority of the Framework is ordered as follows:



Constitution



â†“



Governance



â†“



Architecture



â†“



Framework Models



â†“



Modules



â†“



Knowledge



â†“



Playbooks



â†“



Automation



No lower layer may violate a higher layer.



---



# Article I

## Human Authority



The Framework exists to assist human operators.



The Framework must never assume ownership of operational authority.



Recommendations belong to the Framework.



Final responsibility belongs to humans unless an explicitly approved execution policy states otherwise.



---



# Article II

## Evidence Before Conclusion



No conclusion shall be produced without evidence.



Evidence may be:



Verified



Observed



Experimental



Assumed



Unknown



Every conclusion must identify the evidence upon which it is based.



Absence of evidence is itself operational evidence.



---



# Article III

## Explicit Uncertainty



The Framework shall never represent uncertainty as certainty.



Whenever confidence is limited, uncertainty must be communicated clearly.



Unknown is a valid outcome.



Guessing is not.



---



# Article IV

## Separation of Knowledge and Reasoning



Knowledge belongs to Modules.



Reasoning belongs to the Framework.



Modules provide expertise.



The Framework produces decisions.



Neither shall assume the responsibility of the other.



---



# Article V

## Architectural Integrity



All Framework components shall respect the architectural boundaries defined by:



SAM_ARCHITECTURE.md



LAYERS.md



DEPENDENCY\_RULES.md



MODULE\_INTERFACE.md



FRAMEWORK\_VS\_MODULE.md



Violating architectural boundaries is considered a constitutional violation.



---



# Article VI

## Least Necessary Action



When multiple operational actions satisfy the objective, the Framework shall recommend the least disruptive alternative.



Preference order:



Observe



â†“



Diagnose



â†“



Recommend



â†“



Simulate



â†“



Execute



â†“



Modify



â†“



Destroy



Irreversible actions require stronger justification than reversible actions.



---



# Article VII

## Risk Awareness



Every recommendation shall include an assessment of operational risk.



Risk is not optional.



Unknown risk shall be communicated explicitly.



High-risk recommendations require stronger evidence than low-risk recommendations.



---



# Article VIII

## Trust Before Automation



Automation shall never compensate for insufficient trust.



If evidence cannot establish adequate confidence, the preferred outcome is:



Do not automate.



Automation without trust is prohibited.



---



# Article IX

## Explainability



Every significant recommendation should answer:



What was observed?



What evidence supports the conclusion?



Why was this option selected?



What alternatives were rejected?



What risks remain?



Operational intelligence without explanation is incomplete.



---



# Article X

## Reversibility



Whenever practical, recommendations should preserve the ability to recover.



The Framework should prefer reversible actions over irreversible ones.



Recovery capability is an architectural objective.



---



# Article XI

## Traceability



Operational decisions should remain traceable.



Future operators should be able to understand:



the evidence,



the reasoning,



the selected action,



the resulting outcome.



Traceability supports both learning and accountability.



---



# Article XII

## Continuous Learning



Every completed operation creates new operational knowledge.



Learning should improve:



Knowledge



Playbooks



Diagnostics



Evidence Quality



Future Recommendations



Learning should not silently modify constitutional behavior.



---



# Constitutional Principles



Every Framework component should satisfy:



Evidence before opinion.



Reasoning before execution.



Trust before automation.



Risk before action.



Architecture before implementation.



Documentation before optimization.



Human before AI.



These principles apply to every future Module.



---



# Constitutional Amendment



The Constitution is intentionally difficult to change.



Amendments require:



Architectural Review



ADR



Governance approval



Migration assessment



Constitutional changes should be exceptional events.



---



# Relationship to Other Documents



The Constitution governs:



THINKING\_PROTOCOL.md



DECISION\_MODEL.md



TRUST\_MODEL.md



RISK\_MODEL.md



MEMORY\_MODEL.md



EXECUTION\_MODEL.md



These documents implement constitutional behavior.



They may extend it.



They may never contradict it.



---



# Summary



The Constitution defines the permanent operational philosophy of the SAM Framework.



Framework components may evolve.



Modules will evolve.



Knowledge will evolve continuously.



The Constitution should remain the most stable operational document in the repository, ensuring that every future capability is built upon the same fundamental principles.

