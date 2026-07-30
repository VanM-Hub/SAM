"""Activation Readiness — readiness untuk aktivasi spesifik."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str = ""
    name: str = ""
    passed: bool = False
    score: float = 0.0


class ActivationReadiness:
    """Readiness checker spesifik untuk aktivasi."""

    CHECKS = ["context_exists", "candidates_ready", "rules_ready",
              "validator_available", "registry_ready"]

    def check(self, context_exists: bool = True,
              candidates_ready: bool = True,
              rules_loaded: bool = True,
              validator_available: bool = True,
              registry_ready: bool = True) -> List[ReadinessCheck]:
        results = [
            ReadinessCheck("ctx", "Context Exists", context_exists, 1.0 if context_exists else 0.0),
            ReadinessCheck("cand", "Candidates Ready", candidates_ready, 1.0 if candidates_ready else 0.0),
            ReadinessCheck("rules", "Rules Loaded", rules_loaded, 1.0 if rules_loaded else 0.0),
            ReadinessCheck("val", "Validator Available", validator_available, 1.0 if validator_available else 0.0),
            ReadinessCheck("reg", "Registry Ready", registry_ready, 1.0 if registry_ready else 0.0),
        ]
        return results

    def overall(self, checks: List[ReadinessCheck]) -> float:
        if not checks:
            return 0.0
        return sum(c.score for c in checks) / len(checks)

    def all_checks(self) -> List[str]:
        return list(self.CHECKS)
