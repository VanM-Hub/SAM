# Runtime Diagnostics



Version: 1.0



Status: Draft



Knowledge Type: Operational



Evidence Level: Observed



Confidence: Medium



Owner: OpenClaw Module



Related Documents



Knowledge



\- ../knowledge/runtime.md

\- ../knowledge/startup.md

\- ../knowledge/shutdown.md

\- ../knowledge/logs.md

\- ../knowledge/health-checks.md

\- ../knowledge/configuration.md

\- ../knowledge/workspace.md

\- ../knowledge/providers.md



Architecture



\- ../architecture/runtime-flow.md

\- ../architecture/components.md

\- ../architecture/data-flow.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/DECISION\_MODEL.md

\- docs/models/RISK\_MODEL.md



---



# Purpose



This document defines a structured methodology for investigating Runtime-related operational issues.



Its objective is to determine whether observed failures originate from the Runtime itself or from one of its operational dependencies.



This document intentionally excludes corrective actions.



---



# Scope



Runtime Diagnostics investigates:



\- Runtime initialization

\- execution lifecycle

\- worker coordination

\- component orchestration

\- startup sequence

\- shutdown sequence

\- execution state transitions



Implementation-specific debugging procedures are outside the scope of this document.



---



# Diagnostic Principles



The Runtime should be evaluated as the coordinator of execution rather than as the default source of failure.



Evidence should distinguish between:



\- Runtime failures

\- Startup failures

\- Shutdown failures

\- Configuration failures

\- Workspace failures

\- Provider failures

\- Filesystem failures



The location where a symptom appears is not necessarily the location where the failure originated.



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



The investigation follows the standard diagnostic methodology defined by the Core Framework.



---



# Step 1 — Observe Symptoms



Record Runtime behavior exactly as observed.



Examples include:



\- Runtime fails to start

\- unexpected termination

\- worker stops unexpectedly

\- execution hangs

\- incomplete execution

\- repeated initialization attempts

\- abnormal shutdown



Observation should remain descriptive.



Avoid assigning causes.



---



# Step 2 — Collect Evidence



Potential evidence includes:



\- Runtime logs

\- startup sequence

\- shutdown sequence

\- worker status

\- health checks

\- configuration resolution

\- Workspace observations

\- Provider state



Evidence should originate from multiple independent sources whenever practical.



---



# Step 3 — Evaluate Evidence



Evaluate evidence according to:



\- completeness

\- consistency

\- freshness

\- reliability

\- repeatability



Conflicting observations should remain documented.



---



# Step 4 — Generate Hypotheses



Possible hypotheses include:



\- Runtime initialization failure

\- dependency initialization failure

\- worker lifecycle failure

\- execution coordination failure

\- invalid Runtime state transition

\- unexpected component interaction



Hypotheses remain provisional until supported by evidence.



---



# Step 5 — Estimate Confidence



Confidence should consider:



\- evidence quality

\- evidence quantity

\- consistency

\- reproducibility

\- independent confirmation



Confidence should never exceed available evidence.



---



# Step 6 — Identify the Most Probable Cause



The investigation concludes by identifying the hypothesis best supported by available evidence.



Alternative explanations should remain documented when confidence is insufficient.



---



# Evidence Sources



Typical evidence sources include:



\- Runtime logs

\- startup events

\- shutdown events

\- worker lifecycle observations

\- health checks

\- configuration state

\- Workspace state

\- Provider status



No single evidence source should be considered authoritative.



---



# Common Symptom Categories



Typical Runtime symptoms include:



\- failed startup

\- unexpected shutdown

\- stalled execution

\- worker exhaustion

\- repeated restart cycles

\- execution timeout

\- incomplete task processing



Identical symptoms may originate from different architectural layers.



---



# Relationship with Runtime Flow



Runtime Flow defines the expected execution lifecycle.



Runtime Diagnostics compares observed execution against that expected lifecycle.



---



# Relationship with Startup



Startup represents the transition into operational readiness.



Failures during Startup should be distinguished from failures occurring during normal execution.



---



# Relationship with Shutdown



Shutdown represents the controlled termination of Runtime activity.



Unexpected termination should not automatically be classified as Shutdown failure.



---



# Relationship with Health Checks



Health Checks provide operational observations.



Runtime Diagnostics interprets those observations within a broader evidence-based investigation.



Health Checks alone do not establish causality.



---



# Relationship with Providers



Provider failures may appear as Runtime failures.



Diagnostics should determine whether Runtime coordination or Provider interaction better explains observed behavior.



---



# Relationship with Configuration



Configuration determines Runtime behavior.



Unexpected Runtime execution may result from valid Runtime logic operating on incorrect Effective Configuration.



---



# Diagnostic Boundaries



This document does not:



\- restart Runtime

\- terminate workers

\- modify configuration

\- change Provider selection

\- repair execution failures



Its sole responsibility is evidence-based investigation.



---



# Future Evolution



Future documentation may expand into:



diagnostics/runtime/



README.md



startup-diagnostics.md



worker-lifecycle.md



execution-state.md



runtime-coordination.md



shutdown-analysis.md



resource-management.md



---



# Summary



Runtime Diagnostics is an evidence-driven methodology for evaluating Runtime behavior.



By distinguishing Runtime coordination from dependency failures, OpenClaw improves diagnostic accuracy while avoiding incorrect attribution of operational problems.

