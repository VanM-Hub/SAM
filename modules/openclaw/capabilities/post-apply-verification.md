# Post-Apply Verification



Version: 1.0



Status: Draft



Capability Type: Controlled Verification



Execution Mode: Verification



Risk Level: Variable



Owner: OpenClaw Module



---



# Purpose



Verify that an approved and executed system modification achieved its intended operational outcome without introducing unacceptable regressions.



Post-Apply Verification is the final gate before an execution is considered complete.



---



# Related Documents



Knowledge



\- ../knowledge/health-checks.md

\- ../knowledge/runtime.md

\- ../knowledge/providers.md

\- ../knowledge/models.md

\- ../knowledge/workspace.md

\- ../knowledge/configuration.md



Architecture



\- ../architecture/runtime-flow.md

\- ../architecture/data-flow.md



Diagnostics



\- ../diagnostics/runtime.md

\- ../diagnostics/provider.md

\- ../diagnostics/configuration.md

\- ../diagnostics/workspace.md



Playbooks



\- ../playbooks/verify-installation.md

\- ../playbooks/verify-provider.md

\- ../playbooks/verify-workspace.md

\- ../playbooks/collect-diagnostics.md



Capabilities



\- execution-planning.md

\- approval-gate.md

\- apply-configuration.md

\- apply-provider.md

\- rollback.md

\- health-checks.md

\- provider-testing.md

\- model-testing.md



Framework



\- docs/core/EXECUTION\_MODEL.md

\- docs/core/THINKING\_PROTOCOL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/RISK\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose of Post-Apply Verification



Confirm that:



\- the intended change was applied,

\- the system remains operational,

\- expected functionality is available,

\- no critical regression has been introduced.



Verification determines execution success.



---



# Scope



This capability evaluates the operational outcome after execution.



It does not modify the system.



If verification fails, recovery decisions are delegated to Rollback.



---



# Verification Principles



Verification shall be:



\- evidence-based

\- repeatable

\- objective

\- measurable

\- traceable



Subjective observations should not determine execution success.



---



# Verification Inputs



Required inputs include:



\- Execution Plan

\- Approval Decision

\- Execution Log

\- Configuration State

\- Runtime Status

\- Health Check Results



Optional inputs may include:



\- Diagnostic Package

\- Provider Test Results

\- Model Test Results



---



# Verification Categories



## Configuration Verification



Confirm:



\- intended configuration exists

\- configuration integrity maintained

\- references remain valid



---



## Runtime Verification



Confirm:



\- Runtime operational

\- workers functioning

\- startup completed successfully

\- no unexpected failures observed



---



## Provider Verification



Confirm:



\- configured Provider reachable

\- authentication successful

\- endpoint operational



---



## Model Verification



Confirm:



\- configured models available

\- expected capabilities accessible

\- model resolution successful



---



## Workspace Verification



Confirm:



\- workspace accessible

\- required files present

\- permissions unchanged

\- metadata consistent



---



# Operational Health Verification



Execute:



\- Health Checks

\- Runtime observations

\- Provider tests

\- Workspace validation



Verification should represent actual operational readiness.



---



# Success Criteria



Execution is considered successful only if:



\- configuration valid

\- runtime healthy

\- provider operational

\- models available

\- workspace accessible

\- health checks successful

\- no critical regression detected



Failure of any critical criterion prevents execution closure.



---



# Regression Assessment



Evaluate whether the applied change introduced:



\- unexpected failures

\- degraded functionality

\- performance issues

\- unavailable services

\- inconsistent state



Critical regressions require immediate evaluation.



---



# Verification Workflow



```

Execution Completed



↓



Collect Verification Evidence



↓



Verify Configuration



↓



Verify Runtime



↓



Verify Provider



↓



Verify Models



↓



Verify Workspace



↓



Evaluate Operational Health



↓



Execution Successful



or



Initiate Rollback Evaluation

```



Execution closes only after successful verification.



---



# Evidence Collection



Record:



\- verification timestamp

\- execution identifier

\- observed system state

\- health check results

\- provider status

\- model status

\- workspace status

\- operator observations



Verification evidence should support future audits.



---



# Verification Report



Generate a structured report containing:



\- execution summary

\- verification findings

\- operational status

\- detected regressions

\- remaining risks

\- final outcome



Reports shall remain immutable.



---



# Failure Handling



If verification fails:



\- preserve verification evidence

\- identify failed verification stage

\- notify operator

\- evaluate rollback conditions



Verification failure shall not automatically initiate rollback.



Rollback remains a separate decision.



---



# Dependencies



This capability depends upon:



Capabilities



\- Execution Planning

\- Approval Gate

\- Apply Configuration

\- Apply Provider

\- Rollback

\- Health Checks

\- Provider Testing

\- Model Testing



Knowledge



\- Runtime

\- Providers

\- Models

\- Workspace



Framework



\- Execution Model

\- Risk Model

\- Thinking Protocol



---



# Operational Boundaries



This capability shall not:



\- modify configuration

\- restart runtime

\- repair failures

\- bypass failed verification

\- suppress evidence



Verification concludes with an operational assessment.



---



# Future Evolution



Future versions may support:



capabilities/verification/



continuous-verification.md



canary-verification.md



performance-verification.md



security-verification.md



distributed-verification.md



verification-policy.md



---



# Summary



Post-Apply Verification confirms that an approved and executed change has produced the intended operational outcome.



By combining configuration validation, runtime observation, provider verification, model verification, workspace validation, and health assessment, this capability provides the final operational gate before execution is considered complete.



If successful, the execution may be closed.



If unsuccessful, the evidence supports informed recovery decisions without automatically initiating rollback.

