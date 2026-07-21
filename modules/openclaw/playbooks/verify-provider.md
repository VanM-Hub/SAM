# Verify Provider



Version: 1.0



Status: Draft



Playbook Type: Verification



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Verify that an AI Provider is accessible, properly configured, and operationally available without modifying the system.



This playbook collects evidence only.



---



# Related Documents



Knowledge



\- ../knowledge/providers.md

\- ../knowledge/models.md

\- ../knowledge/configuration.md

\- ../knowledge/runtime.md

\- ../knowledge/environment-variables.md

\- ../knowledge/networking.md

\- ../knowledge/health-checks.md



Diagnostics



\- ../diagnostics/provider.md

\- ../diagnostics/runtime.md

\- ../diagnostics/configuration.md



Framework



\- docs/core/EXECUTION\_MODEL.md

\- docs/core/THINKING\_PROTOCOL.md

\- docs/models/TRUST\_MODEL.md



---



# Preconditions



The operator should have:



\- access to the configured Provider

\- permission to inspect configuration

\- access to Runtime logs

\- access to the CLI



No configuration changes should be performed during this playbook.



---



# Expected Outcome



The operator can determine whether:



\- the configured Provider is reachable

\- authentication appears valid

\- configured models are available

\- Runtime can communicate with the Provider

\- no critical Provider-related anomalies are observed



---



# Verification Steps



## Step 1 — Identify Active Provider



Determine which Provider the Runtime intends to use.



Record:



\- Provider name

\- Provider configuration source

\- selected model (if applicable)



Do not modify Provider selection.



---



## Step 2 — Verify Configuration Resolution



Confirm that the Effective Configuration resolves to the expected Provider.



Record observations.



Do not edit configuration.



---



## Step 3 — Verify Provider Reachability



Observe whether the Runtime can communicate with the Provider.



Record:



\- successful connection

\- timeout

\- authentication response

\- unexpected communication failures



Do not retry excessively.



---



## Step 4 — Verify Model Availability



Observe whether the configured model appears available.



Record any discrepancies between configured and available models.



Do not change model selection.



---



## Step 5 — Observe Runtime Behavior



Observe Runtime interaction with the Provider.



Record:



\- initialization

\- request dispatch

\- response handling

\- reported errors



Avoid interpreting causes during this stage.



---



## Step 6 — Record Findings



Document:



\- observations

\- collected evidence

\- remaining uncertainty

\- potential hypotheses (if applicable)



Separate evidence from conclusions.



---



# Verification Criteria



Successful verification should demonstrate:



\- Provider configuration is resolvable

\- Provider is reachable

\- authentication appears valid

\- configured model is observable

\- Runtime can communicate with the Provider



---



# Evidence Collection



Collect evidence such as:



\- Runtime logs

\- Provider status information

\- CLI output

\- Effective Configuration

\- networking observations



Evidence should remain unchanged.



---



# Recovery Considerations



This playbook performs no recovery.



Unexpected findings should be investigated using:



\- diagnostics/provider.md

\- diagnostics/runtime.md

\- diagnostics/configuration.md



before any corrective action is considered.



---



# Completion Checklist



\- Active Provider identified

\- Effective Configuration verified

\- Provider reachability observed

\- Model availability observed

\- Runtime interaction observed

\- Findings documented



---



# Summary



This playbook verifies Provider operational readiness through structured, non-destructive observation.



It establishes confidence that the configured Provider can participate in Runtime execution while preserving system state and maintaining the principle of evidence-based verification.

