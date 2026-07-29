# Verify Installation



Version: 1.0



Status: Draft



Playbook Type: Verification



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Verify that an OpenClaw installation is complete, internally consistent, and operationally ready without modifying the system.



This playbook gathers evidence only.



---



# Related Documents



Knowledge



\- ../knowledge/environment.md

\- ../knowledge/filesystem.md

\- ../knowledge/runtime.md

\- ../knowledge/startup.md

\- ../knowledge/health-checks.md



Diagnostics



\- ../diagnostics/runtime.md

\- ../diagnostics/filesystem.md

\- ../diagnostics/configuration.md



Framework



\- docs/core/EXECUTION\_MODEL.md

\- docs/core/THINKING\_PROTOCOL.md



---



# Preconditions



The operator should have:



\- read access to the installation

\- access to the CLI

\- permission to inspect logs

\- permission to inspect configuration



No administrative privileges are required unless explicitly documented.



---



# Expected Outcome



The operator can determine whether:



\- installation appears complete

\- required files exist

\- Runtime can initialize

\- configuration can be resolved

\- installation is ready for operational use



---



# Verification Steps



## Step 1 — Verify Installation Structure



Confirm that expected directories and files are present.



Record observations.



Do not create missing files.



---



## Step 2 — Verify Configuration Availability



Determine whether configuration sources are present and readable.



Do not modify configuration.



---



## Step 3 — Verify Runtime Initialization



Observe Runtime startup behavior.



Record initialization results.



Do not restart services repeatedly.



---



## Step 4 — Verify CLI Availability



Confirm that the CLI is accessible.



Observe command availability.



Do not execute commands that modify state.



---



## Step 5 — Verify Health Indicators



Observe available health information.



Record abnormal conditions.



---



## Step 6 — Record Findings



Summarize observations.



Separate facts from interpretations.



---



# Verification Criteria



Successful verification should demonstrate:



\- installation completeness

\- readable configuration

\- accessible Runtime

\- functional CLI

\- no critical initialization failures



---



# Evidence Collection



Collect evidence such as:



\- CLI output

\- Runtime logs

\- directory structure

\- configuration availability

\- health reports



Evidence should remain unchanged.



---



# Recovery Considerations



This playbook performs no recovery.



Unexpected findings should be investigated using the Diagnostics documentation before any corrective action.



---



# Completion Checklist



\- Installation inspected

\- Runtime observed

\- CLI observed

\- Configuration inspected

\- Findings documented



---



# Summary



This playbook verifies installation readiness using non-destructive observation and evidence collection.

