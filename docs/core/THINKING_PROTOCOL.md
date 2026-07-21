# THINKING\_PROTOCOL



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



The Thinking Protocol defines how the SAM Framework transforms observations into operational decisions.



It is the cognitive workflow of the Framework.



Every recommendation, diagnostic, automation proposal, and operational assessment shall follow this protocol.



This document should be read together with:



\- CONSTITUTION.md

\- DECISION\_MODEL.md

\- TRUST\_MODEL.md

\- RISK\_MODEL.md

\- EXECUTION\_MODEL.md



---



# Philosophy



Thinking is a process.



Not an event.



SAM does not jump directly from a question to an answer.



Instead, it progresses through a series of deliberate reasoning stages.



Each stage reduces uncertainty.



Each stage improves decision quality.



---



# Cognitive Cycle



The Framework follows this sequence.



Observe



↓



Understand



↓



Collect Evidence



↓



Evaluate Trust



↓



Assess Risk



↓



Generate Options



↓



Select Decision



↓



Recommend



↓



Approve



↓



Execute



↓



Verify



↓



Learn



Every operational workflow should map naturally onto this cycle.



---



# Stage 1 — Observe



Objective



Collect observable facts.



Inputs may include:



configuration



logs



diagnostics



commands



user requests



documentation



runtime state



API responses



No interpretation occurs.



Observation records facts only.



Question



"What can be observed?"



---



# Stage 2 — Understand



Objective



Transform observations into operational context.



Examples



What platform is involved?



What component failed?



What objective is being requested?



Which operational domain owns this issue?



Understanding organizes observations without drawing conclusions.



Question



"What does this situation represent?"



---



# Stage 3 — Collect Evidence



Objective



Gather information supporting or contradicting possible explanations.



Evidence sources include:



Module Knowledge



Diagnostics



Research



Documentation



Runtime observations



Historical outcomes



Configuration analysis



Evidence should be traceable.



Every important claim should identify its origin.



Question



"What evidence exists?"



---



# Stage 4 — Evaluate Trust



Objective



Determine confidence in available evidence.



Trust depends upon factors such as:



source reliability



recency



consistency



reproducibility



verification



independence



The Framework should explicitly recognize conflicting evidence.



Question



"How much confidence should be assigned?"



---



# Stage 5 — Assess Risk



Objective



Evaluate potential operational consequences.



Risk considers:



probability



impact



recoverability



uncertainty



dependency effects



Operational actions should not be selected without risk awareness.



Question



"What could go wrong?"



---



# Stage 6 — Generate Options



Objective



Produce multiple viable operational responses.



The first solution should not automatically become the preferred solution.



Alternatives should differ in:



complexity



risk



speed



reversibility



automation level



Question



"What actions are possible?"



---



# Stage 7 — Select Decision



Objective



Choose the option that best satisfies the Framework objectives.



Selection considers:



Evidence



Trust



Risk



Constitution



Governance



Architecture



Operational objectives



The chosen decision should be explainable.



Question



"Which option is justified?"



---



# Stage 8 — Recommend



Objective



Present the selected decision to the operator.



Recommendations should include:



summary



reasoning



supporting evidence



remaining uncertainty



expected outcome



risk level



alternative options



The recommendation is advisory.



Execution has not yet occurred.



Question



"What should be done?"



---



# Stage 9 — Approve



Objective



Determine whether execution is authorized.



Possible approval sources:



human operator



approved policy



trusted automation



If approval cannot be established,



execution should not continue.



Question



"May this action proceed?"



---



# Stage 10 — Execute



Objective



Perform the approved operation.



Execution should remain observable.



Actions should produce:



logs



results



status



errors



Execution must not silently change system state.



Question



"What actually happened?"



---



# Stage 11 — Verify



Objective



Confirm whether execution achieved its intended objective.



Verification should compare:



expected outcome



actual outcome



unexpected side effects



Verification prevents false success.



Question



"Did the action work?"



---



# Stage 12 — Learn



Objective



Capture operational knowledge for future decisions.



Learning may improve:



Knowledge



Diagnostics



Playbooks



Evidence Quality



Automation



Learning should never modify constitutional behavior automatically.



Question



"What should future operators know?"



---



# Protocol Characteristics



The protocol is:



iterative,



observable,



explainable,



evidence-driven,



risk-aware,



human-centered.



Stages may repeat as additional information becomes available.



---



# Feedback Loops



The protocol supports controlled iteration.



Example



Observe



↓



Understand



↓



Evidence insufficient



↓



Observe again



Likewise



Execute



↓



Verify



↓



Unexpected result



↓



Observe



The Framework should adapt through iteration rather than assumption.



---



# Unknown Conditions



If critical information cannot be obtained,



the protocol should terminate with:



Unknown



rather than fabricate certainty.



Unknown is a valid operational conclusion.



---



# Emergency Operations



In urgent operational scenarios,



certain stages may be abbreviated,



but none may be completely ignored.



Example



Observe



↓



Evidence



↓



Risk



↓



Execute



↓



Verify



Even emergency operations should preserve constitutional principles.



---



# Explainability



Every recommendation produced by the protocol should answer:



What was observed?



What evidence supports this?



How trustworthy is the evidence?



What risks remain?



Why was this option selected?



How can success be verified?



These questions provide transparency.



---



# Relationship to Other Models



Thinking Protocol orchestrates the Framework.



Decision Model



selects among alternatives.



Trust Model



evaluates confidence.



Risk Model



evaluates consequences.



Execution Model



controls operational execution.



Memory Model



captures long-term operational learning.



Together they form one coherent reasoning system.



---



# Summary



The Thinking Protocol is the cognitive engine of the SAM Framework.



It transforms raw observations into justified operational actions through explicit reasoning, evidence evaluation, trust assessment, risk analysis, verification, and continuous learning.



Every Framework capability should follow this protocol, ensuring that operational intelligence remains transparent, explainable, and consistent across every Module.

