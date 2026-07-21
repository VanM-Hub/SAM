# CLI Diagnostics



Version: 1.0



Status: Draft



Knowledge Type: Operational



Evidence Level: Observed



Confidence: Medium



Owner: OpenClaw Module



Related Documents



Knowledge



\- ../knowledge/cli.md

\- ../knowledge/runtime.md

\- ../knowledge/configuration.md

\- ../knowledge/workspace.md

\- ../knowledge/logs.md



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



This document defines a structured methodology for investigating Command Line Interface (CLI) issues.



Its objective is to determine whether observed problems originate from the CLI itself, user interaction, Runtime communication, or downstream components.



This document intentionally excludes corrective procedures.



---



# Scope



CLI Diagnostics investigates:



\- command parsing

\- argument handling

\- command execution

\- Runtime communication

\- output generation

\- error reporting

\- user interaction



Repair activities are outside the scope of this document.



---



# Diagnostic Principles



The CLI should be evaluated as an interface rather than as the execution engine.



Evidence should distinguish between:



\- invalid command input

\- argument parsing failure

\- command dispatch failure

\- Runtime communication failure

\- output rendering failure

\- Runtime execution failure



The CLI may expose failures originating elsewhere.



---



# Diagnostic Workflow

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





The workflow follows the standard diagnostic methodology defined by the Core Framework.



---



# Evidence Sources



Typical evidence sources include:



\- CLI output

\- command history

\- Runtime logs

\- execution events

\- Health Check reports

\- Workspace observations



No single evidence source should be considered definitive.



---



# Common Symptom Categories



Typical CLI symptoms include:



\- unknown command

\- invalid option

\- missing argument

\- command timeout

\- unexpected output

\- no response

\- abnormal exit code



Identical symptoms may originate from different architectural layers.



---



# Relationship with Runtime



The CLI delegates execution to the Runtime.



CLI Diagnostics should determine whether failures occur before, during, or after Runtime interaction.



---



# Relationship with Configuration



Configuration may influence command behavior.



Unexpected CLI behavior should not automatically be interpreted as a CLI failure.



---



# Diagnostic Boundaries



This document does not:



\- modify commands

\- change configuration

\- restart Runtime

\- repair parsing failures

\- alter Workspace



Its responsibility is evidence-based investigation only.



---



# Future Evolution



Future documentation may expand into:



diagnostics/cli/



README.md



command-parsing.md



argument-validation.md



runtime-communication.md



output-rendering.md



exit-codes.md



interactive-mode.md



---



# Summary



CLI Diagnostics is an evidence-driven methodology for evaluating the Command Line Interface.



By separating interface behavior from Runtime behavior and distinguishing user interaction from execution, OpenClaw improves diagnostic accuracy while reducing incorrect attribution of operational failures.

