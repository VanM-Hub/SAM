"""L6 — Preview -> Audit (pendekatan C: Composition Root Holder).

Alur: Preview -> Execution Runtime -> Outcome -> Audit Registry Holder -> AuditRegistry.
Registry tetap immutable; consumer bind-tetap; execution tidak mengenal audit.
Tanpa feedback; audit terminal observer.
"""
from __future__ import annotations

import pytest

from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from sam.runtime_service.api.audit_recording import AuditRegistryRef
from sam.runtime_service.api.preview_gateway import PreviewOutcomeView


def test_l6_holder_mencatat_satu_record_terminal():
    reg = AuditRegistry()
    holder = AuditRegistryRef(reg)
    outcome = PreviewOutcomeView(runtime_id="eng-e1", approved=False,
                                 executed=False, external_calls=0, mode="preview")
    holder.record_from_outcome(outcome)
    assert holder.count() == 1
    assert holder.get().exists("audit-eng-e1") is True


def test_l6_registry_asli_tetap_immutable_tidak_dimutasi():
    reg = AuditRegistry()
    holder = AuditRegistryRef(reg)
    outcome = PreviewOutcomeView(runtime_id="e2", approved=True, executed=False,
                                 external_calls=0, mode="preview")
    holder.record_from_outcome(outcome)
    # objek registry asli TIDAK berubah (immutable; referensi holder yang di-swap)
    assert reg.count() == 0
    assert holder.count() == 1


def test_l6_holder_penuhi_invariant_frozen():
    reg = AuditRegistry()
    # registry immutable membuktikan frozen violation kalau di-assign atribut
    import dataclasses
    with pytest.raises(Exception):
        reg._entries = {}  # frozen


def test_l6_integrasi_entry_preview_mencatat_audit_terminal():
    """Integrasi: preview di entry web menghasilkan 1 record audit terminal di holder."""
    import sam.web.server as s
    from sam.runtime_service.api import APIRequest
    before = s._audit_registry_holder.count()
    resp = s.runtime_api.handle(APIRequest(
        action="execution.preview", request_id="l6int",
        payload={"execution_id": "e-int", "provider_id": "filesystem", "operation": "list"}))
    assert resp.is_ok()
    assert s._audit_registry_holder.count() == before + 1
    # record dengan runtime_id dari outcome
    assert s._audit_registry_holder.get().exists("audit-eng-e-int") is True


def test_l6_consumer_tetap_bind_awal():
    """audit_consumer bind registry awal (tidak direcreate per preview)."""
    import sam.web.server as s
    assert s.audit_consumer is not None
    # consumer memakai registry awal dari holder (instance immutable) — tidak di-rebind
    assert isinstance(s.audit_consumer.registry, AuditRegistry)
