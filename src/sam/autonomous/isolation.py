"""
Plugin Isolation — Phase 1

Mengisolasi plugin yang bermasalah untuk mencegah dampak ke komponen lain.
"""

import structlog
from typing import Dict, Any, Optional
from .models import AutonomousAction, ActionType, RiskLevel, AutonomousActionStatus

logger = structlog.get_logger()


class PluginIsolation:
    """Isolasi plugin yang bermasalah — stop, isolate, flag."""

    # Simulated set of known plugins
    ACTIVE_PLUGINS = {
        "monitor", "guardian", "telemetry", "scheduler",
        "notifier", "backup", "updater", "connector",
    }

    def __init__(self, coordinator=None):
        self.coordinator = coordinator
        self._isolated: set = set()

    async def isolate(self, plugin_name: str) -> AutonomousAction:
        """Isolasi plugin yang bermasalah.

        Args:
            plugin_name: Nama plugin yang akan di-isolasi.

        Returns:
            AutonomousAction hasil eksekusi.
        """
        if plugin_name not in self.ACTIVE_PLUGINS:
            # Plugin tidak dikenal
            action = AutonomousAction(
                action_type=ActionType.ISOLATE,
                target=plugin_name,
                reason="Plugin {0} not found in active plugins".format(plugin_name),
                confidence=0.3,
                risk_level=RiskLevel.LOW,
            )
            action.status = AutonomousActionStatus.FAILED
            action.error = "Plugin not found: {0}".format(plugin_name)
            return action

        if plugin_name in self._isolated:
            action = AutonomousAction(
                action_type=ActionType.ISOLATE,
                target=plugin_name,
                reason="Plugin {0} is already isolated".format(plugin_name),
                confidence=1.0,
                risk_level=RiskLevel.LOW,
            )
            action.status = AutonomousActionStatus.COMPLETED
            action.result = {"status": "already_isolated", "plugin": plugin_name}
            return action

        # Determine risk level
        risk = RiskLevel.HIGH if plugin_name in ("guardian", "telemetry", "updater") else RiskLevel.MEDIUM

        action = AutonomousAction(
            action_type=ActionType.ISOLATE,
            target=plugin_name,
            reason="Isolating problematic plugin: {0}".format(plugin_name),
            confidence=0.85,
            risk_level=risk,
            steps=[
                "Stop plugin: {0}".format(plugin_name),
                "Disconnect plugin from event bus",
                "Remove plugin from active registry",
                "Verify isolation",
                "Notify operator",
            ],
        )

        if self.coordinator:
            result = await self.coordinator.action_executor.execute(action)
            if result.status.value == "completed":
                self._isolated.add(plugin_name)
                logger.info("plugin_isolated", plugin=plugin_name)
            return result

        # Without coordinator, simulate success
        self._isolated.add(plugin_name)
        action.status = AutonomousActionStatus.COMPLETED
        action.result = {"status": "isolated", "plugin": plugin_name}
        logger.info("plugin_isolated_standalone", plugin=plugin_name)
        return action

    async def restore(self, plugin_name: str) -> bool:
        """Restore plugin yang sebelumnya di-isolasi."""
        if plugin_name in self._isolated:
            self._isolated.remove(plugin_name)
            logger.info("plugin_restored", plugin=plugin_name)
            return True
        logger.warning("plugin_not_isolated", plugin=plugin_name)
        return False

    def get_isolated_plugins(self) -> set:
        """Ambil daftar plugin yang sedang di-isolasi."""
        return set(self._isolated)
