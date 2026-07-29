# OpenClaw Diagnostics

Version: 1.0

Status: Draft

Owner: SAM Framework

Related Documents

- ../README.md
- ../MODULE_SPECIFICATION.md
- ../architecture/README.md
- ../knowledge/README.md
- ../playbooks/README.md

Framework References

- docs/models/TRUST_MODEL.md
- docs/models/DECISION_MODEL.md
- docs/models/RISK_MODEL.md
- docs/models/MEMORY_MODEL.md
- docs/core/THINKING_PROTOCOL.md

---

# Purpose

This directory defines how operational problems are investigated within the OpenClaw Module.

Diagnostics focuses on understanding system behavior through structured observation, evidence collection, hypothesis evaluation, and verification.

The objective is to reduce uncertainty before any operational action is recommended or executed.

---

# Philosophy

Diagnostics is an investigation process.

It is not:

- a troubleshooting checklist,
- a repair guide,
- a collection of assumptions,
- or a list of common fixes.

Diagnostics seeks to answer one question:

> **"What is actually happening?"**

Only after that question is answered should remediation be considered.

---

# Relationship with the Framework

Diagnostics follows the reasoning process defined by the Framework.

The typical flow is:

Observe

↓

Collect Evidence

↓

Assess Trust

↓

Generate Hypotheses

↓

Evaluate Risk

↓

Recommend Action

↓

Execute (if approved)

↓

Verify

↓

Capture Learning

Each stage maps directly to Framework models.

---

# Relationship with Knowledge

Knowledge explains recurring operational behavior.

Diagnostics determines whether a current observation matches existing knowledge.

Possible outcomes include:

- Existing knowledge explains the issue.
- Existing knowledge is incomplete.
- No existing knowledge applies.

In the third case, the investigation may become Research.

---

# Relationship with Playbooks

Diagnostics identifies the problem.

Playbooks resolve the problem.

A diagnostic document should never prescribe operational changes unless the corresponding Playbook exists.

Instead, diagnostics should reference the appropriate Playbook whenever possible.

---

# Relationship with Incidents

Every significant incident should begin with diagnostics.

The expected lifecycle is:

Incident

↓

Diagnostics

↓

Evidence

↓

Root Cause

↓

Knowledge

↓

Playbook Improvement

↓

Future Prevention

This ensures that every incident strengthens the operational maturity of the module.

---

# Diagnostic Principles

All diagnostic activities should follow these principles.

## Evidence First

Never conclude before sufficient evidence has been collected.

---

## Reproducibility

Whenever possible, findings should be reproducible.

---

## Traceability

Every conclusion should be traceable to supporting evidence.

---

## Least Assumption

Prefer observable facts over assumptions.

---

## Incremental Investigation

Gather information gradually.

Avoid large investigative jumps unsupported by evidence.

---

## Verification

Every conclusion should be tested whenever practical.

---

# Diagnostic Workflow

The recommended workflow is:

1. Define the observed symptom.

2. Collect relevant evidence.

3. Assess evidence quality using the Trust Model.

4. Generate candidate hypotheses.

5. Eliminate inconsistent hypotheses.

6. Identify the most probable root cause.

7. Assess operational risk.

8. Recommend appropriate Playbook(s).

9. Verify the outcome.

10. Capture lessons learned.

This workflow should remain consistent across all OpenClaw diagnostics.

---

# Categories

Future diagnostic documents may include:

## Installation

Installation failures.

## Configuration

Configuration inconsistencies.

## Providers

Authentication failures.

Rate limits.

Connectivity.

Model availability.

## Runtime

Startup failures.

Execution failures.

Worker failures.

## Agents

Identity issues.

Workspace synchronization.

Agent lifecycle.

## Workspace

Corrupted files.

Missing configuration.

Permission issues.

## Performance

Latency.

Resource utilization.

Unexpected behavior.

Each diagnostic document should focus on one operational concern.

---

# Evidence Sources

Common evidence sources include:

- log files,
- configuration files,
- runtime output,
- API responses,
- operating system information,
- filesystem state,
- process status,
- user observations.

Evidence quality should always be evaluated before drawing conclusions.

---

# Quality Standards

A diagnostic document should:

- remain objective,
- separate facts from hypotheses,
- identify uncertainty,
- reference supporting evidence,
- avoid speculative conclusions,
- document verification methods.

If uncertainty remains unresolved, it should be explicitly documented.

---

# Future Expansion

Future documents may include:

provider.md

runtime.md

workspace.md

filesystem.md

network.md

authentication.md

logs.md

performance.md

startup.md

shutdown.md

These documents extend the diagnostic knowledge base without altering the architectural principles defined here.

---

# Success Criteria

The Diagnostics directory succeeds when operators can:

- identify problems systematically,
- distinguish symptoms from root causes,
- make evidence-based decisions,
- reduce unnecessary operational risk,
- continuously improve diagnostic quality through accumulated experience.

---

# Summary

The Diagnostics directory provides the investigative discipline of the OpenClaw Module.

Rather than prescribing immediate fixes, it establishes a structured process for understanding operational behavior, reducing uncertainty, and enabling informed decision making.

By separating investigation from remediation, Diagnostics complements Knowledge and Playbooks while remaining fully aligned with the reasoning principles of the SAM Framework.