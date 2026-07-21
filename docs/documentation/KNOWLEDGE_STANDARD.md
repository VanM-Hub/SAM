# Knowledge Standard



Version: 1.0



Status: Approved



Owner: SAM Framework



Category: Documentation Standard



Related Documents



Framework



\- docs/core/CONSTITUTION.md

\- docs/core/THINKING\_PROTOCOL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/MEMORY\_MODEL.md

\- docs/models/DECISION\_MODEL.md



Documentation



\- DOCUMENT\_STRUCTURE.md

\- WRITING\_GUIDELINES.md

\- CROSS\_REFERENCE\_RULES.md

\- DOCUMENT\_LIFECYCLE.md



Module Example



\- modules/openclaw/knowledge/README.md



---



# Purpose



This document defines the standard structure and metadata for every Knowledge document maintained within the SAM Framework.



Its objective is to ensure that knowledge is:



\- consistent,

\- searchable,

\- traceable,

\- reviewable,

\- trustworthy,

\- reusable.



Knowledge is treated as an operational asset rather than ordinary documentation.



---



# Philosophy



The SAM Framework distinguishes documentation from knowledge.



Documentation describes.



Knowledge explains.



Knowledge exists to preserve validated understanding that future contributors should not have to rediscover.



Every Knowledge document therefore represents a unit of organizational memory.



---



# Objectives



The Knowledge Standard has five objectives.



1\. Standardize metadata.



2\. Improve discoverability.



3\. Support evidence-based reasoning.



4\. Enable operational memory.



5\. Support future automation.



---



# Knowledge Unit



Every Knowledge document is considered a Knowledge Unit.



A Knowledge Unit consists of:



\- metadata,

\- content,

\- evidence,

\- relationships,

\- lifecycle.



Together these elements form a reusable unit of operational knowledge.



---



# Required Metadata



Every Knowledge document shall include the following metadata.



```yaml

Version: 1.0



Status: Draft



Knowledge Type:



Concept

Operational

Reference



Evidence Level:



Verified

Observed

Experimental



Confidence:



High

Medium

Low

```



Additional metadata may be introduced in future Framework versions without breaking compatibility.



---



# Knowledge Type



Knowledge Type identifies the role of the document.



Exactly one primary type shall be assigned.



---



## Concept



Defines stable concepts.



Examples



\- Workspace

\- Runtime

\- Provider

\- Model

\- Agent

\- Identity



Concept documents explain what something is.



They should remain relatively stable over time.



---



## Operational



Describes operational behavior.



Examples



\- Startup

\- Shutdown

\- Health Checks

\- Logs

\- Backup

\- Diagnostics



Operational knowledge evolves as operational experience grows.



---



## Reference



Describes factual reference information.



Examples



\- CLI

\- Configuration Files

\- Environment Variables

\- Permissions

\- Filesystem Layout



Reference documents prioritize accuracy and completeness.



---



# Evidence Level



Evidence Level describes how the knowledge was obtained.



---



## Verified



Confirmed through repeatable observation, testing, or authoritative sources.



Highest confidence.



Preferred for production decisions.



---



## Observed



Based on operational experience but not yet independently verified.



Useful but should be interpreted carefully.



---



## Experimental



Derived from investigation or limited testing.



Requires further validation.



Should not become operational policy until verified.



---



# Confidence



Confidence represents the current confidence of the Knowledge Unit.



High



Evidence is strong and consistent.



Medium



Evidence is generally reliable but may require additional validation.



Low



Evidence remains incomplete.



Low confidence documents should reference Research whenever possible.



---



# Relationship with Trust Model



Confidence is not a replacement for the Trust Model.



Instead:



Trust Model



↓



Evaluates Evidence



↓



Knowledge Standard



↓



Records Confidence



The Trust Model explains *how* evidence is evaluated.



The Knowledge Standard records the result.



---



# Relationship with Memory Model



The Memory Model defines how operational memory evolves.



Knowledge documents are persistent memory objects.



Operational learning should follow this lifecycle:



Observation



↓



Evidence



↓



Validation



↓



Knowledge



↓



Operational Use



↓



Review



↓



Improved Knowledge



Knowledge should accumulate over time rather than being repeatedly rediscovered.



---



# Required Cross References



Every Knowledge document shall reference at least one related document.



Relationships may include:



Framework references



Module references



Knowledge dependencies



Playbooks



Diagnostics



Architecture



Related research



Knowledge must never exist in isolation.



---



# Content Structure



Knowledge documents should generally follow this structure.



1\. Purpose



2\. Scope



3\. Definition



4\. Detailed Explanation



5\. Relationships



6\. Operational Considerations



7\. Future Evolution (if applicable)



8\. Summary



Minor variations are acceptable when appropriate.



---



# Naming Rules



Document names should:



\- use lowercase,

\- use hyphens,

\- describe one concept,

\- avoid abbreviations unless standardized.



Good



workspace.md



runtime.md



health-checks.md



Bad



misc.md



notes.md



stuff.md



---



# Evolution



Knowledge evolves through evidence.



Possible changes include:



\- clarification,

\- expansion,

\- correction,

\- deprecation,

\- replacement.



Knowledge should rarely be deleted.



Historical understanding is valuable.



---



# Review Requirements



Knowledge should be reviewed when:



new evidence appears,



operational behavior changes,



major software versions change,



an incident reveals incorrect assumptions,



an ADR changes architectural direction.



Review follows the Framework Review Process.



---



# Future Compatibility



Future versions of the Knowledge Standard may introduce metadata such as:



Author



Last Reviewed



Applies To



Tags



Related ADRs



Automation Status



These additions should remain backward compatible whenever possible.



---



# Example Metadata



Example 1



```yaml

Version: 1.0



Status: Draft



Knowledge Type: Concept



Evidence Level: Verified



Confidence: High

```



---



Example 2



```yaml

Version: 1.0



Status: Draft



Knowledge Type: Operational



Evidence Level: Observed



Confidence: Medium

```



---



Example 3



```yaml

Version: 1.0



Status: Draft



Knowledge Type: Reference



Evidence Level: Verified



Confidence: High

```



---



# Definition of Done



A Knowledge document complies with this standard when it:



✓ contains all required metadata,



✓ references related documents,



✓ clearly identifies its Knowledge Type,



✓ records evidence quality,



✓ records confidence,



✓ follows the Documentation Standards,



✓ is understandable without requiring author explanation.



---



# Summary



The Knowledge Standard establishes the rules by which knowledge is created, classified, evaluated, and maintained within the SAM Framework.



By treating every Knowledge document as a structured Knowledge Unit—with defined metadata, evidence quality, confidence, relationships, and lifecycle—the Framework transforms documentation into a durable Knowledge Operating System capable of supporting operational reasoning, continuous learning, and future automation.

