"""Test endpoint /workflow (L2 — hilangkan hardcode; data dari WorkflowRegistry).

Validasi:
- Endpoint `/workflow` memakai `workflow_consumer` (jalur resmi WorkflowRegistry).
- Tidak lagi berisi data hardcode (literal wf-00X / nama workflow statis).
- Data dibentuk dari `WorkflowPreview` (read-only, external_calls=0).
"""
from __future__ import annotations
import inspect

import sam.web.server as server


def test_workflow_page_menggunakan_workflow_consumer():
    """Endpoint memakai workflow_consumer (bukan literal hardcode)."""
    src = inspect.getsource(server.workflow_page)
    assert "workflow_consumer" in src
    assert ".list_workflows()" in src


def test_workflow_page_tidak_hardcode_data():
    """Tidak ada literal workflow hardcode (wf-00X / nama statis)."""
    src = inspect.getsource(server.workflow_page)
    for banned in ("wf-001", "wf-002", "wf-003", "wf-004",
                   "Health Check Cycle", "Provider Connectivity Test",
                   "Knowledge Import", "Plugin Discovery"):
        assert banned not in src, f"masih terdapat data hardcode: {banned}"


def test_workflow_page_membentuk_dict_tampilan_dari_preview():
    """Endpoint memetakan WorkflowPreview ke dict tampilan (id dari workflow_id)."""
    src = inspect.getsource(server.workflow_page)
    assert '"id": data["workflow_id"]' in src
    assert '"name": data["name"]' in src


def test_workflow_consumer_tersedia_di_entry():
    """workflow_consumer terpasang di entry web dengan registry (jalur resmi)."""
    assert hasattr(server, "workflow_consumer")
    assert server.workflow_consumer is not None
