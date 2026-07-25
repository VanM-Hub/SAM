"""Pattern Engine for SAM Framework - rule-based pattern detection with optional persistence."""

import structlog
from typing import List, Optional, Any
from sam.patterns.models import PatternRule, PatternDetection, PatternSeverity
from sam.knowledge.models import KnowledgeFact

logger = structlog.get_logger()


class PatternEngine:
    """Rule-based pattern detection engine.

    Optionally persists detections via a repository implementing add(detection).
    """

    def __init__(self, repo: Optional[Any] = None) -> None:
        self._rules: List[PatternRule] = []
        self._detections: List[PatternDetection] = []
        self._repo = repo
        logger.debug("PatternEngine initialized", rules=0, detections=0, persistent=repo is not None)

    async def register_rule(self, rule: PatternRule) -> None:
        """Register a pattern rule for evaluation.

        Args:
            rule: The PatternRule to register.
        """
        self._rules.append(rule)
        logger.info(
            "Pattern rule registered",
            rule_id=rule.id,
            name=rule.name,
            severity=rule.severity.value,
            tags=rule.tags,
            min_confidence=rule.min_confidence,
            enabled=rule.enabled,
        )

    async def evaluate(self, facts: List[KnowledgeFact]) -> List[PatternDetection]:
        """Evaluate all enabled rules against the given facts.

        Args:
            facts: List of KnowledgeFact records to evaluate.

        Returns:
            List of PatternDetection events generated.
        """
        new_detections: List[PatternDetection] = []

        for rule in self._rules:
            if not rule.enabled:
                logger.debug("Skipping disabled rule", rule_id=rule.id)
                continue

            matching_facts = self._match_rule(rule, facts)
            if matching_facts:
                detection = PatternDetection(
                    rule_id=rule.id,
                    knowledge_fact_ids=[f.id for f in matching_facts],
                    severity=rule.severity,
                    message=f"Pattern detected: {rule.name} ({rule.condition})",
                    metadata={
                        "rule_name": rule.name,
                        "condition": rule.condition,
                        "matched_fact_count": len(matching_facts),
                    },
                )
                self._detections.append(detection)
                new_detections.append(detection)
                logger.info(
                    "Pattern detected",
                    detection_id=detection.id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=detection.severity.value,
                    fact_count=len(matching_facts),
                )
                # Persist detection if repository provided
                if self._repo is not None:
                    try:
                        # Try to extract correlation_id from detection metadata or from matched facts
                        correlation_id = detection.metadata.get('correlation_id') if isinstance(detection.metadata, dict) else None
                        if not correlation_id and matching_facts:
                            # Check first matching fact for correlation metadata
                            first_meta = getattr(matching_facts[0], 'metadata', {})
                            if isinstance(first_meta, dict):
                                correlation_id = first_meta.get('correlation_id')
                        await self._repo.add(detection, correlation_id=correlation_id)
                    except Exception:
                        logger.exception("Failed to persist pattern detection", detection_id=detection.id)
            else:
                logger.debug(
                    "Rule did not match",
                    rule_id=rule.id,
                    rule_name=rule.name,
                )

        return new_detections

    def _match_rule(self, rule: PatternRule, facts: List[KnowledgeFact]) -> List[KnowledgeFact]:
        """Check which facts match the rule conditions.

        A fact matches if:
        1. Its confidence >= rule.min_confidence
        2. It has at least one tag from rule.tags (if rule.tags is non-empty)

        Args:
            rule: The rule to match against.
            facts: List of facts to check.

        Returns:
            List of matching facts.
        """
        matches = []
        for fact in facts:
            if fact.confidence < rule.min_confidence:
                continue

            if rule.tags:
                # At least one tag must match
                if not any(tag in fact.tags for tag in rule.tags):
                    continue

            matches.append(fact)

        return matches

    async def get_detections(self, limit: int = 100) -> List[PatternDetection]:
        """Retrieve recent pattern detections.

        Args:
            limit: Maximum number of detections to return.

        Returns:
            List of PatternDetection events (most recent first).
        """
        sorted_detections = sorted(self._detections, key=lambda d: d.timestamp, reverse=True)
        return sorted_detections[:limit]

    async def clear(self) -> None:
        """Clear all stored detections and rules. Primarily for testing."""
        count = len(self._detections)
        rule_count = len(self._rules)
        self._detections.clear()
        self._rules.clear()
        logger.info("PatternEngine cleared", detections_removed=count, rules_removed=rule_count)