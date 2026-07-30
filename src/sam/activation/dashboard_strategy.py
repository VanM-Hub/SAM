"""Dashboard Strategy Bridge — Sprint 84, 5 cards."""
from typing import Any, Dict, List
from dataclasses import dataclass, field
from sam.activation.activation_strategy import ActivationStrategyEngine
from sam.activation.activation_alternative import AlternativeGenerator
from sam.activation.activation_priority import ActivationPriority
from sam.activation.activation_window import ActivationWindowManager
from sam.activation.activation_sequence import SequenceBuilder
from sam.activation.activation_registry import ActivationRegistry


@dataclass(frozen=True)
class StrategyCard:
    card_type: str = ""
    title: str = ""
    items: List[str] = field(default_factory=list)


class DashboardStrategy:
    """Dashboard bridge untuk Strategy — 5 cards."""

    def __init__(self, registry: ActivationRegistry):
        self._registry = registry

    @property
    def card_count(self) -> int:
        return 5

    def get_cards(self, engine: ActivationStrategyEngine,
                  gen: AlternativeGenerator,
                  priority: ActivationPriority,
                  wm: ActivationWindowManager,
                  seq_builder: SequenceBuilder,
                  env: str) -> List[StrategyCard]:
        return [
            self._strategy_card(engine, env),
            self._alternatives_card(gen, env),
            self._priority_card(priority),
            self._window_card(wm, env),
            self._sequence_card(seq_builder, engine, priority, env),
        ]

    def _strategy_card(self, engine: ActivationStrategyEngine,
                       env: str) -> StrategyCard:
        cands = self._registry.list_candidates()
        cnt = len(cands)
        conf_avg = sum(c.confidence for c in cands) / cnt if cnt > 0 else 0.0
        s = engine.select(env, cnt, conf_avg)
        return StrategyCard(
            "strategy", "Selected Strategy",
            [f"Name: {s.name}", f"Mode: {s.mode}",
             f"Confidence: {s.confidence}", f"ID: {s.strategy_id}"],
        )

    def _alternatives_card(self, gen: AlternativeGenerator,
                           env: str) -> StrategyCard:
        alts = gen.generate(env, self._registry.list_candidates())
        return StrategyCard(
            "alternatives", "Alternatives",
            [f"{a.name}: viability={a.viability:.2f}, risk={a.risk_score:.2f}"
             for a in alts],
        )

    def _priority_card(self, priority: ActivationPriority) -> StrategyCard:
        assign = priority.assign(self._registry.list_candidates())
        return StrategyCard(
            "priority", "Priority Assignments",
            [f"#{a.priority} {a.candidate_id}: {a.reason}" for a in assign],
        )

    def _window_card(self, wm: ActivationWindowManager,
                     env: str) -> StrategyCard:
        w = wm.create(env, 60.0, 1000.0)
        return StrategyCard(
            "window", "Activation Window",
            [f"ID: {w.window_id}", f"Duration: {w.duration}",
             f"Urgency: {w.urgency}", f"End: {w.end}"],
        )

    def _sequence_card(self, builder: SequenceBuilder,
                       engine: ActivationStrategyEngine,
                       priority: ActivationPriority,
                       env: str) -> StrategyCard:
        cands = self._registry.list_candidates()
        cnt = len(cands)
        conf_avg = sum(c.confidence for c in cands) / cnt if cnt > 0 else 0.0
        strat = engine.select(env, cnt, conf_avg)
        assign = priority.assign(cands)
        seq = builder.build(strat, assign, cands)
        return StrategyCard(
            "sequence", "Activation Sequence",
            [f"Steps: {seq.total_steps}", f"Duration: {seq.duration_estimate:.0f}s",
             f"Strategy: {strat.name}"] +
            [f"  Step {s.order}: {s.candidate_ref} ({s.status})" for s in seq.steps],
        )
