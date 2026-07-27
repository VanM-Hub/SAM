"""
SAM Windows Service Wrapper.

Membungkus SAM Runtime sebagai Windows Service menggunakan pywin32.
Requires: pip install pywin32

Usage:
    python -m sam.service.windows install
    python -m sam.service.windows start
    python -m sam.service.windows stop
    python -m sam.service.windows remove
"""

import asyncio
import sys
from ..runtime.coordinator import RuntimeCoordinator

try:
    import servicemanager
    import win32serviceutil
    import win32service
    import win32event

    class SAMService(win32serviceutil.ServiceFramework):
        """SAM Runtime Windows Service."""

        _svc_name_ = "SAMRuntime"
        _svc_display_name_ = "SAM Runtime Service"
        _svc_description_ = "SAM — AI Operations Guardian Runtime"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.running = True
            self.coordinator = RuntimeCoordinator()

        def SvcStop(self):
            """Handle SERVICE_CONTROL_STOP — graceful shutdown."""
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.running = False
            asyncio.run(self.coordinator.stop())

        def SvcDoRun(self):
            """Main entry point when service starts."""
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ''),
            )
            self.main()

        def main(self):
            """Run coordinator and wait for stop signal."""
            asyncio.run(self.coordinator.start())
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


    if __name__ == '__main__':
        win32serviceutil.HandleCommandLine(SAMService)

except ImportError:
    # Not running on Windows — mock for testing
    class SAMService:
        """Mock SAMService for platforms without pywin32."""
        _svc_name_ = "SAMRuntime"
        _svc_display_name_ = "SAM Runtime Service"
        _svc_description_ = "SAM — AI Operations Guardian Runtime"

        def __init__(self, args=None):
            self.coordinator = RuntimeCoordinator()
