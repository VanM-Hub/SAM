"""Activation Strategy — pemilihan strategi aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivationStrategy:
    strategy_id: str = ""
    name: str = ""
    mode: str = "sequential"  # sequential, parallel, conditional, fallback
    confidence: float = 0.0
    description: str = ""


class ActivationStrategyEngine:
    """Menentukan strategi aktivasi berdasarkan konteks."""

    STRATEGIES = {
        "direct": ActivationStrategy("direct", "Direct Activation", "sequential", 0.95, "Aktivasi langsung"),
        "staged": ActivationStrategy("staged", "Staged Activation", "sequential", 0.80, "Bertahap"),
        "parallel": ActivationStrategy("parallel", "Parallel Activation", "parallel", 0.70, "Paralel"),
        "conditional": ActivationStrategy("conditional", "Conditional Activation", "conditional", 0.60, "Bersyarat"),
        "fallback": ActivationStrategy("fallback", "Fallback Activation", "fallback", 0.50, "Cadangan"),
    }

    def select(self, env: str, candidate_count: int,
               confidence_avg: float) -> ActivationStrategy:
        if env == "emergency":
            return self.STRATEGIES["direct"]
        elif env == "busy" and candidate_count <= 3:
            return self.STRATEGIES["parallel"]
        elif env == "idle":
            return self.STRATEGIES["fallback"]
        elif candidate_count > 5:
            return self.STRATEGIES["staged"]
        elif confidence_avg >= 0.7:
            return self.STRATEGIES["direct"]
        else:
            return self.STRATEGIES["conditional"]

    def list_strategies(self) -> List[ActivationStrategy]:
        return list(self.STRATEGIES.values())

    def get_strategy(self, sid: str) -> Optional[ActivationStrategy]:
        return self.STRATEGIES.get(sid)
