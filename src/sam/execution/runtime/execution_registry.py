"""Execution Registry — registry context, request, candidate."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate


@dataclass(frozen=True)
class ExecutionSnapshot:
    """Snapshot registry pada satu titik waktu."""
    context_ids: Tuple[str, ...]
    request_ids: Tuple[str, ...]
    candidate_ids: Tuple[str, ...]
    context_count: int
    request_count: int
    candidate_count: int


class ExecutionRegistry:
    """Registry untuk execution context, request, dan candidate.

    Registry adalah penyimpanan in-memory yang menyediakan CRUD.
    Semua data immutable — registry hanya menyimpan referensi.
    """

    def __init__(self) -> None:
        self._contexts: Dict[str, ExecutionContext] = {}
        self._requests: Dict[str, ExecutionRequest] = {}
        self._candidates: Dict[str, ExecutionCandidate] = {}

    # --- Context ---

    def register_context(self, context: ExecutionContext) -> None:
        """Daftarkan execution context baru."""
        self._contexts[context.context_id] = context

    def get_context(self, context_id: str) -> Optional[ExecutionContext]:
        """Ambil execution context berdasarkan ID."""
        return self._contexts.get(context_id)

    def list_contexts(self) -> List[ExecutionContext]:
        """Daftar semua execution context."""
        return list(self._contexts.values())

    def clear_contexts(self) -> None:
        """Hapus semua execution context."""
        self._contexts.clear()

    # --- Request ---

    def register_request(self, request: ExecutionRequest) -> None:
        """Daftarkan execution request baru."""
        self._requests[request.request_id] = request

    def get_request(self, request_id: str) -> Optional[ExecutionRequest]:
        """Ambil execution request berdasarkan ID."""
        return self._requests.get(request_id)

    def list_requests(self) -> List[ExecutionRequest]:
        """Daftar semua execution request."""
        return list(self._requests.values())

    def clear_requests(self) -> None:
        """Hapus semua execution request."""
        self._requests.clear()

    # --- Candidate ---

    def register_candidate(self, candidate: ExecutionCandidate) -> None:
        """Daftarkan execution candidate baru."""
        self._candidates[candidate.candidate_id] = candidate

    def get_candidate(self, candidate_id: str) -> Optional[ExecutionCandidate]:
        """Ambil execution candidate berdasarkan ID."""
        return self._candidates.get(candidate_id)

    def list_candidates(self) -> List[ExecutionCandidate]:
        """Daftar semua execution candidate."""
        return list(self._candidates.values())

    def clear_candidates(self) -> None:
        """Hapus semua execution candidate."""
        self._candidates.clear()

    # --- Snapshot ---

    def snapshot(self) -> ExecutionSnapshot:
        """Ambil snapshot registry saat ini."""
        return ExecutionSnapshot(
            context_ids=tuple(self._contexts.keys()),
            request_ids=tuple(self._requests.keys()),
            candidate_ids=tuple(self._candidates.keys()),
            context_count=len(self._contexts),
            request_count=len(self._requests),
            candidate_count=len(self._candidates),
        )

    # --- Utility ---

    def clear_all(self) -> None:
        """Hapus semua data di registry."""
        self._contexts.clear()
        self._requests.clear()
        self._candidates.clear()

    @property
    def is_empty(self) -> bool:
        """Cek apakah registry kosong."""
        return not (self._contexts or self._requests or self._candidates)

    @property
    def total_items(self) -> int:
        """Total item di registry."""
        return len(self._contexts) + len(self._requests) + len(self._candidates)
