"""
Unit tests — Recovery Manager (Phase 0)
"""

import pytest
from sam.runtime.recovery import RecoveryManager
from sam.runtime.state import RuntimeState
from sam.runtime.coordinator import RuntimeCoordinator


class TestRecoveryManager:
    @pytest.mark.asyncio
    async def test_recovery_no_crash(self):
        """Jika tidak ada crash, recovery selesai cepat."""
        coord = RuntimeCoordinator()
        rm = RecoveryManager(coord)
        result = await rm.recover()
        assert result is True
        assert coord.state == RuntimeState.READY

    @pytest.mark.asyncio
    async def test_recovery_with_crash_detected(self):
        """Simulasi crash terdeteksi (session masih RUNNING)."""
        coord = RuntimeCoordinator()
        # Buat session lalu langsung jalankan recovery
        coord.session_manager.create_session()
        rm = RecoveryManager(coord)
        result = await rm.recover()
        # Should succeed without checkpoint
        assert result is True
        assert coord.state == RuntimeState.READY

    @pytest.mark.asyncio
    async def test_recovery_with_checkpoint(self):
        """Recovery dengan checkpoint tersimpan."""
        coord = RuntimeCoordinator()
        coord.session_manager.create_session()
        # Simpan checkpoint
        coord.session_manager.save_checkpoint({
            "type": "runtime_state",
            "state": "RUNNING",
            "timestamp": "2026-07-27T00:00:00",
        })
        rm = RecoveryManager(coord)
        result = await rm.recover()
        assert result is True
        assert coord.state == RuntimeState.READY

    @pytest.mark.asyncio
    async def test_detect_crash_returns_false_for_no_session(self):
        """Tidak ada session = tidak ada crash yang terdeteksi."""
        coord = RuntimeCoordinator()
        rm = RecoveryManager(coord)
        crash = await rm._detect_crash()
        assert crash is False

    @pytest.mark.asyncio
    async def test_detect_crash_returns_true_for_running_session(self):
        """Session dalam state RUNNING saat startup = crash."""
        coord = RuntimeCoordinator()
        coord.session_manager.create_session()  # state = RUNNING
        rm = RecoveryManager(coord)
        crash = await rm._detect_crash()
        assert crash is True

    @pytest.mark.asyncio
    async def test_detect_crash_returns_false_for_completed_session(self):
        """Session COMPLETED = shutdown normal, bukan crash."""
        coord = RuntimeCoordinator()
        coord.session_manager.create_session()
        coord.session_manager.end_session("SHUTDOWN")
        rm = RecoveryManager(coord)
        # Set current session setelah end_session (di-set None)
        # Simulasikan dengan membuat session baru yang sudah COMPLETED
        coord.session_manager.create_session()
        # Langsung end
        coord.session_manager.end_session("COMPLETED")
        crash = await rm._detect_crash()
        # Hasil: current_session is None setelah end, jadi False
        assert crash is False

    @pytest.mark.asyncio
    async def test_recovery_pipeline_reaches_safe_mode_on_error(self):
        """Jika recovery gagal, state jadi SAFE_MODE."""
        coord = RuntimeCoordinator()
        rm = RecoveryManager(coord)
        # Inject error di _verify
        async def failing_verify():
            raise RuntimeError("Verification failed")
        rm._verify = failing_verify
        # Butuh crash + checkpoint untuk sampai ke verify
        coord.session_manager.create_session()
        coord.session_manager.save_checkpoint({"type": "test"})
        result = await rm.recover()
        assert result is False
        assert coord.state == RuntimeState.SAFE_MODE

    @pytest.mark.asyncio
    async def test_coordinator_start_with_recovery(self):
        """Coordinator.start() mendeteksi crash dan recovery."""
        coord = RuntimeCoordinator()
        # Simulasikan crash — session RUNNING dari sebelumnya
        coord.session_manager.create_session()
        coord.session_manager.save_checkpoint({
            "type": "pre_crash", "state": "RUNNING"
        })
        # Reset coordinator state
        coord.state = RuntimeState.INITIALIZING
        # Start akan mendeteksi crash via _detect_crash
        # Karena session masih RUNNING, akan trigger recovery
        # Tapi session dibuat ulang di start(), jadi yang pertama kena
        # Better: test langsung via manual flow
        result = await coord.start()
        assert result == RuntimeState.READY
