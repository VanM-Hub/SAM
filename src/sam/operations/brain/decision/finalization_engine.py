"""
Finalization Engine.

Assembles all pipeline outputs into an immutable FinalDecisionRecord.
Does NOT execute approval. Preview only.
"""

import uuid
from datetime import datetime
from typing import Optional
from .finalization import FinalDecisionRecord, FinalDecisionState, FinalDecisionMetadata, FinalDecisionStatistics, FinalDecisionSnapshot
from .finalization_summary import FinalizationSummary
from .finalization_history import FinalizationHistory
from .approval_certification import ApprovalCertification
from .approval_activation import ApprovalActivation


class FinalizationEngine:
    def __init__(self) -> None:
        self._records: list = []
        self._history = FinalizationHistory()

    def finalize(self, certification: Optional[ApprovalCertification] = None,
                 activation: Optional[ApprovalActivation] = None,
                 session_id: str = "", lifecycle_id: str = "",
                 gateway_request_id: str = "") -> FinalDecisionRecord:
        summary = FinalizationSummary.build(certification, activation)
        integrity = FinalizationSummary.compute_integrity(certification, activation)
        complete = FinalizationSummary.compute_complete(certification, activation)
        rid = str(uuid.uuid4())

        record = FinalDecisionRecord(
            record_id=rid, timestamp=datetime.now().timestamp(),
            state=FinalDecisionState.FINALIZED if complete else FinalDecisionState.PENDING,
            session_id=session_id, lifecycle_id=lifecycle_id,
            activation_id=activation.activation_id if activation else "",
            certification_id=certification.certification_id if certification else "",
            gateway_request_id=gateway_request_id,
            summary=summary,
            metadata=FinalDecisionMetadata(record_id=rid, created_at=datetime.now().timestamp()),
            pipeline_integrity=integrity,
            complete=complete,
        )
        self._records.append(record)
        self._history.record(rid, "finalized" if complete else "pending", record.state.name, integrity)
        return record

    def latest(self) -> Optional[FinalDecisionRecord]:
        return self._records[-1] if self._records else None

    @property
    def count(self) -> int: return len(self._records)
    @property
    def history(self) -> FinalizationHistory: return self._history

    def get_statistics(self) -> FinalDecisionStatistics:
        counts = {"pending":0,"finalized":0,"completed":0,"invalidated":0,"archived":0,"reopened":0}
        for r in self._records:
            n = r.state.name.lower()
            if n in counts: counts[n] += 1
        return FinalDecisionStatistics(total=self.count, **counts)

    def create_snapshot(self) -> FinalDecisionSnapshot:
        return FinalDecisionSnapshot(
            snapshot_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
            records=list(self._records[-20:]),
            statistics=self.get_statistics()
        )
