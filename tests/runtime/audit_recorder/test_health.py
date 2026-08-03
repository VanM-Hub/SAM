"""Test health service and reporting."""

import pytest
from src.sam.runtime.audit_recorder.services.health_service import HealthService
from src.sam.runtime.audit_recorder.lifecycle.recorder_lifecycle import (
    RecorderLifecycleState,
)


class TestHealthService:
    """Verify health reporting for Audit Recorder."""

    def test_uninitialized_maps_to_unavailable(self):
        hs = HealthService(
            lifecycle_getter=lambda: RecorderLifecycleState.UNINITIALIZED,
            record_count_getter=lambda: 0,
        )
        health = hs.get_health()
        assert health["status"] == "UNAVAILABLE"

    def test_initializing_maps_to_degraded(self):
        hs = HealthService(
            lifecycle_getter=lambda: RecorderLifecycleState.INITIALIZING,
            record_count_getter=lambda: 0,
        )
        health = hs.get_health()
        assert health["status"] == "DEGRADED"

    def test_running_maps_to_healthy(self):
        hs = HealthService(
            lifecycle_getter=lambda: RecorderLifecycleState.RUNNING,
            record_count_getter=lambda: 5,
        )
        health = hs.get_health()
        assert health["status"] == "HEALTHY"
        assert health["record_count"] == 5

    def test_stopping_maps_to_degraded(self):
        hs = HealthService(
            lifecycle_getter=lambda: RecorderLifecycleState.STOPPING,
            record_count_getter=lambda: 10,
        )
        health = hs.get_health()
        assert health["status"] == "DEGRADED"

    def test_stopped_maps_to_unavailable(self):
        hs = HealthService(
            lifecycle_getter=lambda: RecorderLifecycleState.STOPPED,
            record_count_getter=lambda: 3,
        )
        health = hs.get_health()
        assert health["status"] == "UNAVAILABLE"

    def test_none_lifecycle_maps_to_unknown(self):
        hs = HealthService(
            lifecycle_getter=lambda: None,
            record_count_getter=lambda: 0,
        )
        health = hs.get_health()
        assert health["status"] == "UNKNOWN"

    def test_none_count_gets_zero(self):
        hs = HealthService(
            lifecycle_getter=lambda: RecorderLifecycleState.RUNNING,
            record_count_getter=lambda: None,
        )
        health = hs.get_health()
        assert health["record_count"] == 0

    def test_default_getters(self):
        """HealthService works with default (None) getters."""
        hs = HealthService()
        health = hs.get_health()
        assert health["status"] == "UNKNOWN"
        assert health["record_count"] == 0

    def test_integration_with_recorder_service(self):
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )
        s = RecorderService()
        # UNINITIALIZED → UNAVAILABLE
        assert s.get_health()["status"] == "UNAVAILABLE"

        s.initialize()
        # RUNNING → HEALTHY
        assert s.get_health()["status"] == "HEALTHY"

        s.shutdown()
        # STOPPED → UNAVAILABLE
        assert s.get_health()["status"] == "UNAVAILABLE"
