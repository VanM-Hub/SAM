"""
Integration tests — Service & Deployment Layer (Phase 1)
"""

import pytest
from sam.service.manager import ServiceManager
from sam.service.systemd import generate_unit_file, SYSTEMD_UNIT


class TestSystemdUnit:
    def test_unit_file_content(self):
        assert "[Unit]" in SYSTEMD_UNIT
        assert "Description=SAM" in SYSTEMD_UNIT
        assert "[Service]" in SYSTEMD_UNIT
        assert "[Install]" in SYSTEMD_UNIT
        assert "ExecStart=" in SYSTEMD_UNIT
        assert "Restart=on-failure" in SYSTEMD_UNIT

    def test_unit_file_generation(self, tmp_path):
        unit_path = tmp_path / "sam.service"
        generate_unit_file(str(unit_path))
        assert unit_path.exists()
        content = unit_path.read_text()
        assert "Description=SAM" in content


class TestSAMServiceMock:
    def test_windows_service_mock(self):
        from sam.service.windows import SAMService
        service = SAMService()
        assert service._svc_name_ == "SAMRuntime"
        assert service._svc_display_name_ == "SAM Runtime Service"


class TestServiceManager:
    @pytest.mark.asyncio
    async def test_service_manager_init(self):
        manager = ServiceManager()
        assert manager.os in ("Windows", "Linux", "Darwin")

    @pytest.mark.asyncio
    async def test_service_status(self):
        manager = ServiceManager()
        status = await manager.status()
        assert isinstance(status, str)

    @pytest.mark.asyncio
    async def test_service_install_unsupported(self):
        import platform
        if platform.system() == "Darwin":
            manager = ServiceManager()
            result = await manager.install()
            assert result is False


@pytest.mark.asyncio
async def test_desktop_launcher_imports():
    import sam.launcher.desktop
    assert hasattr(sam.launcher.desktop, "main")


class TestDeploymentFiles:
    def test_dockerfile_exists(self):
        import os
        assert os.path.exists("Dockerfile")

    def test_dockerfile_has_entrypoint(self):
        with open("Dockerfile", "r") as f:
            content = f.read()
        assert "ENTRYPOINT" in content
        assert "sam.launcher.desktop" in content

    def test_docker_compose_exists(self):
        import os
        assert os.path.exists("docker-compose.yml")

    def test_launcher_bat_exists(self):
        import os
        assert os.path.exists("scripts/launcher.bat")

    def test_launcher_sh_exists(self):
        import os
        assert os.path.exists("scripts/launcher.sh")

    def test_sam_service_exists(self):
        import os
        assert os.path.exists("sam.service")
