"""Concrete compliance checkers (P1-008).

Each Batch module defines concrete BaseComplianceCheck subclasses that
implement execute() against the BaselineSnapshot (P1-007). The builder
module assembles all 99 checkers into a dict keyed by check_id, ready
for the BaselineBackedSessionRunner (P1-008 CLI layer).
"""
