"""Audit Recorder — terminal unit of the SAM Reference Runtime.

Responsibility:
- Receive execution outcomes
- Create immutable audit records
- Maintain traceability backward through the entire chain
- Perform verification (state transition Recorded → Verified per ADR-007)
- Archive records (terminal)
- Terminate failure propagation (ADR-004)

Dependencies: shared only (I1-001 §2.7).
"""

__all__ = []
