"""Example capability: Hello World."""

import datetime
import uuid

from sam.sdk.base import Capability
from sam.models import Capability as CapabilityModel
from sam.runtime.context import ExecutionContext


class HelloCapability(Capability):
    """A simple capability that returns a greeting."""

    # Metadata instance conforming to the Capability model
    metadata = CapabilityModel(
        id=uuid.uuid4(),
        created_at=datetime.datetime.utcnow(),
        capability_id="hello",
        name="Hello World",
        description="Says hello",
        owner="SAM",
        version="1.0.0",
        permissions=[],
        risk_level="Low",
        rollback_supported=False,
    )

    async def execute(self, context: ExecutionContext) -> dict:
        """Execute the capability.

        Args:
            context: Execution context containing logger and IDs.

        Returns:
            A dictionary with a greeting message.
        """
        context.logger.info("HelloCapability executed")
        return {"message": "Hello, World!"}