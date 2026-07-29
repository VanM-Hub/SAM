# Verify Workspace



Version: 1.0



Status: Draft



Playbook Type: Verification



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Verify that a Workspace provides a valid operational context for OpenClaw without modifying its contents.



This playbook performs observation and evidence collection only.



---



# Related Documents



Knowledge



\- ../knowledge/workspace.md

\- ../knowledge/filesystem.md

\- ../knowledge/configuration.md

\- ../knowledge/runtime.md

\- ../knowledge/permissions.md

\- ../knowledge/health-checks.md



Diagnostics



\- ../diagnostics/workspace.md

\- ../diagnostics/filesystem.md

\- ../diagnostics/configuration.md



Architecture



\- ../architecture/workspace-model.md

\- ../architecture/components.md



Framework



\- docs/core/EXECUTION\_MODEL.md

\- docs/core/THINKING\_PROTOCOL.md

\- docs/models/TRUST\_MODEL.md



---



# Preconditions



The operator should have:



\- read access to the Workspace

\- permission to inspect Workspace metadata

\- access to Runtime logs

\- access to the CLI



No files should be modified during this playbook.



---



# Expected Outcome



The operator can determine whether:



\- the Workspace exists

\- the Workspace structure is valid

\- required operational artifacts are present

\- the Runtime can recognize the Workspace

\- the Workspace appears operationally ready



---



# Verification Steps



## Step 1 — Identify Target Workspace



Determine the Workspace under investigation.



Record:



\- Workspace location

\- Workspace identifier (if applicable)

\- selection method



Do not change the active Workspace.



---



## Step 2 — Verify Workspace Accessibility



Observe whether the Workspace can be accessed.



Verify:



\- directory availability

\- read access

\- expected structure



Record observations only.



---



## Step 3 — Verify Workspace Structure



Compare the observed directory structure with the expected Workspace model.



Observe:



\- required directories

\- required operational files

\- missing artifacts

\- unexpected artifacts



Do not create or remove files.



---



## Step 4 — Verify Runtime Recognition



Observe whether the Runtime successfully recognizes the Workspace.



Record:



\- Workspace discovery

\- Workspace initialization

\- reported inconsistencies



Do not restart the Runtime.



---



## Step 5 — Verify Operational Readiness



Observe whether the Workspace satisfies the minimum operational requirements.



Evaluate:



\- accessibility

\- structural consistency

\- configuration availability

\- Runtime compatibility



Do not interpret business-specific content.



---



## Step 6 — Record Findings



Document:



\- observations

\- supporting evidence

\- identified anomalies

\- remaining uncertainty



Separate factual observations from interpretation.



---



# Verification Criteria



Successful verification should demonstrate:



\- Workspace exists

\- Workspace is accessible

\- Workspace structure matches expectations

\- Runtime recognizes the Workspace

\- no critical structural inconsistencies are observed



---



# Evidence Collection



Collect evidence such as:



\- directory listings

\- Workspace metadata

\- Runtime logs

\- CLI output

\- filesystem observations



Evidence should remain unchanged.



---



# Recovery Considerations



This playbook performs no recovery.



Unexpected findings should be investigated using:



\- diagnostics/workspace.md

\- diagnostics/filesystem.md

\- diagnostics/configuration.md



before corrective actions are considered.



---



# Completion Checklist



\- Workspace identified

\- Accessibility verified

\- Structure inspected

\- Runtime recognition observed

\- Findings documented



---



# Summary



This playbook verifies that a Workspace provides a valid operational context for OpenClaw.



Verification is performed through structured observation and evidence collection without modifying Workspace contents, ensuring consistency with the evidence-based operational model defined by the Core Framework.

