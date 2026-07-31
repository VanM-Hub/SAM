"""Sprint 242 — Embedding Model.

Program B — Model Runtime Integration.
Tidak menghasilkan embedding asli. Hanya representasi.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.embedding_model import EmbeddingModel
from sam.model_runtime.embedding_request import EmbeddingRequest
from sam.model_runtime.embedding_result import EmbeddingResult, EmbeddingVector
from sam.model_runtime.embedding_builder import EmbeddingBuilder
from sam.model_runtime.embedding_preview import EmbeddingPreviewEngine, EmbeddingPreview
from sam.model_runtime.embedding_validator import EmbeddingValidator
from sam.model_runtime.conversation_embedding import ConversationEmbedding
from sam.model_runtime.dashboard_embedding import DashboardEmbedding


def test_embedding_model_immutable():
    m = EmbeddingModel(embedding_id="e1", name="text-embed", dimension_hint=768)
    assert m.external_calls == 0
    assert m.preview_only is True
    with pytest.raises(Exception):
        m.name = "x"
    assert m.as_dict()["external_calls"] == 0


def test_embedding_request_immutable():
    r = EmbeddingRequest(request_id="r1", texts=["a", "b"])
    assert r.external_calls == 0
    assert r.mode == "preview"
    assert len(r.texts) == 2
    with pytest.raises(Exception):
        r.input_type = "x"


def test_placeholder_result_no_real_vector():
    b = EmbeddingBuilder()
    req = b.build_request("r1", ["alpha", "beta"])
    res = b.placeholder_result(req, dimension_hint=384)
    assert isinstance(res, EmbeddingResult)
    assert len(res.vectors) == 2
    assert all(not v.filled for v in res.vectors)  # tidak dihitung
    assert res.summary["filled"] is False
    assert res.external_calls == 0
    assert "no real embedding" in res.summary["note"]


def test_embedding_preview_deterministic():
    eng = EmbeddingPreviewEngine()
    req = EmbeddingRequest(request_id="r1", texts=["x", "y", "z"])
    pv = eng.preview(req, dimension_hint=512)
    assert isinstance(pv, EmbeddingPreview)
    assert pv.text_count == 3
    assert pv.would_compute is False
    assert pv.external_calls == 0


def test_embedding_validator():
    v = EmbeddingValidator()
    good = EmbeddingRequest(request_id="r1", texts=["a"])
    assert v.validate_request(good).valid is True
    bad = EmbeddingRequest(request_id="", texts=[])
    assert v.validate_request(bad).valid is False
    res = EmbeddingResult(request_id="r1", vectors=[
        EmbeddingVector(index=0, dimension=384, filled=False)])
    assert v.validate_result(res, expected=1).valid is True
    assert v.validate_result(res, expected=2).valid is False


def test_conversation_embedding_bridge():
    conv = ConversationEmbedding()
    out = conv.embed_preview("conv-1", ["hello world"])
    assert out.external_calls == 0
    assert out.preview.text_count == 1
    assert out.request.external_calls == 0


def test_dashboard_embedding_rows():
    dash = DashboardEmbedding()
    res = EmbeddingResult(request_id="r1", vectors=[
        EmbeddingVector(index=0, dimension=384, filled=False)],
        summary={"filled": False})
    dash.add(res)
    assert len(dash.rows()) == 1
    assert dash.rows()[0].text_count == 1
    assert dash.summary()["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.embedding_builder as eb
    src = inspect.getsource(eb)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
