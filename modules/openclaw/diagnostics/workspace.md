# Workspace Diagnostics



Version: 1.0



Status: Draft



Knowledge Type: Operational



Evidence Level: Observed



Confidence: Medium



Owner: OpenClaw Module



Related Documents



Knowledge



\- ../knowledge/workspace.md

\- ../knowledge/filesystem.md

\- ../knowledge/configuration.md

\- ../knowledge/runtime.md

\- ../knowledge/permissions.md

\- ../knowledge/logs.md

\- ../knowledge/health-checks.md



Architecture



\- ../architecture/workspace-model.md

\- ../architecture/components.md

\- ../architecture/data-flow.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/DECISION\_MODEL.md

\- docs/models/RISK\_MODEL.md



---



# Purpose



This document defines a structured methodology for investigating Workspace-related operational issues.



Its objective is to determine whether the Workspace provides a valid operational context for the Runtime.



This document intentionally excludes corrective procedures.



---



# Scope



Workspace Diagnostics investigates:



\- Workspace existence

\- Workspace structure

\- Workspace accessibility

\- Workspace integrity

\- Workspace selection

\- Workspace consistency

\- Workspace readiness



Repair activities are outside the scope of this document.



---



# Diagnostic Principles



Workspace should be evaluated as an operational context rather than merely as a directory.



Evidence should distinguish between:



\- missing Workspace

\- inaccessible Workspace

\- corrupted Workspace

\- invalid Workspace selection

\- inconsistent Workspace

\- Runtime issues unrelated to the Workspace



---



# Diagnostic Workflow



```

Observe



↓



Collect Evidence



↓



Evaluate Evidence



↓



Generate Hypotheses



↓



Estimate Confidence



↓



Identify Most Probable Cause

```



The workflow follows the standard diagnostic methodology defined by the Core Framework.



---



# Step 1 — Observe Symptoms



Record observable Workspace behavior.



Examples include:



\- Workspace cannot be opened

\- Workspace unexpectedly changes

\- missing operational files

\- invalid directory structure

\- inconsistent metadata

\- startup fails during Workspace resolution



Avoid interpreting the cause during this stage.



---



# Step 2 — Collect Evidence



Evidence may include:



\- directory structure

\- Workspace metadata

\- Runtime logs

\- configuration sources

\- filesystem observations

\- health check results



Evidence should originate from multiple independent sources whenever practical.



---



# Step 3 — Evaluate Evidence



Evaluate evidence according to:



\- completeness

\- consistency

\- freshness

\- reliability

\- relevance



Conflicting evidence should remain documented rather than discarded.



---



# Step 4 — Generate Hypotheses



Possible hypotheses include:



\- incorrect Workspace selected

\- damaged Workspace structure

\- missing operational files

\- insufficient permissions

\- configuration inconsistency

\- Runtime failure during Workspace initialization



Hypotheses remain provisional until supported by evidence.



---



# Step 5 — Estimate Confidence



Confidence should consider:



\- quantity of evidence

\- quality of evidence

\- consistency across observations

\- repeatability



Confidence should never exceed available evidence.



---



# Step 6 — Identify the Most Probable Cause



The investigation concludes by identifying the hypothesis best supported by available evidence.



Alternative hypotheses should remain documented when appropriate.



---



# Evidence Sources



Typical evidence sources include:



\- Workspace directory

\- Workspace metadata

\- Runtime logs

\- Configuration Resolution

\- Filesystem observations

\- Health Check reports



---



# Common Symptom Categories



Typical Workspace-related symptoms include:



\- Workspace not found

\- invalid Workspace structure

\- inaccessible Workspace

\- missing operational artifacts

\- inconsistent metadata

\- unexpected Workspace selection



Similar symptoms may originate from other components.



---



# Relationship with Workspace Model



Workspace Model defines the expected architecture.



Workspace Diagnostics compares observed Workspace behavior against that expected model.



---



# Relationship with Filesystem



Filesystem provides storage.



Workspace provides operational meaning.



Filesystem issues may affect Workspace integrity but should remain diagnostically distinguishable.



---



# Relationship with Runtime



Runtime consumes the Workspace.



Workspace Diagnostics should determine whether observed failures originate from Workspace state or Runtime behavior.



---



# Relationship with Configuration



Configuration determines Workspace selection.



Incorrect Configuration may appear to be a Workspace problem.



Both should be evaluated independently.



---



# Relationship with Health Checks



Health Checks provide operational observations.



Workspace Diagnostics evaluates those observations within a broader investigative process.



Health Checks alone do not establish causality.



---



# Diagnostic Boundaries



This document does not:



\- repair Workspace structure

\- recreate missing files

\- modify configuration

\- change permissions

\- migrate Workspace



Its responsibility is evidence-based investigation only.



---



# Future Evolution



Future documentation may expand into:



diagnostics/workspace/



README.md



integrity.md



structure.md



selection.md



metadata.md



consistency.md



workspace-readiness.md



---



# Summary



Workspace Diagnostics is an evidence-driven methodology for determining whether a Workspace provides a valid operational context.



By separating Workspace observations from assumptions and evaluating multiple evidence sources, OpenClaw improves diagnostic accuracy while preserving operational safety.

