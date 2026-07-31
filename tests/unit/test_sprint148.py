"""Sprint 148 — Docker Provider Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.docker.docker_provider import DockerProvider
from sam.providers.docker.container_request import ContainerRequest
from sam.providers.docker.image_request import ImageRequest
from sam.providers.docker.compose_request import ComposeRequest
from sam.providers.docker.validator import DockerValidator, DockerValidation
from sam.providers.docker.preview import DockerPreview, DockerPreviewEngine
from sam.providers.docker.history import DockerHistory, DockerHistoryEntry
from sam.providers.docker.conversation_docker import ConversationDockerBridge
from sam.providers.docker.dashboard_docker import DashboardDockerBridge
from sam.providers.base.base_provider import ProviderError
from sam.providers.dashboard.dashboard_provider import ExecutionCard


class TestDockerProvider:
    def test_descriptor(self):
        p = DockerProvider()
        assert p.descriptor.provider_type == "docker"

    def test_supports_kinds(self):
        p = DockerProvider()
        assert p.supports("container_create")
        assert p.supports("image_pull")
        assert p.supports("compose_up")

    def test_plan(self):
        p = DockerProvider()
        r = p.plan("container", "app")
        assert r["preview"] is True
        assert r["engine_contacted"] is False
        assert r["external_calls"] == 0

    def test_plan_bad_kind(self):
        with pytest.raises(ProviderError):
            DockerProvider().plan("kube", "x")

    def test_external_always_zero(self):
        p = DockerProvider()
        p.plan("image", "nginx")
        assert p.external_calls == 0


class TestRequests:
    def test_container_valid(self):
        r = ContainerRequest("r1", "nginx:latest")
        assert r.is_valid() is True

    def test_image_valid(self):
        r = ImageRequest("r1", "nginx")
        assert r.is_valid() is True

    def test_compose_valid(self):
        r = ComposeRequest("r1", "myproj")
        assert r.is_valid() is True

    def test_immutable(self):
        r = ContainerRequest("r1", "nginx")
        with pytest.raises(FrozenInstanceError):
            r.image = "app"

    def test_image_immutable(self):
        r = ImageRequest("r1", "nginx")
        with pytest.raises(FrozenInstanceError):
            r.reference = "app"


class TestDockerValidator:
    def test_valid_container(self):
        v = DockerValidator().validate_container(ContainerRequest("r1", "nginx"))
        assert v.valid is True

    def test_invalid_container(self):
        v = DockerValidator().validate_container(ContainerRequest("", ""))
        assert v.valid is False

    def test_valid_image(self):
        v = DockerValidator().validate_image(ImageRequest("r1", "nginx"))
        assert v.valid is True

    def test_valid_compose(self):
        v = DockerValidator().validate_compose(ComposeRequest("r1", "proj"))
        assert v.valid is True


class TestDockerPreviewEngine:
    def test_preview(self):
        p = DockerPreviewEngine().preview("container", "app", "container_create", "r1")
        assert p.executed is False
        assert p.engine_contacted is False
        assert p.external_calls == 0


class TestDockerHistory:
    def test_record(self):
        h = DockerHistory()
        h.record(DockerHistoryEntry("r1", "image", "nginx", "image_pull"))
        assert h.count() == 1

    def test_no_execution(self):
        h = DockerHistory()
        h.record(DockerHistoryEntry("r1", "image", "nginx", "image_pull"))
        assert h.total_external_calls() == 0


class TestConversationDockerBridge:
    def test_describe(self):
        b = ConversationDockerBridge(DockerProvider())
        assert "docker" in b.describe()

    def test_contract(self):
        b = ConversationDockerBridge(DockerProvider())
        assert "docker" in b.contract()

    def test_supports(self):
        b = ConversationDockerBridge(DockerProvider())
        assert b.supports("compose_up")


class TestDashboardDockerBridge:
    def test_card(self):
        b = DashboardDockerBridge(DockerProvider())
        card = b.card()
        assert isinstance(card, ExecutionCard)
        assert card.provider_id == "docker"
        assert card.verdict == "ready"


class TestDockerImmutability:
    DTO_CLASSES = [
        ContainerRequest, ImageRequest, ComposeRequest,
        DockerValidation, DockerPreview, DockerHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
