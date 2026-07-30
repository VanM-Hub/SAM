"""
Guardian Impact Analyzer.

Analyzes the impact of runtime transitions.
All rule-based. No AI, no machine learning.
Synchronous only.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from .transition import RuntimeTransition, TransitionType, ImpactLevel


class ImpactAnalyzer:
    """
    Rule-based impact analyzer for runtime transitions.

    Categorizes impact as:
        LOW
        MEDIUM
        HIGH
        CRITICAL

    Rules are based on transition type, frequency, and
    relationship between runtimes.
    """

    def analyze_transition(self, transition: RuntimeTransition) -> ImpactLevel:
        """
        Analyze the impact of a single transition.

        Args:
            transition: The transition to analyze.

        Returns:
            ImpactLevel for this transition.
        """
        # CRITICAL: health critical
        if transition.transition_type == TransitionType.HEALTH_CHANGED:
            details = transition.details or {}
            field_change = details.get("field_change", {})
            to_val = field_change.get("to", "")
            if to_val == "CRITICAL":
                return ImpactLevel.CRITICAL
            if to_val == "DEGRADED":
                return ImpactLevel.HIGH

        # HIGH: runtime removed, status error
        if transition.transition_type == TransitionType.RUNTIME_REMOVED:
            return ImpactLevel.HIGH

        if transition.transition_type == TransitionType.STATUS_CHANGED:
            details = transition.details or {}
            field_change = details.get("field_change", {})
            to_val = field_change.get("to", "")
            if to_val in ("ERROR", "STOPPED"):
                return ImpactLevel.HIGH

        # MEDIUM: version changes, status recovery, sync failures
        if transition.transition_type in (
            TransitionType.VERSION_CHANGED,
            TransitionType.REGISTRY_CHANGED,
            TransitionType.SYNC_FAILED,
        ):
            return ImpactLevel.MEDIUM

        # LOW: additions, status improvement
        if transition.transition_type in (
            TransitionType.RUNTIME_ADDED,
            TransitionType.SYNC_STARTED,
            TransitionType.SYNC_COMPLETED,
        ):
            return ImpactLevel.LOW

        return ImpactLevel.LOW

    def analyze_batch(
        self,
        transitions: List[RuntimeTransition],
    ) -> Dict[str, Any]:
        """
        Analyze a batch of transitions.

        Args:
            transitions: List of transitions to analyze.

        Returns:
            Dict with batch analysis results.
        """
        if not transitions:
            return {
                "has_critical": False,
                "has_high": False,
                "total": 0,
                "max_impact": "NONE",
                "impact_summary": {},
                "recommendations": [],
            }

        impact_counts: Dict[str, int] = defaultdict(int)
        max_impact = ImpactLevel.LOW
        recommendations: List[str] = []

        for t in transitions:
            impact = self.analyze_transition(t)

            # Update impact for each transition
            transitions_list = list(transitions)
            idx = transitions_list.index(t)
            # We can't modify frozen DTO, so just track in impact_counts
            impact_counts[impact.name] += 1

            if impact.value > max_impact.value:
                max_impact = impact

        # Generate rule-based recommendations
        if impact_counts.get("CRITICAL", 0) > 0:
            recommendations.append(
                f"CRITICAL: {impact_counts['CRITICAL']} transition(s) "
                "require immediate attention"
            )
        if impact_counts.get("HIGH", 0) > 0:
            recommendations.append(
                f"HIGH: {impact_counts['HIGH']} transition(s) "
                "should be reviewed"
            )
        if impact_counts.get("MEDIUM", 0) > 0:
            recommendations.append(
                f"MEDIUM: {impact_counts['MEDIUM']} transition(s) "
                "may require attention"
            )

        health_transitions = [
            t for t in transitions
            if t.transition_type == TransitionType.HEALTH_CHANGED
        ]
        if len(health_transitions) > 2:
            recommendations.append(
                f"Multiple health transitions ({len(health_transitions)}) "
                "detected — possible instability"
            )

        return {
            "has_critical": impact_counts.get("CRITICAL", 0) > 0,
            "has_high": impact_counts.get("HIGH", 0) > 0,
            "total": len(transitions),
            "max_impact": max_impact.name,
            "impact_summary": dict(impact_counts),
            "recommendations": recommendations,
        }

    def get_impact_priority(self, impact: ImpactLevel) -> int:
        """
        Get numerical priority for an impact level.

        Args:
            impact: The impact level.

        Returns:
            Priority number (lower = more urgent).
        """
        mapping = {
            ImpactLevel.CRITICAL: 0,
            ImpactLevel.HIGH: 1,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 3,
        }
        return mapping.get(impact, 99)
