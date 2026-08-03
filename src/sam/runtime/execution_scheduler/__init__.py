"""Execution Scheduler — Unit 6 Reference Runtime.

Executes approved operations in Strict Linear Ordering (ADR-005),
observing Contract-declared idempotency (ADR-003),
with linear failure propagation (ADR-004).

Public API: create_execution, schedule, transition, verify, get, get_health
"""
