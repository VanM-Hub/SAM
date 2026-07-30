"""Execution Builder — 5 tipe kandidat eksekusi."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.execution_candidate import ExecutionCandidate


class ExecutionBuilder:
    """Builder untuk membuat execution candidate.

    5 tipe kandidat:
      1. immediate — eksekusi langsung
      2. scheduled — terjadwal
      3. conditional — bersyarat
      4. batch — batch processing
      5. pipeline — pipeline processing
    """

    def build_immediate(
        self,
        candidate_id: str,
        context_id: str,
        request_id: str,
        timestamp: float,
        name: str = "",
        description: str = "",
        estimated_effort: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCandidate:
        """Buat kandidat immediate — eksekusi langsung saat siap."""
        return ExecutionCandidate(
            candidate_id=candidate_id,
            context_id=context_id,
            request_id=request_id,
            timestamp=timestamp,
            name=name or f"immediate_{candidate_id}",
            description=description or "Execute immediately when ready",
            candidate_type="immediate",
            estimated_effort=estimated_effort,
            tags=tags or ["immediate"],
            metadata=metadata or {"type": "immediate"},
        )

    def build_scheduled(
        self,
        candidate_id: str,
        context_id: str,
        request_id: str,
        timestamp: float,
        schedule_time: float = 0.0,
        name: str = "",
        description: str = "",
        estimated_effort: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCandidate:
        """Buat kandidat scheduled — eksekusi terjadwal."""
        meta = metadata or {}
        meta["type"] = "scheduled"
        meta["schedule_time"] = schedule_time
        return ExecutionCandidate(
            candidate_id=candidate_id,
            context_id=context_id,
            request_id=request_id,
            timestamp=timestamp,
            name=name or f"scheduled_{candidate_id}",
            description=description or f"Execute at scheduled time {schedule_time}",
            candidate_type="scheduled",
            estimated_effort=estimated_effort,
            tags=tags or ["scheduled"],
            metadata=meta,
        )

    def build_conditional(
        self,
        candidate_id: str,
        context_id: str,
        request_id: str,
        timestamp: float,
        condition: str = "always",
        name: str = "",
        description: str = "",
        estimated_effort: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCandidate:
        """Buat kandidat conditional — eksekusi jika kondisi terpenuhi."""
        meta = metadata or {}
        meta["type"] = "conditional"
        meta["condition"] = condition
        return ExecutionCandidate(
            candidate_id=candidate_id,
            context_id=context_id,
            request_id=request_id,
            timestamp=timestamp,
            name=name or f"conditional_{candidate_id}",
            description=description or f"Execute when condition '{condition}' is met",
            candidate_type="conditional",
            estimated_effort=estimated_effort,
            tags=tags or ["conditional"],
            metadata=meta,
        )

    def build_batch(
        self,
        candidate_id: str,
        context_id: str,
        request_id: str,
        timestamp: float,
        batch_size: int = 1,
        name: str = "",
        description: str = "",
        estimated_effort: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCandidate:
        """Buat kandidat batch — batch processing multiple items."""
        meta = metadata or {}
        meta["type"] = "batch"
        meta["batch_size"] = batch_size
        return ExecutionCandidate(
            candidate_id=candidate_id,
            context_id=context_id,
            request_id=request_id,
            timestamp=timestamp,
            name=name or f"batch_{candidate_id}",
            description=description or f"Batch process {batch_size} items",
            candidate_type="batch",
            estimated_effort=estimated_effort,
            tags=tags or ["batch"],
            metadata=meta,
        )

    def build_pipeline(
        self,
        candidate_id: str,
        context_id: str,
        request_id: str,
        timestamp: float,
        steps: int = 1,
        name: str = "",
        description: str = "",
        estimated_effort: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionCandidate:
        """Buat kandidat pipeline — pipeline processing multi-step."""
        meta = metadata or {}
        meta["type"] = "pipeline"
        meta["steps"] = steps
        return ExecutionCandidate(
            candidate_id=candidate_id,
            context_id=context_id,
            request_id=request_id,
            timestamp=timestamp,
            name=name or f"pipeline_{candidate_id}",
            description=description or f"Pipeline process with {steps} steps",
            candidate_type="pipeline",
            estimated_effort=estimated_effort,
            tags=tags or ["pipeline"],
            metadata=meta,
        )
