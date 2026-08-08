"""explanation — WP-06 (IP-3.1-001).

- decision/ : DecisionExplanation (decision, evidence, rationale,
             confidence, missing evidence).
- trust/    : trust / confidence descriptors.
"""

from sam.governance_intelligence.explanation.decision import (
    DecisionExplanation,
    build_explanation,
    explanation_summary,
)

__all__ = ["DecisionExplanation", "build_explanation", "explanation_summary"]
