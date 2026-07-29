# Diagnostic Automation



Version: 1.0



Status: Draft



Capability Type: Read-Only Automation



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Automatically collect operational evidence from OpenClaw and organize it into a structured diagnostic package suitable for investigation, incident reporting, and operational learning.



This capability performs evidence acquisition only.



---



# Related Documents



Knowledge



\- ../knowledge/logs.md

\- ../knowledge/runtime.md

\- ../knowledge/workspace.md

\- ../knowledge/configuration.md

\- ../knowledge/filesystem.md

\- ../knowledge/providers.md

\- ../knowledge/environment.md



Architecture



\- ../architecture/components.md

\- ../architecture/runtime-flow.md

\- ../architecture/data-flow.md



Diagnostics



\- ../diagnostics/runtime.md

\- ../diagnostics/provider.md

\- ../diagnostics/workspace.md

\- ../diagnostics/configuration.md

\- ../diagnostics/filesystem.md

\- ../diagnostics/cli.md



Playbooks



\- ../playbooks/collect-diagnostics.md



Capabilities



\- health-checks.md

\- configuration-validation.md

\- provider-testing.md

\- model-testing.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/core/EXECUTION\_MODEL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/MEMORY\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose of Diagnostic Automation



Diagnostic Automation standardizes operational evidence collection.



Instead of requiring operators to manually gather information, this capability executes a repeatable collection workflow that produces a consistent diagnostic package.



No analysis or remediation is performed.



---



# Scope



This capability automates collection of:



\- Runtime state

\- Configuration state

\- Workspace state

\- Provider state

\- Model state

\- Filesystem observations

\- CLI observations

\- Health indicators

\- Log summaries



Business-specific artifacts are outside the scope.



---



# Inputs



Typical inputs include:



\- Runtime status

\- Effective Configuration

\- Workspace metadata

\- Provider metadata

\- Model metadata

\- Filesystem metadata

\- CLI output

\- Log files



All inputs remain read-only.



---



# Outputs



The capability produces a structured diagnostic package containing:



\- collected evidence

\- collection metadata

\- execution summary

\- warnings

\- collection limitations

\- confidence estimate



No root-cause analysis is generated.



---



# Collection Domains



## Runtime



Collect:



\- Runtime status

\- initialization state

\- worker status

\- execution metadata



---



## Configuration



Collect:



\- Effective Configuration

\- configuration sources

\- configuration metadata

\- validation results



---



## Workspace



Collect:



\- Workspace structure

\- metadata

\- accessibility observations



---



## Provider



Collect:



\- configured Provider

\- connectivity observations

\- authentication results

\- service availability



---



## Models



Collect:



\- configured models

\- available models

\- unavailable models

\- compatibility observations



---



## Filesystem



Collect:



\- directory structure

\- permissions

\- storage observations

\- file metadata



---



## Logs



Collect:



\- Runtime logs

\- CLI logs

\- diagnostic logs

\- timestamp information



---



# Execution Workflow



The capability follows the standard automation lifecycle.



```

Define Scope



↓



Collect Runtime Evidence



↓



Collect Configuration Evidence



↓



Collect Workspace Evidence



↓



Collect Provider Evidence



↓



Collect Model Evidence



↓



Collect Filesystem Evidence



↓



Collect Logs



↓



Verify Completeness



↓



Estimate Confidence



↓



Generate Diagnostic Package

```



Collection order should remain deterministic.



---



# Evidence Collection Principles



Evidence should be:



\- complete

\- reproducible

\- attributable

\- timestamped

\- traceable

\- minimally invasive



Original evidence should never be modified.



---



# Package Organization



The generated package should clearly separate:



Evidence



Metadata



Observations



Warnings



Collection Limitations



Confidence Assessment



Future investigation should not require reorganization of the package.



---



# Completeness Verification



Before reporting, verify that:



\- requested domains were evaluated

\- collected evidence is traceable

\- missing evidence is documented

\- collection timestamps are available

\- package metadata is complete



---



# Confidence Assessment



Confidence should consider:



\- completeness

\- consistency

\- freshness

\- source reliability

\- collection success



Confidence should decrease when evidence is incomplete.



---



# Report Structure



A diagnostic automation report should include:



\- execution timestamp

\- collection scope

\- completed domains

\- omitted domains

\- warnings

\- confidence estimate

\- evidence inventory



---



# Dependencies



This capability depends upon:



Knowledge



\- Logs

\- Runtime

\- Workspace

\- Configuration

\- Providers



Architecture



\- Components

\- Runtime Flow

\- Data Flow



Diagnostics



\- All Diagnostic documents



Playbooks



\- Collect Diagnostics



Capabilities



\- Health Checks

\- Configuration Validation

\- Provider Testing

\- Model Testing



---



# Operational Boundaries



This capability shall not:



\- repair Runtime

\- modify Workspace

\- rewrite configuration

\- restart services

\- rotate credentials

\- remove files

\- execute user workloads



Its responsibility ends after producing a diagnostic package.



---



# Failure Handling



When collection cannot be completed:



\- continue collecting independent evidence

\- document unavailable sources

\- preserve partial results

\- reduce confidence appropriately



Partial evidence is preferable to no evidence.



---



# Future Evolution



Future versions may support:



capabilities/diagnostics/



continuous-monitoring.md



scheduled-collection.md



incident-packaging.md



forensic-preservation.md



evidence-correlation.md



distributed-collection.md



---



# Summary



Diagnostic Automation provides a repeatable, evidence-driven mechanism for collecting operational information across all major OpenClaw components.



By standardizing evidence acquisition while preserving system state, the capability establishes a reliable foundation for diagnostics, incident response, operational learning, and future autonomous analysis.

