"""
Service Manager — Phase 1

Mengelola instalasi, start, stop, dan status service
di berbagai platform (Windows, Linux).
"""

import structlog
import platform
from typing import Optional

logger = structlog.get_logger()


class ServiceManager:
    """Service Manager — cross-platform service lifecycle."""

    def __init__(self):
        self.os = platform.system()

    async def install(self) -> bool:
        """Install SAM sebagai service (Windows) atau generate unit file (Linux).

        Returns:
            True jika berhasil.
        """
        if self.os == "Windows":
            return await self._install_windows()
        elif self.os == "Linux":
            return await self._install_linux()
        else:
            logger.warning("service_install_not_supported", os=self.os)
            return False

    async def start(self) -> bool:
        """Start SAM service."""
        try:
            if self.os == "Windows":
                return await self._start_windows()
            elif self.os == "Linux":
                return await self._start_linux()
            return False
        except Exception as e:
            logger.error("service_start_error", error=str(e))
            return False

    async def stop(self) -> bool:
        """Stop SAM service."""
        try:
            if self.os == "Windows":
                return await self._stop_windows()
            elif self.os == "Linux":
                return await self._stop_linux()
            return False
        except Exception as e:
            logger.error("service_stop_error", error=str(e))
            return False

    async def status(self) -> str:
        """Get SAM service status.

        Returns:
            Status string (e.g. "running", "stopped", "unknown").
        """
        try:
            if self.os == "Windows":
                return await self._status_windows()
            elif self.os == "Linux":
                return await self._status_linux()
            return "unknown"
        except Exception as e:
            return f"error: {e}"

    # ── Windows ─────────────────────────────────────────────────────

    async def _install_windows(self) -> bool:
        """Install Windows Service via pywin32."""
        try:
            from .windows import SAMService
            import win32serviceutil
            import win32service

            win32serviceutil.InstallService(
                None,
                SAMService._svc_name_,
                SAMService._svc_display_name_,
                SAMService._svc_description_,
                startType=win32service.SERVICE_AUTO_START,
            )
            logger.info("windows_service_installed", name=SAMService._svc_name_)
            return True
        except ImportError:
            logger.error("pywin32_not_installed")
            return False

    async def _start_windows(self) -> bool:
        import win32serviceutil
        win32serviceutil.StartService("SAMRuntime")
        logger.info("windows_service_started")
        return True

    async def _stop_windows(self) -> bool:
        import win32serviceutil
        win32serviceutil.StopService("SAMRuntime")
        logger.info("windows_service_stopped")
        return True

    async def _status_windows(self) -> str:
        import win32serviceutil
        status_code = win32serviceutil.QueryServiceStatus("SAMRuntime")[1]
        status_map = {
            1: "stopped",
            2: "starting",
            3: "stopping",
            4: "running",
        }
        return status_map.get(status_code, f"unknown({status_code})")

    # ── Linux ───────────────────────────────────────────────────────

    async def _install_linux(self) -> bool:
        """Generate systemd unit file."""
        import subprocess
        from .systemd import generate_unit_file

        try:
            generate_unit_file()
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "sam"], check=True)
            logger.info("systemd_unit_installed")
            return True
        except Exception as e:
            logger.error("systemd_install_error", error=str(e))
            return False

    async def _start_linux(self) -> bool:
        import subprocess
        subprocess.run(["systemctl", "start", "sam"], check=True)
        return True

    async def _stop_linux(self) -> bool:
        import subprocess
        subprocess.run(["systemctl", "stop", "sam"], check=True)
        return True

    async def _status_linux(self) -> str:
        import subprocess
        result = subprocess.run(
            ["systemctl", "is-active", "sam"],
            capture_output=True, text=True,
        )
        return result.stdout.strip()
