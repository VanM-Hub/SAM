markdown

# Model Testing



Version: 1.0



Status: Draft



Capability Type: Read-Only Automation



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Automatically verify that configured AI Models are available, resolvable, and operationally usable without modifying the system.



This capability evaluates model availability independently from Provider availability.



---



# Related Documents



Knowledge



\- ../knowledge/models.md

\- ../knowledge/providers.md

\- ../knowledge/configuration.md

\- ../knowledge/runtime.md



Architecture



\- ../architecture/provider-model.md

\- ../architecture/runtime-flow.md

\- ../architecture/data-flow.md



Diagnostics



\- ../diagnostics/provider.md

\- ../diagnostics/runtime.md

\- ../diagnostics/configuration.md



Playbooks



\- ../playbooks/verify-provider.md

\- ../playbooks/collect-diagnostics.md



Capabilities



\- health-checks.md

\- provider-testing.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/core/EXECUTION\_MODEL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose of Model Testing



Model Testing determines whether configured models are operationally available and compatible with the current Provider configuration.



The capability does not execute user prompts or benchmark model quality.



---



# Scope



Model Testing evaluates:



\- configured model resolution

\- model availability

\- Provider compatibility

\- model metadata

\- access permissions

\- operational readiness



Model performance evaluation is outside the scope.



---



# Inputs



Typical inputs include:



\- Effective Configuration

\- configured Provider

\- configured Model

\- Runtime metadata

\- Provider model catalogue



Inputs remain read-only.



---



# Outputs



The capability produces a structured report containing:



\- configured models

\- resolved models

\- available models

\- unavailable models

\- compatibility findings

\- confidence estimate

\- supporting evidence



---



# Testing Dimensions



## Model Resolution



Verify that every configured model can be resolved.



Record:



\- configured identifier

\- resolved identifier

\- unresolved references



---



## Availability Testing



Verify whether each configured model is observable from the Provider.



Possible outcomes include:



\- available

\- unavailable

\- deprecated

\- unknown



Availability should be based on observed evidence.



---



## Compatibility Testing



Evaluate whether the selected model is compatible with:



\- configured Provider

\- Runtime expectations

\- supported interfaces



Compatibility should not be inferred without evidence.



---



## Metadata Verification



Collect model metadata where available.



Examples include:



\- model identifier

\- version

\- family

\- capabilities

\- context length

\- availability status



Metadata collection should not modify Provider state.



---



## Accessibility Testing



Verify whether the configured credentials allow access to the model.



Observe:



\- accessible

\- restricted

\- unauthorized

\- unavailable



Access should never be assumed from Provider availability alone.



---



# Execution Workflow



The capability follows the standard automation lifecycle.

Load Configuration



↓



Resolve Provider



↓



Resolve Models



↓



Verify Availability



↓



Verify Compatibility



↓



Estimate Confidence



↓



Generate Report



text



No user inference requests should be executed.



---



# Evidence Collection



Evidence may include:



\- Provider model listings

\- Runtime observations

\- configuration metadata

\- API metadata

\- CLI observations



Sensitive information should be excluded from reports.



---



# Result Classification



Each evaluated model should be classified as:



\- Available

\- Warning

\- Unavailable

\- Deprecated

\- Unknown



Unknown should be preferred whenever evidence is insufficient.



---



# Confidence Assessment



Confidence should consider:



\- successful model discovery

\- metadata completeness

\- Provider response consistency

\- repeated observations

\- evidence freshness



Confidence should never exceed available evidence.



---



# Report Structure



A Model Testing report should include:



\- execution timestamp

\- configured Provider

\- configured models

\- resolved models

\- unavailable models

\- compatibility findings

\- confidence estimate

\- unresolved uncertainty



---



# Dependencies



This capability depends upon:



Knowledge



\- Models

\- Providers

\- Configuration



Architecture



\- Provider Model

\- Runtime Flow



Diagnostics



\- Provider Diagnostics

\- Configuration Diagnostics



Capabilities



\- Health Checks

\- Provider Testing



---



# Operational Boundaries



This capability shall not:



\- download models

\- install models

\- remove models

\- change Provider selection

\- modify configuration

\- execute user prompts



Its responsibility ends after reporting.



---



# Failure Handling



When model validation cannot be completed:



\- identify the failed validation stage

\- distinguish Provider failures from Model failures

\- document missing evidence

\- reduce confidence appropriately



Model unavailability should not automatically imply Provider failure.



---



# Future Evolution



Future versions may support:



capabilities/models/



model-catalog.md



compatibility-matrix.md



model-history.md



model-deprecation.md



quota-analysis.md



cost-analysis.md



benchmark-comparison.md



---



# Summary



Model Testing provides automated, evidence-based verification of model availability and compatibility.



By treating Models as independent operational entities rather than simple Provider attributes, the capability enables precise diagnostics, reliable reporting, and future extensibility while preserving the read-only execution model.

