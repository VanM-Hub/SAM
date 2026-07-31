"""Sprint 244 — Vision Model.

Program B — Model Runtime Integration.
Representasi image input. Tidak inference.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.vision_model import VisionModel
from sam.model_runtime.vision_input import VisionInput
from sam.model_runtime.vision_request import VisionRequest
from sam.model_runtime.vision_preview import VisionPreviewEngine, VisionPreview
from sam.model_runtime.vision_validator import VisionValidator
from sam.model_runtime.vision_summary import VisionSummary
from sam.model_runtime.conversation_vision import ConversationVision
from sam.model_runtime.dashboard_vision import DashboardVision


def test_vision_model_immutable():
    m = VisionModel(vision_id="v1", name="visual")
    assert m.external_calls == 0
    assert m.accepts_image is True
    with pytest.raises(Exception):
        m.name = "x"


def test_vision_input_representation_only():
    img = VisionInput(image_id="i1", width=640, height=480)
    assert "no pixel data" in img.as_dict()["note"]
    assert img.width == 640


def test_vision_request_immutable():
    img = VisionInput(image_id="i1")
    r = VisionRequest(request_id="r1", prompt="what is this?", images=[img])
    assert r.external_calls == 0
    assert len(r.images) == 1
    with pytest.raises(Exception):
        r.prompt = "x"


def test_vision_preview_no_inference():
    eng = VisionPreviewEngine()
    r = VisionRequest(request_id="r1", images=[VisionInput(image_id="i1")])
    pv = eng.preview(r)
    assert isinstance(pv, VisionPreview)
    assert pv.image_count == 1
    assert "no inference" in pv.note
    assert pv.external_calls == 0


def test_vision_validator():
    v = VisionValidator()
    good = VisionRequest(request_id="r1", images=[VisionInput(image_id="i1")])
    assert v.validate_request(good).valid is True
    bad = VisionRequest(request_id="", images=[])
    assert v.validate_request(bad).valid is False
    bad_img = VisionRequest(request_id="r2", images=[VisionInput(image_id="i2", media_type="image/gif")])
    assert v.validate_request(bad_img).valid is False


def test_vision_summary():
    s = VisionSummary(summary_id="s1", images=[VisionInput(image_id="i1")])
    assert s.external_calls == 0
    assert s.as_dict()["image_count"] == 1


def test_conversation_vision_bridge():
    conv = ConversationVision()
    out = conv.preview_images("conv-1", [VisionInput(image_id="i1")])
    assert out.external_calls == 0
    assert out.preview.image_count == 1


def test_dashboard_vision_rows():
    dash = DashboardVision()
    pv = VisionPreview(preview_id="p", request_id="r1", image_count=2)
    dash.add(pv)
    assert len(dash.rows()) == 1
    assert dash.rows()[0].image_count == 2
    assert dash.summary()["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.vision_preview as vp
    src = inspect.getsource(vp)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
