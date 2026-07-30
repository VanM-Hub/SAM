"""
Guardian Justification Builder.

Builds DecisionJustification from DecisionInput, Assessment, Intent, Situation, Transition.
Deterministic. Rule-based. No domain knowledge.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from .justification import DecisionJustification, JustificationSection, EvidenceReference, RuleReference
from .decision_input import DecisionInput, EligibilityStatus
from .intent import GuardianIntent, IntentType


class JustificationBuilder:
    """Builds DecisionJustification from operational data."""

    def build(
        self,
        decision_input: DecisionInput,
        intent: Optional[GuardianIntent] = None,
    ) -> DecisionJustification:
        """Build a complete justification."""
        sections = []

        # Section 1: Overview
        overview_evidence = [EvidenceReference(step="handoff",source_id=decision_input.input_id,source_type="DecisionInput",timestamp=decision_input.timestamp)]
        sections.append(JustificationSection(
            title="Overview",
            content=f"DecisionInput {decision_input.input_id} eligibility: {decision_input.eligibility.name}",
            evidence=overview_evidence,
        ))

        # Section 2: Intent
        if intent:
            intent_evidence = [EvidenceReference(step="intent",source_id=intent.intent_id,source_type="GuardianIntent",timestamp=intent.timestamp)]
            intent_rules = [RuleReference(rule_name="intent_type_classification",rule_type="mapping",triggered=True,
                                          input_values={"intent_type":intent.intent_type.name},output_value=intent.policy_name)]
            sections.append(JustificationSection(
                title="Intent Source",
                content=f"Intent: {intent.intent_type.name} ({intent.policy_name}) priority={intent.priority.name} confidence={intent.confidence}",
                evidence=intent_evidence,rules=intent_rules,
            ))

        # Section 3: Eligibility
        elig_evidence = [EvidenceReference(step="eligibility",source_id=decision_input.input_id,source_type="EligibilityEngine",timestamp=decision_input.timestamp)]
        elig_rules = [RuleReference(rule_name="eligibility_check",rule_type="eligibility",triggered=True,
                                     input_values={"min_confidence":20,"min_evidence":1},
                                     output_value=decision_input.eligibility.name)]
        sections.append(JustificationSection(
            title="Eligibility",
            content=f"Status: {decision_input.eligibility.name} confidence={decision_input.confidence}",
            evidence=elig_evidence,rules=elig_rules,
        ))

        # Section 4: Candidates
        cand_count = len(decision_input.candidates)
        cand_evidence = [EvidenceReference(step="mapping",source_id=c.candidate_id,source_type="DecisionCandidate",timestamp=decision_input.timestamp) for c in decision_input.candidates[:3]]
        sections.append(JustificationSection(
            title=f"Candidates ({cand_count})",
            content=f"Mapped {cand_count} candidate(s) for handoff",
            evidence=cand_evidence,
        ))

        summary = f"Justification for {decision_input.input_id}: {decision_input.eligibility.name}, {cand_count} candidates, confidence {decision_input.confidence}"

        return DecisionJustification(
            justification_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            decision_input_id=decision_input.input_id,
            source_intent_id=intent.intent_id if intent else "",
            sections=sections,
            summary=summary,
        )
