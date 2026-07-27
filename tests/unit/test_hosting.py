"""
Unit tests — Hosting Adapter (Phase 0)
"""

import pytest
from sam.hosting.base import HostingAdapter, DesktopAdapter, DockerAdapter


class TestDesktopAdapter:
    def test_get_workspace(self):
        adapter = DesktopAdapter()
        assert adapter.get_workspace() == "./workspace"

    def test_get_environment(self):
        adapter = DesktopAdapter()
        env = adapter.get_environment()
        assert isinstance(env, dict)

    def test_get_log_path(self):
        adapter = DesktopAdapter()
        assert adapter.get_log_path() == "./workspace/logs"

    def test_get_signal_handler(self):
        adapter = DesktopAdapter()
        assert adapter.get_signal_handler() is None


class TestDockerAdapter:
    def test_default_workspace(self):
        adapter = DockerAdapter()
        assert adapter.get_workspace() == "/opt/sam/workspace"

    def test_custom_workspace(self):
        adapter = DockerAdapter(workspace="/data/sam")
        assert adapter.get_workspace() == "/data/sam"

    def test_get_environment(self):
        adapter = DockerAdapter()
        env = adapter.get_environment()
        assert "CONTAINERIZED" in env
        assert env["CONTAINERIZED"] == "true"

    def test_get_log_path(self):
        adapter = DockerAdapter()
        assert adapter.get_log_path() == "/opt/sam/workspace/logs"

    def test_get_signal_handler(self):
        adapter = DockerAdapter()
        assert adapter.get_signal_handler() is None


class TestAdapterWithCoordinator:
    @pytest.mark.asyncio
    async def test_coordinator_with_desktop_adapter(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator(adapter=DesktopAdapter())
        assert coord.adapter_name == "Desktop"
        assert coord.hosting_adapter.get_workspace() == "./workspace"

    @pytest.mark.asyncio
    async def test_coordinator_with_docker_adapter(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator(adapter=DockerAdapter())
        assert coord.adapter_name == "Docker"
        assert coord.hosting_adapter.get_workspace() == "/opt/sam/workspace"

    @pytest.mark.asyncio
    async def test_coordinator_default_adapter(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        assert coord.adapter_name == "Desktop"
