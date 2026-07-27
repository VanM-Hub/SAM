"""
Analyzer Engine — Phase 0

Menganalisis observasi, mendeteksi drift terhadap DOS.
"""

import structlog
from typing import Dict, Any, List
from ..contracts import DesiredOperationalState

logger = structlog.get_logger()


class AnalyzerEngine:
    """Analyzer Engine — deteksi drift antara observasi dan DOS."""

    def __init__(self, dos: DesiredOperationalState):
        self.dos = dos

    async def analyze(self, observation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Deteksi drift antara kondisi aktual (observation) dan DOS.

        Args:
            observation: Dict hasil observe().

        Returns:
            List of drift dicts. Kosong jika tidak ada drift.
        """
        drifts = []

        # Cek runtime state
        obs_state = observation.get("runtime_state", "unknown")
        if obs_state != self.dos.runtime_state.lower():
            drifts.append({
                "type": "runtime_state",
                "expected": self.dos.runtime_state,
                "actual": obs_state,
                "severity": "critical",
            })

        # Cek plugins count
        plugins_loaded = observation.get("plugins", {}).get("loaded", 0)
        if plugins_loaded < self.dos.plugins_expected:
            drifts.append({
                "type": "plugins",
                "expected": self.dos.plugins_expected,
                "actual": plugins_loaded,
                "severity": "moderate",
            })

        # Cek knowledge
        if not observation.get("knowledge", {}).get("loaded", False):
            drifts.append({
                "type": "knowledge",
                "expected": True,
                "actual": False,
                "severity": "critical",
            })

        # Cek memory
        if not observation.get("memory", {}).get("healthy", False):
            drifts.append({
                "type": "memory",
                "expected": True,
                "actual": False,
                "severity": "critical",
            })

        # Cek health score
        health_score = observation.get("health_score", 0)
        if health_score < self.dos.min_health_score:
            drifts.append({
                "type": "health",
                "expected": self.dos.min_health_score,
                "actual": health_score,
                "severity": "moderate",
            })

        if drifts:
            logger.warning("drifts_detected", count=len(drifts), drifts=drifts)
        else:
            logger.info("no_drift_detected")

        return drifts
