"""Conversation Strategy Bridge — Sprint 84, 8 queries."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_strategy import ActivationStrategyEngine, ActivationStrategy
from sam.activation.activation_alternative import AlternativeGenerator, ActivationAlternative
from sam.activation.activation_priority import ActivationPriority, PriorityAssignment
from sam.activation.activation_window import ActivationWindowManager, ActivationWindow
from sam.activation.activation_sequence import SequenceBuilder, ActivationSequence
from sam.activation.activation_registry import ActivationRegistry


class ConversationStrategy:
    """Conversation bridge untuk Strategy module — 8 queries."""

    def __init__(self, registry: ActivationRegistry):
        self._registry = registry

    @property
    def query_count(self) -> int:
        return 8

    def query_strategies(self, engine: ActivationStrategyEngine) -> List[Dict[str, Any]]:
        return [
            {"id": s.strategy_id, "name": s.name, "mode": s.mode, "confidence": s.confidence}
            for s in engine.list_strategies()
        ]

    def query_selected_strategy(self, engine: ActivationStrategyEngine,
                                 env: str) -> Dict[str, Any]:
        cnt = self._registry.candidate_count
        candidates = self._registry.list_candidates()
        conf_avg = sum(c.confidence for c in candidates) / cnt if cnt > 0 else 0.0
        s = engine.select(env, cnt, conf_avg)
        return {"strategy_id": s.strategy_id, "name": s.name, "mode": s.mode, "confidence": s.confidence}

    def query_alternatives(self, gen: AlternativeGenerator, env: str) -> List[Dict[str, Any]]:
        alts = gen.generate(env, self._registry.list_candidates())
        return [
            {"id": a.alt_id, "name": a.name, "viability": a.viability, "risk": a.risk_score}
            for a in alts
        ]

    def query_best_alternative(self, gen: AlternativeGenerator, env: str) -> Dict[str, Any]:
        alts = gen.generate(env, self._registry.list_candidates())
        best = gen.best(alts)
        if best:
            return {"id": best.alt_id, "name": best.name, "viability": best.viability}
        return {}

    def query_priorities(self, priority: ActivationPriority) -> List[Dict[str, Any]]:
        assign = priority.assign(self._registry.list_candidates())
        return [
            {"candidate": a.candidate_id, "priority": a.priority, "reason": a.reason}
            for a in assign
        ]

    def query_window(self, wm: ActivationWindowManager, env: str, dur: float = 60.0,
                     ts: float = 0.0) -> Dict[str, Any]:
        w = wm.create(env, dur, ts)
        return {"window_id": w.window_id, "duration": w.duration,
                "urgency": w.urgency, "end": w.end}

    def query_sequence(self, builder: SequenceBuilder, engine: ActivationStrategyEngine,
                        priority: ActivationPriority, env: str) -> Dict[str, Any]:
        cands = self._registry.list_candidates()
        cnt = len(cands)
        conf_avg = sum(c.confidence for c in cands) / cnt if cnt > 0 else 0.0
        strat = engine.select(env, cnt, conf_avg)
        assign = priority.assign(cands)
        seq = builder.build(strat, assign, cands)
        return {"sequence_id": seq.sequence_id, "total_steps": seq.total_steps,
                "duration_estimate": seq.duration_estimate,
                "strategy": strat.name}

    def query_all_strategy_infos(self, engine: ActivationStrategyEngine,
                                  gen: AlternativeGenerator,
                                  priority: ActivationPriority,
                                  env: str) -> Dict[str, Any]:
        cands = self._registry.list_candidates()
        cnt = len(cands)
        conf_avg = sum(c.confidence for c in cands) / cnt if cnt > 0 else 0.0
        strat = engine.select(env, cnt, conf_avg)
        alts = gen.generate(env, cands)
        assign = priority.assign(cands)
        return {
            "strategy": strat.name,
            "alternatives": len(alts),
            "priorities": len(assign),
            "best_alt": gen.best(alts).alt_id if gen.best(alts) else "",
        }
