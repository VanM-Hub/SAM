\# SAM Citizen Specification



Version: 1.0

Status: Foundational

Authority: Derived from the Constitution

Depends On: CONSTITUTION, GOVERNANCE, GLOSSARY, SAM_ARCHITECTURE.md



\---



# Scope



Citizen is specified within this document as the constitutional participant of Project SAM.


The meanings of Mission, Constitution, Governance, the Canonical Architecture, and the Model Layer remain authoritative in their respective documents.


This document explains the Citizen domain and does not redefine those concepts.



\---



\# Purpose



This document defines the specification of the Citizen, derived from the Constitution.



Every architectural component participating in SAM governance SHALL

conform to this specification.



Citizen is the highest architectural abstraction in Project SAM.



Every Runtime is a Citizen.



Not every Citizen is a Runtime.



\---



\# Definition



A Citizen is an autonomous constitutional participant capable of

interacting with the SAM Governance System through standardized

contracts.



Citizens communicate through Capabilities.



Citizens never depend on implementation.



Citizens participate in governance.



\---



\# Constitutional Principles



Every Citizen SHALL:



\- possess an immutable identity

\- publish capabilities

\- expose contracts

\- participate in certification

\- expose health information

\- maintain lifecycle state

\- support governance

\- support auditing

\- support discovery

\- be replaceable



\---



\# Citizen Categories



The following are constitutional Citizens.



Runtime



Agent



Provider



Connector



Model



Skill



Tool



Mission



Workflow



Policy



Artifact



Audit



Desktop



Future architectural entities may become Citizens if they satisfy this specification.



\---



\# Mandatory Properties



Every Citizen SHALL expose:



Citizen ID



Citizen Type



Version



Descriptor



Metadata



Capability List



Contract List



Certification Status



Lifecycle State



Health Status



Compatibility Information



Governance Metadata



Audit Identity



\---



\# Citizen Identity



Every Citizen possesses a globally unique identity.



Identity never changes during its lifetime.



Identity should remain independent from implementation.



Example



sam.runtime.memory



sam.provider.openai



sam.agent.openclaw



sam.workflow.analysis



\---



\# Descriptor



Every Citizen SHALL publish an immutable Descriptor.



Descriptor represents the Citizen.



Descriptor never performs work.



Descriptor contains:



Identity



Version



Owner



Metadata



Capabilities



Compatibility



Dependencies



Certification



Lifecycle



\---



\# Capability Publication



Every Citizen SHALL explicitly publish every capability.



Capabilities SHALL NOT be implicit.



Capabilities SHALL be discoverable.



Capabilities SHALL be immutable.



\---



\# Contracts



Every interaction occurs through immutable Contracts, as established by the Constitution and the Glossary.


Citizens SHALL NOT communicate through implementation details.


This specification does not redefine the Contract; it only states how a Citizen relates to Contracts.



expected behavior



Contracts never define implementation.



\---



\# Lifecycle



Every Citizen SHALL expose lifecycle information.



Recommended lifecycle:



Declared



Registered



Certified



Available



Active



Suspended



Deprecated



Retired



Different Citizens may extend lifecycle states.



They may not remove constitutional states.



\---



\# Health



Every Citizen SHALL expose operational health.



Health SHALL NOT include business meaning.



Typical values:



Healthy



Warning



Unavailable



Degraded



Unknown



\---



\# Certification



Every Citizen SHALL be certifiable.



Certification proves constitutional compliance.



Certification SHALL verify at least:



Identity



Contract Integrity



Capability Publication



Determinism



Immutability



Governance Compliance



Audit Compliance



Certification SHALL NOT evaluate business usefulness.



\---



\# Approval



Citizens SHALL declare whether operations require approval.



Citizens SHALL NOT bypass Approval Policy.



Approval requirements belong to governance.



Not implementation.



\---



\# Audit Identity



Every Citizen SHALL expose immutable audit identity.



Audit Identity enables complete traceability.



Audit Identity SHALL include:



Citizen ID



Version



Execution Context



Mission Context



Workflow Context



Approval Context



Policy Context



Timestamp Metadata



\---



\# Discovery



Citizens SHALL NOT discover each other directly.



Citizens SHALL publish themselves to Registry.



Discovery SHALL occur through Registry.



\---



\# Dependencies



Citizens depend on:



Capabilities



Contracts



Registry



Never implementation.



\---



\# Communication



Citizen A



↓



Capability Request



↓



Registry



↓



Discovery



↓



Capability Match



↓



Contract



↓



Citizen B



Citizens never communicate through direct implementation knowledge.



\---



\# Replacement



Any Citizen may be replaced if:



Capabilities remain compatible.



Contracts remain compatible.



Certification succeeds.



Audit identity remains valid.



No other architectural change should be required.



\---



\# Distribution



Citizens SHALL be deployable independently in future architectures.



Current deployment topology does not affect constitutional requirements.



\---



\# Evolution



New Citizen types may be introduced.



They SHALL obey:



Identity



Descriptor



Capability



Contract



Lifecycle



Certification



Audit



Health



Governance



The Constitution evolves by extension.



Not by replacement.



\---



\# Constitutional Equality



No Citizen possesses constitutional privilege.



Runtime is not superior to Provider.



Provider is not superior to Agent.



Agent is not superior to Workflow.



All Citizens obey identical constitutional rules.



Responsibilities differ.



Rights do not.



\---



\# Constitutional Test



A new architectural concept becomes a Citizen only if it answers YES to every question:



Does it possess an identity?



Does it publish capabilities?



Does it expose immutable contracts?



Can it be certified?



Can it be audited?



Can it expose health?



Can it participate in governance?



Can it evolve independently?



If any answer is NO,



it should probably remain a Service rather than becoming a Citizen.



\---



\# Citizen Hierarchy



Citizen



├── Runtime

├── Agent

├── Provider

├── Connector

├── Model

├── Skill

├── Tool

├── Workflow

├── Mission

├── Policy

├── Desktop

└── Future Citizens



Citizen is the highest architectural abstraction within SAM.



\---



\# Final Statement



Citizens are not defined by implementation.



Citizens are defined by constitutional responsibility.



Implementations may change.



Citizens remain.



This guarantees that SAM can evolve without losing its identity.

