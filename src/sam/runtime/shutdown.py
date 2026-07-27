"""
Shutdown Manager — Phase 0

Graceful shutdown pipeline:
    stop accepting work → finish tasks → persist session →
    flush telemetry → shutdown plugins → close database → exit
"""

import asyncio
import structlog
from .state import RuntimeState

logger = structlog.get_logger()


class ShutdownManager:
    """Shutdown Manager — graceful shutdown pipeline."""

    def __init__(self, coordinator, timeout: int = 60):
        self.coordinator = coordinator
        self.timeout = timeout
        self._steps = [
            "_stop_accepting_work",
            "_finish_running_tasks",
            "_persist_session",
            "_flush_telemetry",
            "_shutdown_plugins",
            "_close_database",
        ]

    @property
    def steps(self) -> list:
        return list(self._steps)

    async def shutdown(self) -> bool:
        """Jalankan graceful shutdown pipeline.

        Returns:
            True jika semua langkah berhasil, False jika timeout/gagal.
        """
        logger.info("shutdown_started")
        self.coordinator.state = RuntimeState.STOPPING

        for step_name in self._steps:
            try:
                step_method = getattr(self, step_name)
                await asyncio.wait_for(step_method(), timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.warning("shutdown_step_timeout", step=step_name)
                return False
            except Exception as e:
                logger.error("shutdown_step_error", step=step_name, error=str(e))
                return False

        # End session
        if self.coordinator.session_manager.current_session:
            self.coordinator.session_manager.end_session("SHUTDOWN")

        self.coordinator.state = RuntimeState.SHUTDOWN
        logger.info("shutdown_completed")
        return True

    async def _stop_accepting_work(self) -> None:
        """1. Stop accepting new work requests."""
        logger.info("shutdown_stop_accepting_work")
        await asyncio.sleep(0.05)

    async def _finish_running_tasks(self) -> None:
        """2. Wait for in-flight tasks to complete."""
        logger.info("shutdown_finish_tasks")
        await asyncio.sleep(0.05)

    async def _persist_session(self) -> None:
        """3. Persist current session state."""
        logger.info("shutdown_persist_session")
        session = self.coordinator.session_manager.current_session
        if session:
            # Mark last activity before persist
            from datetime import datetime
            session["last_activity"] = datetime.utcnow().isoformat()
            self.coordinator.session_manager._save_session(session)
        await asyncio.sleep(0.05)

    async def _flush_telemetry(self) -> None:
        """4. Flush telemetry buffers."""
        logger.info("shutdown_flush_telemetry")
        await asyncio.sleep(0.05)

    async def _shutdown_plugins(self) -> None:
        """5. Gracefully shutdown all plugins."""
        logger.info("shutdown_plugins")
        await asyncio.sleep(0.05)

    async def _close_database(self) -> None:
        """6. Close database connections."""
        logger.info("shutdown_close_database")
        await asyncio.sleep(0.05)
