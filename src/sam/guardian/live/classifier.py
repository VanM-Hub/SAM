"""
Guardian Situation Classifier.

Classifies situation candidates into built-in situation types.
All rule-based. No AI, no machine learning.
Synchronous only.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .transition import RuntimeTransition, TransitionType, ImpactLevel
from .situation import (
    GuardianSituation, SituationType, SituationSeverity,
    SituationCandidate, SituationSummary, SituationStatistics,
)
from .correlator import TransitionCorrelator
from .severity import SituationSeverityCalculator


class SituationClassifier:
    """
    Rule-based classifier for operational situations.

    Built-in situation types:
        HEALTHY              — no significant transitions
        BUSY                 — many transitions, low impact
        APPROVAL_BOTTLENECK  — many approval-related transitions
        EXECUTION_DELAY      — execution-related transitions
        RUNTIME_INSTABILITY  — health/status changes
        RECOVERY             — recovery transitions
        CONFIGURATION_DRIFT  — version/registry changes
        RESOURCE_PRESSURE    — health critical transitions
        UNKNOWN              — unclassifiable
    """

    def __init__(self) -> None:
        self._correlator = TransitionCorrelator()
        self._severity_calculator = SituationSeverityCalculator()

    def classify(
        self,
        transitions: List[RuntimeTransition],
    ) -> List[GuardianSituation]:
        """
        Classify transitions into situations.

        Args:
            transitions: List of transitions to classify.

        Returns:
            List of classified GuardianSituation objects.
        """
        if not transitions:
            return []

        # Step 1: Correlate transitions
        candidates = self._correlator.correlate(transitions)

        # Step 2: Classify each candidate
        situations: List[GuardianSituation] = []
        now = datetime.now().timestamp()

        for candidate in candidates:
            situation_type = self._classify_type(candidate, transitions)
            severity = self._severity_calculator.calculate(candidate, transitions)
            affected_runtimes = list(set(candidate.runtimes))

            situation = GuardianSituation(
                situation_id=str(uuid.uuid4()),
                situation_type=situation_type,
                severity=severity,
                timestamp=now,
                duration_seconds=self._estimate_duration(candidate, transitions),
                related_transition_ids=candidate.transition_ids,
                affected_runtimes=affected_runtimes,
                description=self._build_description(situation_type, candidate),
                details={
                    "score": candidate.score,
                    "reason": candidate.reason,
                    "transition_count": len(candidate.transition_ids),
                },
            )
            situations.append(situation)

        # Sort by severity (most severe first)
        situations.sort(
            key=lambda s: s.severity.value,
            reverse=True,
        )

        return situations

    def _classify_type(
        self,
        candidate: SituationCandidate,
        all_transitions: List[RuntimeTransition],
    ) -> SituationType:
        """
        Classify a candidate into a situation type based on rules.

        Args:
            candidate: The situation candidate.
            all_transitions: All available transitions for lookup.

        Returns:
            SituationType based on rules.
        """
        # Build lookup
        trans_by_id = {t.transition_id: t for t in all_transitions}
        candidate_transitions = [
            trans_by_id[tid] for tid in candidate.transition_ids
            if tid in trans_by_id
        ]

        if not candidate_transitions:
            return SituationType.UNKNOWN

        # Count transition types in this candidate
        type_counts: Dict[str, int] = {}
        impact_counts: Dict[str, int] = {}
        for t in candidate_transitions:
            type_counts[t.transition_type.name] = (
                type_counts.get(t.transition_type.name, 0) + 1
            )
            impact_counts[t.impact.name] = (
                impact_counts.get(t.impact.name, 0) + 1
            )

        # Rule: HEALTHY — no high/critical impact
        if impact_counts.get("CRITICAL", 0) == 0 and \
           impact_counts.get("HIGH", 0) == 0 and \
           len(candidate_transitions) <= 2:
            return SituationType.HEALTHY

        # Rule: APPROVAL_BOTTLENECK — many low-impact changes
        if len(candidate_transitions) >= 3 and \
           impact_counts.get("CRITICAL", 0) == 0 and \
           impact_counts.get("HIGH", 0) == 0:
            return SituationType.APPROVAL_BOTTLENECK

        # Rule: RUNTIME_INSTABILITY — health/status changes
        health_count = type_counts.get("HEALTH_CHANGED", 0)
        status_count = type_counts.get("STATUS_CHANGED", 0)
        if health_count + status_count >= 2:
            return SituationType.RUNTIME_INSTABILITY

        # Rule: RESOURCE_PRESSURE — critical health changes
        if impact_counts.get("CRITICAL", 0) >= 1:
            return SituationType.RESOURCE_PRESSURE

        # Rule: RECOVERY — mix of added + stable transitions
        if type_counts.get("RUNTIME_ADDED", 0) >= 1 and \
           impact_counts.get("HIGH", 0) == 0:
            return SituationType.RECOVERY

        # Rule: CONFIGURATION_DRIFT — version changes
        if type_counts.get("VERSION_CHANGED", 0) >= 1 or \
           type_counts.get("REGISTRY_CHANGED", 0) >= 1:
            return SituationType.CONFIGURATION_DRIFT

        # Rule: BUSY — many transitions
        if len(candidate_transitions) >= 2:
            return SituationType.BUSY

        # Default
        return SituationType.UNKNOWN

    def _estimate_duration(
        self,
        candidate: SituationCandidate,
        all_transitions: List[RuntimeTransition],
    ) -> float:
        """Estimate duration from first to last transition timestamp."""
        trans_by_id = {t.transition_id: t for t in all_transitions}
        timestamps = [
            trans_by_id[tid].timestamp
            for tid in candidate.transition_ids
            if tid in trans_by_id
        ]
        if len(timestamps) < 2:
            return 0.0
        return max(timestamps) - min(timestamps)

    def _build_description(
        self,
        situation_type: SituationType,
        candidate: SituationCandidate,
    ) -> str:
        """Build a human-readable description."""
        descriptions = {
            SituationType.HEALTHY: "No significant transitions detected",
            SituationType.BUSY: f"High activity detected: {candidate.reason}",
            SituationType.APPROVAL_BOTTLENECK: "Multiple approval-related transitions",
            SituationType.EXECUTION_DELAY: "Execution delays detected",
            SituationType.RUNTIME_INSTABILITY: "Runtime health or status fluctuations",
            SituationType.RECOVERY: "Recovery in progress",
            SituationType.CONFIGURATION_DRIFT: "Configuration or version drift detected",
            SituationType.RESOURCE_PRESSURE: "Critical resource pressure detected",
            SituationType.UNKNOWN: "Unclassifiable transition pattern",
        }
        return descriptions.get(situation_type, "No description")
