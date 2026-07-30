"""Activation Alternative — alternatif strategi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivationAlternative:
    alt_id: str = ""
    name: str = ""
    strategy_ref: str = ""
    candidate_count: int = 0
    estimated_duration: float = 0.0
    risk_score: float = 0.0
    viability: float = 0.0


class AlternativeGenerator:
    """Menghasilkan alternatif aktivasi."""

    def generate(self, env: str, candidates: List[Any],
                 strategy: Any = None) -> List[ActivationAlternative]:
        alts: List[ActivationAlternative] = []
        env_risk = {"normal": 0.2, "busy": 0.4, "idle": 0.3, "emergency": 0.8}
        risk_base = env_risk.get(env, 0.5)

        alts.append(ActivationAlternative(
            "alt_direct", "Direct Route", "direct",
            len(candidates), 10.0, risk_base * 0.5, 1.0 - risk_base * 0.3
        ))
        alts.append(ActivationAlternative(
            "alt_safe", "Safe Route", "staged",
            len(candidates), 30.0, risk_base * 0.3, 1.0 - risk_base * 0.1
        ))
        alts.append(ActivationAlternative(
            "alt_parallel", "Fast Route", "parallel",
            len(candidates), 5.0, risk_base * 0.8, 1.0 - risk_base * 0.6
        ))

        if env == "emergency":
            alts.append(ActivationAlternative(
                "alt_emergency", "Emergency Override", "direct",
                len(candidates), 2.0, risk_base * 0.9, 0.95
            ))

        return alts

    def best(self, alternatives: List[ActivationAlternative]) -> Optional[ActivationAlternative]:
        if not alternatives:
            return None
        return max(alternatives, key=lambda a: a.viability * (1 - a.risk_score))


# Type alias for forward ref workaround
ActivationAny = Any
