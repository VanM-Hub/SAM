"""
Recommender — Phase 1

Memberikan rekomendasi perbaikan berdasarkan insiden dan RCA.
"""

import structlog
import uuid
from typing import List, Optional
from .models import Incident, Recommendation, RootCause

logger = structlog.get_logger()


class Recommender:
    """Recommender — menghasilkan rekomendasi pemulihan dengan confidence score."""

    # Template steps berdasarkan tipe rekomendasi
    STEP_TEMPLATES = {
        "restart": [
            "Identify affected component",
            "Graceful stop of component",
            "Verify component has stopped",
            "Start component",
            "Verify health after restart",
        ],
        "verify": [
            "Collect evidence and logs",
            "Verify configuration file",
            "Test connectivity to dependencies",
            "Report findings",
        ],
        "investigate": [
            "Review recent log entries",
            "Collect diagnostic information",
            "Consult knowledge base",
            "Take corrective action",
        ],
        "recover": [
            "Execute recovery workflow",
            "Verify data integrity",
            "Validate system state",
            "Confirm resolution",
        ],
    }

    async def recommend(
        self,
        incident: Incident,
        causes: List[RootCause],
    ) -> List[Recommendation]:
        """Buat rekomendasi berdasarkan insiden dan RCA.

        Args:
            incident: Insiden yang direkomendasikan.
            causes: Root causes hasil RCA.

        Returns:
            List Recommendation diurutkan oleh confidence.
        """
        recommendations = []

        for cause in causes:
            if not cause.cause:
                continue

            # Determine step template
            template = self._select_template(cause)
            steps = list(self.STEP_TEMPLATES.get(template, self.STEP_TEMPLATES["investigate"]))

            # Rekomendasi spesifik jika ada
            if cause.recommendation:
                # Tambahkan sebagai step pertama
                steps.insert(0, cause.recommendation)

            rec = Recommendation(
                incident_id=incident.id,
                title="Recover from: {0}".format(self._summarize(cause.cause, 50)),
                description="Root cause: {0}".format(cause.cause),
                confidence=cause.confidence * 0.9,  # discount untuk safety
                risk=self._determine_risk(incident.severity),
                steps=steps,
            )
            recommendations.append(rec)

        # Fallback jika tidak ada
        if not recommendations:
            recommendations.append(
                Recommendation(
                    incident_id=incident.id,
                    title="General recovery: restart affected component",
                    description="No specific root cause identified. Consider restarting.",
                    confidence=0.4,
                    risk="medium",
                    steps=self.STEP_TEMPLATES["restart"],
                )
            )

        # Sort by confidence descending
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        logger.info(
            "recommendation_generated",
            incident_id=incident.id,
            count=len(recommendations),
        )
        return recommendations

    def _select_template(self, cause: RootCause) -> str:
        """Pilih template langkah berdasarkan rekomendasi."""
        rec = (cause.recommendation or "").lower()
        cause_lower = cause.cause.lower()

        if "restart" in rec or "restart" in cause_lower:
            return "restart"
        if "check" in rec or "verify" in rec or "check" in cause_lower:
            return "verify"
        if "recover" in rec or "recovery" in cause_lower:
            return "recover"
        return "investigate"

    def _determine_risk(self, severity) -> str:
        """Tentukan level risk berdasarkan severity."""
        if severity.value in ("critical", "high"):
            return "high"
        elif severity.value == "medium":
            return "medium"
        return "low"

    def _summarize(self, text: str, max_len: int = 50) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len].rsplit(" ", 1)[0] + "..."
