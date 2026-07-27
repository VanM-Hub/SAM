"""
Recovery Manager — Phase 0

Deteksi crash, restore dari checkpoint, replay, verify.
Pipeline:
    1. detect_crash → 2. load_session → 3. restore_checkpoint →
    4. replay → 5. verify
"""

import structlog
from typing import Optional, Dict, Any
from .state import RuntimeState

logger = structlog.get_logger()


class RecoveryManager:
    """Recovery Manager — crash detection and state restoration."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def recover(self) -> bool:
        """Jalankan recovery pipeline.

        Returns:
            True jika recovery berhasil, False jika gagal.
        """
        logger.info("recovery_started")
        self.coordinator.state = RuntimeState.RECOVERING

        try:
            # 1. Detect crash
            crash_detected = await self._detect_crash()
            if not crash_detected:
                logger.info("recovery_no_crash_detected")
                # No crash means we can proceed without full recovery
                self.coordinator.state = RuntimeState.READY
                return True

            # 2. Load session from last known state
            session = await self._load_session()
            if not session:
                logger.warning("recovery_no_session_found")
                # No session is not a fatal error — start fresh
                self.coordinator.state = RuntimeState.READY
                return True

            # 3. Restore checkpoint
            checkpoint = await self._restore_checkpoint(session)
            if not checkpoint:
                logger.warning("recovery_no_checkpoint_found")
                self.coordinator.state = RuntimeState.READY
                return True

            # 4. Replay from checkpoint
            await self._replay(checkpoint)

            # 5. Verify restored state
            verified = await self._verify()
            if not verified:
                logger.error("recovery_verification_failed")
                self.coordinator.state = RuntimeState.SAFE_MODE
                return False

            self.coordinator.state = RuntimeState.READY
            logger.info("recovery_completed")
            return True

        except Exception as e:
            logger.error("recovery_failed", error=str(e))
            self.coordinator.state = RuntimeState.SAFE_MODE
            return False

    async def _detect_crash(self) -> bool:
        """Deteksi apakah runtime sebelumnya crash.

        Returns:
            True jika crash terdeteksi, False jika shutdown normal.
        """
        session = self.coordinator.session_manager.get_current_session()
        if session:
            state = session.get("state", "UNKNOWN")
            # Jika session masih RUNNING saat startup → crash
            return state == "RUNNING"
        return False

    async def _load_session(self) -> Optional[Dict[str, Any]]:
        """Muat session terakhir yang tersimpan."""
        return self.coordinator.session_manager.get_current_session()

    async def _restore_checkpoint(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ambil checkpoint terakhir dari session."""
        checkpoints = session.get("checkpoints", [])
        if checkpoints:
            return checkpoints[-1]
        return None

    async def _replay(self, checkpoint: Dict[str, Any]) -> None:
        """Replay actions dari checkpoint (simulasi)."""
        logger.info("recovery_replay", checkpoint_type=checkpoint.get("type", "unknown"))

    async def _verify(self) -> bool:
        """Verifikasi state setelah recovery (simulasi)."""
        logger.info("recovery_verify")
        return True
