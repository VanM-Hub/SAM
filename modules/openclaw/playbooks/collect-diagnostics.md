# Collect Diagnostics



Version: 1.0



Status: Draft



Playbook Type: Evidence Collection



Execution Mode: Read-Only



Risk Level: Low



Owner: OpenClaw Module



---



# Purpose



Collect operational evidence required for investigation without modifying the system.



The objective is to produce a consistent diagnostic package that supports troubleshooting, incident analysis, and future knowledge capture.



This playbook performs evidence collection only.



---



# Related Documents



Knowledge



\- ../knowledge/logs.md

\- ../knowledge/runtime.md

\- ../knowledge/workspace.md

\- ../knowledge/configuration.md

\- ../knowledge/filesystem.md

\- ../knowledge/environment.md

\- ../knowledge/providers.md



Diagnostics



\- ../diagnostics/provider.md

\- ../diagnostics/workspace.md

\- ../diagnostics/configuration.md

\- ../diagnostics/runtime.md

\- ../diagnostics/cli.md

\- ../diagnostics/filesystem.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/core/EXECUTION\_MODEL.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/MEMORY\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Preconditions



The operator should have:



\- read access to the Workspace

\- permission to inspect logs

\- access to Runtime status

\- access to the CLI

\- permission to read configuration



The target system should remain unchanged throughout the collection process.



---



# Expected Outcome



The operator produces a diagnostic package containing sufficient evidence to support later investigation.



The package should be suitable for independent review.



---



# Evidence Collection Principles



Evidence should be:



\- complete

\- traceable

\- reproducible

\- minimally invasive

\- timestamped

\- attributable



Collection should preserve the original evidence.



---



# Collection Scope



The diagnostic package should include, where applicable:



\- Runtime logs

\- CLI observations

\- configuration metadata

\- Workspace metadata

\- filesystem observations

\- Provider observations

\- health-check results

\- environment information



Additional evidence may be included when relevant.



---



# Collection Procedure



## Step 1 — Define Investigation Scope



Record:



\- investigation purpose

\- target Workspace

\- target Runtime

\- collection timestamp



The scope should be documented before evidence collection begins.



---



## Step 2 — Collect Runtime Evidence



Collect:



\- Runtime status

\- Runtime logs

\- startup observations

\- shutdown observations (if applicable)



Do not restart Runtime.



---



## Step 3 — Collect Configuration Evidence



Collect:



\- Effective Configuration

\- configuration sources

\- configuration metadata



Do not modify configuration.



---



## Step 4 — Collect Workspace Evidence



Collect:



\- Workspace structure

\- Workspace metadata

\- operational artifacts



Do not modify Workspace contents.



---



## Step 5 — Collect Provider Evidence



Collect:



\- configured Provider

\- observed Provider availability

\- model availability

\- communication observations



Do not alter Provider configuration.



---



## Step 6 — Collect Filesystem Evidence



Collect:



\- directory structure

\- file metadata

\- storage observations

\- permission observations



Do not change filesystem contents.



---



## Step 7 — Organize Evidence



Group collected evidence into logical categories.



Preserve:



\- timestamps

\- original filenames

\- source information



Avoid renaming evidence unless documented.



---



## Step 8 — Verify Evidence Completeness



Verify that the collected package contains:



\- all planned evidence

\- no obvious omissions

\- sufficient metadata

\- traceable sources



Document any missing evidence.



---



## Step 9 — Record Findings



Record:



\- observations

\- collection limitations

\- known uncertainties

\- evidence summary



Separate observations from interpretation.



---



# Verification Criteria



Successful collection should demonstrate:



\- evidence completeness

\- traceability

\- reproducibility

\- preserved integrity

\- documented limitations



---



# Evidence Package Structure



A diagnostic package should clearly identify:



\- collection time

\- collector

\- system context

\- evidence sources

\- collection scope

\- verification status



The package should remain understandable without additional explanation.



---



# Recovery Considerations



This playbook performs no recovery.



Collected evidence should be analyzed using the Diagnostics documentation before corrective action is considered.



---



# Completion Checklist



\- Investigation scope recorded

\- Runtime evidence collected

\- Configuration evidence collected

\- Workspace evidence collected

\- Provider evidence collected

\- Filesystem evidence collected

\- Evidence organized

\- Completeness verified

\- Findings documented



---



# Operational Notes



This playbook intentionally avoids:



\- modifying configuration

\- restarting Runtime

\- editing Workspace contents

\- changing Provider settings

\- repairing detected issues



Its sole responsibility is structured evidence acquisition.



---



# Future Evolution



Future documentation may expand into:



playbooks/collect-diagnostics/



README.md



evidence-packaging.md



evidence-validation.md



automated-collection.md



incident-collection.md



forensic-collection.md



---



# Summary



This playbook defines a repeatable, evidence-driven process for collecting operational information without altering system state.



By emphasizing completeness, traceability, and verification, it provides a reliable foundation for diagnostics, incident response, operational learning, and future automation.

