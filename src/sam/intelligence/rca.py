"""
Root Cause Analyzer — Phase 1

Menganalisis akar penyebab insiden berdasarkan pattern matching,
log analysis, dan knowledge lookup.
"""

import structlog
from typing import List, Optional, Dict, Any
from .models import Incident, IncidentSeverity, RootCause

logger = structlog.get_logger()

# Pattern-based RCA rules
RCA_RULES = [
    {
        "keywords": ["worker", "timeout", "crash", "connection refused"],
        "cause": "Worker resource exhaustion or network connectivity failure",
        "confidence": 0.8,
        "recommendation": "Restart worker or check network connectivity",
    },
    {
        "keywords": ["provider", "auth", "credential", "authentication", "token"],
        "cause": "Provider authentication or credential failure",
        "confidence": 0.85,
        "recommendation": "Verify provider credentials and rotate if needed",
    },
    {
        "keywords": ["memory", "oom", "out of memory", "allocation"],
        "cause": "Memory exhaustion — system running out of available memory",
        "confidence": 0.9,
        "recommendation": "Increase memory allocation or reduce workload",
    },
    {
        "keywords": ["disk", "space", "storage", "i/o", "io error"],
        "cause": "Disk space or I/O issue",
        "confidence": 0.85,
        "recommendation": "Free up disk space or check disk health",
    },
    {
        "keywords": ["runtime", "exception", "internal error", "segfault"],
        "cause": "Runtime internal error — possible bug or corruption",
        "confidence": 0.65,
        "recommendation": "Check runtime logs and restart if needed",
    },
    {
        "keywords": ["gateway", "unreachable", "down", "not responding"],
        "cause": "Gateway is down or unreachable",
        "confidence": 0.9,
        "recommendation": "Verify gateway status and restart if necessary",
    },
    {
        "keywords": ["database", "db", "sql", "query", "connection pool"],
        "cause": "Database connectivity or query failure",
        "confidence": 0.8,
        "recommendation": "Check database health and connection pool",
    },
    {
        "keywords": ["plugin", "load", "init", "register"],
        "cause": "Plugin initialization or registration failure",
        "confidence": 0.7,
        "recommendation": "Check plugin manifest and dependencies",
    },
]


class RootCauseAnalyzer:
    """Analyzer akar penyebab — pattern-based + knowledge-augmented."""

    def __init__(self, knowledge_store=None):
        self.knowledge_store = knowledge_store

    async def analyze(self, incident: Incident) -> List[RootCause]:
        """Analisis akar penyebab insiden.

        Args:
            incident: Insiden yang akan dianalisis.

        Returns:
            List RootCause yang teridentifikasi, diurutkan oleh confidence.
        """
        causes = []

        # 1. Pattern-based analysis
        text = incident.title + " " + incident.description
        text_lower = text.lower()

        for rule in RCA_RULES:
            if any(keyword in text_lower for keyword in rule["keywords"]):
                causes.append(
                    RootCause(
                        incident_id=incident.id,
                        cause=rule["cause"],
                        confidence=rule["confidence"],
                        evidence=["Pattern matched: {0}".format(rule["keywords"])],
                        recommendation=rule["recommendation"],
                    )
                )

        # 2. Evidence-based analysis (dari log lines)
        for evidence in incident.evidence:
            msg = evidence.get("message", "") if isinstance(evidence, dict) else ""
            if isinstance(msg, str) and msg:
                for rule in RCA_RULES:
                    if any(kw in msg.lower() for kw in rule["keywords"]):
                        # Only add if not already captured
                        if not any(rule["cause"] in c.cause for c in causes):
                            causes.append(
                                RootCause(
                                    incident_id=incident.id,
                                    cause=rule["cause"],
                                    confidence=rule["confidence"] * 0.9,  # slightly lower for evidence-only
                                    evidence=["Log evidence: {0}".format(msg[:100])],
                                    recommendation=rule["recommendation"],
                                )
                            )

        # 3. Knowledge lookup
        if self.knowledge_store:
            try:
                knowledge_results = await self.knowledge_store.search(incident.title)
                for k in knowledge_results[:2]:
                    causes.append(
                        RootCause(
                            incident_id=incident.id,
                            cause=k.get("fact", "Knowledge-based cause"),
                            confidence=k.get("confidence", 0.5),
                            evidence=["Knowledge: {0}".format(k.get("id", "unknown"))],
                        )
                    )
            except Exception as e:
                logger.warning("knowledge_lookup_failed", error=str(e))

        # 4. Fallback jika tidak ada
        if not causes:
            causes.append(
                RootCause(
                    incident_id=incident.id,
                    cause="Unknown — insufficient pattern match",
                    confidence=0.3,
                    evidence=["No matching pattern found"],
                    recommendation="Gather more information and consult logs",
                )
            )

        # Sort by confidence descending
        causes.sort(key=lambda c: c.confidence, reverse=True)

        logger.info("rca_completed", incident_id=incident.id, causes=len(causes))
        return causes
