"""Conversation Execution Bridge — 10 queries read-only."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_registry import ExecutionRegistry
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate


class ConversationExecution:
    """Conversation bridge untuk execution runtime — 10 queries read-only."""

    def __init__(self, registry: ExecutionRegistry) -> None:
        self._registry = registry

    def get_execution_context(self, context_id: str) -> Optional[ExecutionContext]:
        """Query 1: Ambil execution context by ID."""
        return self._registry.get_context(context_id)

    def get_execution_request(self, request_id: str) -> Optional[ExecutionRequest]:
        """Query 2: Ambil execution request by ID."""
        return self._registry.get_request(request_id)

    def get_execution_candidate(self, candidate_id: str) -> Optional[ExecutionCandidate]:
        """Query 3: Ambil execution candidate by ID."""
        return self._registry.get_candidate(candidate_id)

    def list_all_contexts(self) -> List[ExecutionContext]:
        """Query 4: Daftar semua execution context."""
        return self._registry.list_contexts()

    def list_all_requests(self) -> List[ExecutionRequest]:
        """Query 5: Daftar semua execution request."""
        return self._registry.list_requests()

    def list_all_candidates(self) -> List[ExecutionCandidate]:
        """Query 6: Daftar semua execution candidate."""
        return self._registry.list_candidates()

    def count_contexts(self) -> int:
        """Query 7: Hitung jumlah execution context."""
        return len(self._registry.list_contexts())

    def count_requests(self) -> int:
        """Query 8: Hitung jumlah execution request."""
        return len(self._registry.list_requests())

    def count_candidates(self) -> int:
        """Query 9: Hitung jumlah execution candidate."""
        return len(self._registry.list_candidates())

    def get_registry_snapshot(self) -> Any:
        """Query 10: Ambil snapshot registry."""
        return self._registry.snapshot()
