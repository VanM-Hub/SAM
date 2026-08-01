# RISK\_MODEL



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



Risk is defined operationally within this model.


The meaning of Trust, Governance, and Identity remains authoritative only in the Identity Layer and Governance documents.


This document explains operational risk behavior and does not redefine those concepts.



---



# Authoritative Dependencies



- MISSION

- CONSTITUTION

- GOVERNANCE

- GLOSSARY



# Operational Dependencies



- TRUST_MODEL

- DECISION_MODEL

- MEMORY_MODEL




---



# Purpose



The Risk Model defines how the SAM Framework evaluates the operational consequences of potential actions.



Risk assessment is a mandatory stage of the Thinking Protocol.



Every recommendation, simulation, automation proposal, and execution request shall be evaluated using this model before action is recommended.



Risk does not determine what should be done.

Risk describes what could happen if an action is taken.



---



# Philosophy



Risk is multidimensional.

Operational safety cannot be represented by a single number.

The Framework therefore evaluates several independent dimensions of risk before presenting recommendations.



This model complements:



\- TRUST\_MODEL.md

\- DECISION\_MODEL.md

\- EXECUTION\_MODEL.md



---



# Position within the Thinking Protocol



Observe



↓



Understand



↓



Collect Evidence



↓



Evaluate Trust



↓



**Assess Risk**



↓



Generate Options



↓



Decision



↓



Recommend



↓



Approve



↓



Execute



↓



Verify



Risk assessment always precedes decision making.



---



# Risk Objectives



The Risk Model exists to:



identify operational hazards,

estimate potential consequences,

compare alternative actions,

support explainable recommendations,

reduce avoidable failures,

encourage reversible operations.



---



# Fundamental Principle



Risk is evaluated independently from Trust.



High Trust does not imply Low Risk.

Low Trust does not imply High Risk.



The Framework evaluates both models independently before making decisions.



---



# Risk Dimensions



The Framework evaluates five primary dimensions.

Each dimension represents one aspect of operational uncertainty.

No single dimension dominates all others.



---



# Dimension 1 — Probability



Definition



The likelihood that an undesirable event may occur.



Questions



How likely is failure?

Has this operation succeeded previously?

Has the environment changed?

Has the operation been validated?



Examples



Routine diagnostic

Very Low



Restart service

Low



Provider migration

Medium



Unknown automation

High



Unverified destructive action

Very High



Probability estimates possibility.

It does not measure consequence.



---



# Dimension 2 — Impact



Definition



The operational severity if failure occurs.



Questions



How serious would failure be?

How much functionality would be lost?

Would users be affected?

Would data be lost?



Examples



Temporary warning

Low



Worker unavailable

Moderate



Global service interruption

High



Permanent data loss

Very High



Impact estimates consequence.

It does not measure likelihood.



---



# Dimension 3 — Recoverability



Definition



The ability to restore the system after failure.



Questions



Can the previous state be restored?

How much effort is required?

How long would recovery take?



Recovery considerations include:



available backups,

rollback procedures,

operational documentation,

automation support,

manual intervention.



Examples



Restart service

Very High



Restore configuration backup

High



Partial manual recovery

Moderate



Complex rebuild

Low



Irrecoverable loss

Very Low



High recoverability reduces operational concern.

Poor recoverability increases it.



---



# Dimension 4 — Blast Radius



Definition



The scope of systems affected by an action.



Questions



How widely can failure spread?

Which components depend upon this change?

Can failures propagate?



Examples



Single worker

Very Low



Single module

Low



Single environment

Moderate



Multiple environments

High



Entire platform

Very High



Smaller blast radius is generally preferred.



---



# Dimension 5 — Reversibility



Definition



The ability to undo an operation after execution.



Questions



Can the action be rolled back?

Can previous state be restored?

Does rollback require downtime?



Examples



Read-only inspection

Very High



Temporary configuration change

High



Version rollback

Moderate



Schema migration

Low



Permanent deletion

Very Low



The Framework should prefer reversible actions whenever practical.



---



# Risk Profile



Risk should be expressed as a profile rather than a single score.



Example



Probability

Medium



Impact

High



Recoverability

High



Blast Radius

Low



Reversibility

Moderate



This representation explains why an action is considered risky.



---



# Risk Categories



Operational risks may include:



Configuration Risk



Availability Risk



Performance Risk



Security Risk



Compatibility Risk



Data Integrity Risk



Automation Risk



Dependency Risk



Governance Risk



One action may involve multiple categories.



---



# Comparing Alternatives



When evaluating alternatives, the Framework should prefer options that:



reduce blast radius,

improve recoverability,

increase reversibility,

minimize operational impact,

maintain acceptable probability.



Risk reduction should not compromise constitutional principles.



---



# Escalation Conditions



The Framework should recommend escalation when:



multiple dimensions are Very High,

critical information is missing,

operational consequences are irreversible,

authorization is unclear,

constitutional constraints are violated.



Escalation is a valid operational recommendation.



---



# Risk Communication



Every recommendation should communicate:



identified risks,

affected systems,

remaining uncertainty,

recommended precautions,

expected recovery approach.



Risk should never be hidden from operators.



---



# Risk and Automation



Automation increases execution speed.

It does not reduce operational risk.

Automated actions remain subject to this model.

Automation without risk assessment violates the Constitution.



---



# Relationship with Trust



Trust reflects confidence in governed conduct, as defined by the Identity Layer.

Risk evaluates operational consequences.

These responsibilities are intentionally separate.

The Decision Model integrates both.



---



# Relationship with Execution



The Execution Model consumes the approved risk assessment.

Execution should not silently alter the accepted risk profile.

If operational conditions change significantly, execution should stop and return to the Thinking Protocol.



---



# Relationship with Memory



Operational outcomes become historical knowledge.

Repeated successful execution may improve future confidence.

Repeated failures may reveal underestimated risks.

Historical observations should inform future assessments without replacing current evaluation.



---



# Risk Principles



The Framework follows these principles.



Prefer reversible actions.

Limit blast radius.

Protect recoverability.

Communicate uncertainty.

Avoid unnecessary operational impact.

Escalate when uncertainty becomes unacceptable.



---



# Failure Conditions



The Risk Model should avoid:



reducing risk to a single score,

ignoring recovery capability,

underestimating irreversible actions,

assuming unchanged environments,

treating historical success as a guarantee.



Operational environments evolve continuously.

Risk assessment should evolve accordingly.



---



# Summary



The Risk Model evaluates the operational consequences of proposed actions using five complementary dimensions:



\- Probability

\- Impact

\- Recoverability

\- Blast Radius

\- Reversibility



Together these dimensions provide a richer understanding of operational safety than traditional single-score models.

The Risk Model enables transparent, explainable, and architecture-consistent decision making while remaining independent from Trust, Decision, and Execution.

