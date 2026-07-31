"""Provider Pipeline (Sprint 253).

Program C - Real Execution Runtime.
Pipeline dispatch: seleksi -> dispatch -> history -> summary.
Semua generik (tidak provider-specific), no network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .execution_request import ExecutionRequest
from .provider_dispatcher import ProviderDispatcher, DispatchTarget
from .provider_selector import ProviderSelector, SelectorRanking
from .provider_history import ProviderHistory, ProviderHistoryEntry
from .provider_summary import ProviderSummary, ProviderSummaryData


@dataclass(frozen=True)
class ProviderPipelineResult:
    """Hasil pipeline dispatch (immutable)."""
    pipeline_id: str
    execution_id: str
    target: DispatchTarget = field(default_factory=lambda: DispatchTarget("openai", "", "preview"))
    history: ProviderHistoryEntry = field(default_factory=lambda: ProviderHistoryEntry("x", "x", "x"))
    ranking: tuple = field(default_factory=tuple)
    summary: tuple = field(default_factory=tuple)
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "execution_id": self.execution_id,
            "ranking": [r.as_dict() for r in self.ranking],
            "target": self.target.as_dict(),
            "history": self.history.as_dict(),
            "summary": [s.as_dict() for s in self.summary],
            "external_calls": self.external_calls,
        }


class ProviderPipeline:
    """Pipeline dispatch provider. Generik, read-only."""

    def __init__(self, dispatcher: ProviderDispatcher | None = None,
                 selector: ProviderSelector | None = None,
                 history: ProviderHistory | None = None,
                 summary: ProviderSummary | None = None) -> None:
        self._dispatcher = dispatcher or ProviderDispatcher()
        self._selector = selector or ProviderSelector()
        self._history = history or ProviderHistory()
        self._summary = summary or ProviderSummary()

    @property
    def dispatcher(self) -> ProviderDispatcher:
        return self._dispatcher

    def run(self, pipeline_id: str, request: ExecutionRequest) -> ProviderPipelineResult:
        ranking = self._selector.rank(request)
        target = self._dispatcher.dispatch(request)
        history_entry = self._history.record(target)
        summary = self._summary.summarize(self._history.all())
        return ProviderPipelineResult(
            pipeline_id=pipeline_id,
            execution_id=request.execution_id,
            ranking=tuple(ranking),
            target=target,
            history=history_entry,
            summary=tuple(summary),
            external_calls=0,
        )
