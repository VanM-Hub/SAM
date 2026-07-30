"""Runtime Identity — identitas runtime."""
from __future__ import annotations
from sam.runtime_kernel.runtime_context import RuntimeIdentity, RuntimeEnvironment


class IdentityBuilder:
    """Builder identitas runtime — preview-only."""

    def build(self, identity_id: str, hostname: str, instance_name: str,
              instance_type: str = "development") -> RuntimeIdentity:
        return RuntimeIdentity(
            identity_id=identity_id,
            hostname=hostname,
            instance_name=instance_name,
            instance_type=instance_type,
        )


class EnvironmentBuilder:
    """Builder environment runtime — preview-only."""

    def build(self, env_id: str, env_type: str) -> RuntimeEnvironment:
        return RuntimeEnvironment(environment_id=env_id, environment_type=env_type)
