"""Audit Pipeline — pipeline preview audit (Sprint 215).

Pipeline: Descriptor → Audit Record → Builder → Preview
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.audit_registry import AuditRegistry
from ..foundation.audit_descriptor import AuditDescriptor
from ..model.audit_record import AuditRecord


@dataclass(frozen=True)
class AuditStage:
    """Satu tahap pipeline immutable."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class AuditPipelineRun:
    """Hasil pipeline immutable."""
    ok: bool = False
    audit_id: str = ""
    stages: List[AuditStage] = field(default_factory=list)
    external_calls: int = 0


class AuditPipeline:
    """Pipeline preview audit. Read-only, tanpa storage."""

    def run(self, registry: AuditRegistry, audit_id: str) -> AuditPipelineRun:
        audit = registry.get(audit_id)
        stages = [
            AuditStage("descriptor", audit is not None,
                       "found" if audit else "not_found"),
        ]
        if audit is None:
            return AuditPipelineRun(
                ok=False, audit_id=audit_id, stages=stages, external_calls=0)
        record = AuditRecord(record_id=audit.audit_id,
                             action="observe", source=audit.category)
        stages.append(AuditStage("audit_record", True, record.record_id))
        stages.append(AuditStage("builder", True, "compose_dto"))
        stages.append(AuditStage("preview", True, "external_calls=0"))
        return AuditPipelineRun(
            ok=True, audit_id=audit_id, stages=stages, external_calls=0)
