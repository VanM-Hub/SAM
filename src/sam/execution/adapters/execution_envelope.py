# OP-431 — Execution Envelope
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sam.execution.dispatch.dispatch_request import (
    DispatchRequest, DispatchTask, DispatchStatus, DispatchPriority,
)


@dataclass(frozen=True)
class ExecutionEnvelopeStatus:
    value: str = "pending"  # pending, building, validated, previewed, ready, completed, failed

    @staticmethod
    def pending() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("pending")

    @staticmethod
    def building() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("building")

    @staticmethod
    def validated() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("validated")

    @staticmethod
    def previewed() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("previewed")

    @staticmethod
    def ready() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("ready")

    @staticmethod
    def completed() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("completed")

    @staticmethod
    def failed() -> "ExecutionEnvelopeStatus":
        return ExecutionEnvelopeStatus("failed")

    def is_terminal(self) -> bool:
        return self.value in ("completed", "failed")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ExecutionEnvelopeMetadata:
    source: str = ""
    adapter_type: str = ""
    connector_type: str = ""
    dispatch_id: str = ""
    plan_id: str = ""
    package_id: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExecutionEnvelopeItem:
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    task_name: str = ""
    action: str = ""
    target: str = ""
    adapter_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_duration_seconds: int = 0
    requires_approval: bool = True


@dataclass(frozen=True)
class ExecutionEnvelope:
    envelope_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    items: Tuple[ExecutionEnvelopeItem, ...] = field(default_factory=tuple)
    metadata: Optional[ExecutionEnvelopeMetadata] = None
    status: ExecutionEnvelopeStatus = field(default_factory=ExecutionEnvelopeStatus.pending)
    total_items: int = 0
    requires_approval: bool = True
    estimated_duration_seconds: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def with_status(self, status: ExecutionEnvelopeStatus) -> "ExecutionEnvelope":
        return ExecutionEnvelope(
            envelope_id=self.envelope_id, items=self.items,
            metadata=self.metadata, status=status,
            total_items=self.total_items,
            requires_approval=self.requires_approval,
            estimated_duration_seconds=self.estimated_duration_seconds,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class ExecutionEnvelopeSummary:
    total_envelopes: int = 0
    pending: int = 0
    validated: int = 0
    previewed: int = 0
    ready: int = 0
    completed: int = 0
    failed: int = 0
    estimated_duration_seconds: int = 0


class ExecutionEnvelopeBuilder:
    """Builds ExecutionEnvelope from dispatch requests."""

    @staticmethod
    def build(
        dispatch: DispatchRequest,
        adapter_type: str = "mock",
    ) -> ExecutionEnvelope:
        items: List[ExecutionEnvelopeItem] = []
        total_duration = 0
        requires_approval = dispatch.requires_approval

        for dt in dispatch.tasks:
            item = ExecutionEnvelopeItem(
                task_id=dt.task_id,
                task_name=dt.name,
                action=dt.action,
                target=dt.target,
                adapter_type=adapter_type,
                estimated_duration_seconds=dt.estimated_duration_seconds,
                requires_approval=dt.status.value == "pending",
            )
            items.append(item)
            total_duration += dt.estimated_duration_seconds

        meta = dispatch.metadata
        env_meta = ExecutionEnvelopeMetadata(
            source=meta.source if meta else "",
            adapter_type=adapter_type,
            connector_type=meta.connector_type if meta else "",
            dispatch_id=dispatch.request_id,
        )

        return ExecutionEnvelope(
            items=tuple(items),
            metadata=env_meta,
            total_items=len(items),
            requires_approval=requires_approval,
            estimated_duration_seconds=total_duration,
        )
