"""Conversation Runtime Context Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_configuration import ConfigurationEngine
from sam.runtime_kernel.runtime_identity import IdentityBuilder, EnvironmentBuilder


class ConversationRuntimeContext:
    """Conversation bridge untuk runtime context — 8 queries."""

    def __init__(self, config_engine: ConfigurationEngine,
                 identity_builder: IdentityBuilder,
                 env_builder: EnvironmentBuilder) -> None:
        self._config = config_engine
        self._identity = identity_builder
        self._env = env_builder

    def get_config_engine(self) -> ConfigurationEngine:
        return self._config

    def get_identity_builder(self) -> IdentityBuilder:
        return self._identity

    def get_env_builder(self) -> EnvironmentBuilder:
        return self._env

    def describe_layers(self) -> List[str]:
        return ["identity", "environment", "profile", "configuration"]

    def count_layers(self) -> int:
        return 4

    def get_setting_names(self) -> List[str]:
        return ["timeout", "retry", "debug", "mode", "log_level"]

    def count_settings(self) -> int:
        return 5

    def has_profile_caps(self) -> bool:
        return True


class DashboardRuntimeContext:
    """Dashboard bridge untuk runtime context — 5 cards."""

    def __init__(self, config_engine: ConfigurationEngine) -> None:
        self._config = config_engine

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Context Engine",
            description="Konteks runtime utama",
            status="ready",
            metrics={"layers": 4, "settings": 5},
            items=["identity", "environment", "profile", "configuration"],
        )

    def identity_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Identity",
            description="Identitas runtime",
            status="ready",
            metrics={"builders": 2},
            items=["IdentityBuilder", "EnvironmentBuilder"],
        )

    def environment_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Environment",
            description="Lingkungan runtime",
            status="ready",
            metrics={"profiles": 1, "features": 0},
            items=["EnvironmentEngine"],
        )

    def configuration_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Configuration",
            description="Konfigurasi runtime",
            status="ready",
            metrics={"capabilities": 4},
            items=["create", "merge", "get", "has"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Runtime Context Summary",
            description="Ringkasan konteks runtime",
            status="ready",
            metrics={"layers": 4},
            items=["identity", "env", "profile", "config"],
        )
