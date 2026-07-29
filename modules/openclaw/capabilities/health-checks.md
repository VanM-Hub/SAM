# Health Checks



Version: 1.0



Status: Draft



Capability Type: Read-Only Automation



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Automatically assess the operational health of an OpenClaw installation without modifying system state.



This capability collects evidence from multiple architectural layers, evaluates health indicators, and produces a structured health report.



---



# Related Documents



Knowledge



\- ../knowledge/runtime.md

\- ../knowledge/workspace.md

\- ../knowledge/providers.md

\- ../knowledge/configuration.md

\- ../knowledge/health-checks.md

\- ../knowledge/logs.md



Architecture



\- ../architecture/components.md

\- ../architecture/runtime-flow.md

\- ../architecture/data-flow.md



Diagnostics



\- ../diagnostics/runtime.md

\- ../diagnostics/workspace.md

\- ../diagnostics/provider.md

\- ../diagnostics/configuration.md



Playbooks



\- ../playbooks/verify-installation.md

\- ../playbooks/verify-provider.md

\- ../playbooks/verify-workspace.md

\- ../playbooks/collect-diagnostics.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/core/EXECUTION\_MODEL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/RISK\_MODEL.md



---



# Purpose of Health Checks



Health Checks automate routine operational verification by combining multiple observations into a single evidence-based assessment.



The objective is early detection of operational anomalies.



No corrective actions are performed.



---



# Scope



This capability evaluates:



\- Runtime health

\- Workspace availability

\- Provider connectivity

\- Configuration validity

\- Filesystem accessibility



Business logic is outside scope.



---



# Inputs



Typical inputs include:



\- Runtime status

\- Effective Configuration

\- Workspace metadata

\- Provider observations

\- Filesystem observations

\- Health indicators

\- Log summaries



All inputs are read-only.



---



# Outputs



The capability produces a structured report containing:



\- observations

\- findings

\- warnings

\- evidence references

\- confidence estimate

\- overall health assessment



Outputs should distinguish facts from interpretation.



---



# Health Dimensions



Health assessment considers five operational dimensions.



## Runtime



Examples:



\- Runtime initialized

\- worker availability

\- execution readiness



---



## Workspace



Examples:



\- Workspace exists

\- Workspace accessible

\- expected structure detected



---



## Provider



Examples:



\- Provider reachable

\- authentication successful

\- configured model observable



---



## Configuration



Examples:



\- configuration resolved

\- required fields present

\- references valid



---



## Filesystem



Examples:



\- required files accessible

\- permissions adequate

\- storage available



---



# Execution Workflow



The capability follows the standard automation lifecycle.



```

Collect Evidence



↓



Validate Inputs



↓



Evaluate Health Indicators



↓



Estimate Confidence



↓



Generate Findings



↓



Produce Report

```



No execution step modifies the target system.



---



# Evidence Collection



Evidence may include:



\- Runtime status

\- CLI observations

\- configuration metadata

\- Workspace metadata

\- filesystem metadata

\- Provider status

\- health indicators



Evidence should be timestamped whenever possible.



---



# Health Assessment



Each operational dimension should be evaluated independently.



Possible assessments include:



\- Healthy

\- Warning

\- Degraded

\- Unknown



The capability should avoid binary healthy/unhealthy conclusions when evidence is incomplete.



---



# Confidence Assessment



Confidence should consider:



\- evidence completeness

\- evidence consistency

\- source reliability

\- observation freshness

\- repeatability



Confidence should never exceed available evidence.



---



# Report Structure



A health report should contain:



\- execution timestamp

\- evaluated components

\- observations

\- findings

\- warnings

\- confidence

\- evidence references

\- unresolved uncertainty



---



# Dependencies



This capability depends upon:



Knowledge



\- Runtime

\- Workspace

\- Providers

\- Configuration



Diagnostics



\- Runtime Diagnostics

\- Provider Diagnostics

\- Workspace Diagnostics

\- Configuration Diagnostics



Playbooks



\- Verify Installation

\- Verify Provider

\- Verify Workspace



---



# Operational Boundaries



This capability shall not:



\- restart Runtime

\- reload configuration

\- repair Workspace

\- reconnect Providers

\- change configuration

\- modify files



Its responsibility ends after reporting.



---



# Failure Handling



When evidence cannot be collected:



\- identify missing evidence

\- record collection limitations

\- reduce confidence accordingly

\- continue evaluation where possible



Missing evidence should never be interpreted as evidence of failure.



---



# Future Evolution



Future versions may support:



capabilities/health/



runtime-health.md



provider-health.md



workspace-health.md



configuration-health.md



filesystem-health.md



trend-analysis.md



health-history.md



predictive-health.md



---



# Summary



Health Checks provides automated, repeatable, evidence-driven assessment of OpenClaw operational health.



It integrates Knowledge, Architecture, Diagnostics, and Playbooks into a unified read-only capability that supports continuous observation while preserving system integrity.

