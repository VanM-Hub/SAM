"""Base classes for SDK components."""

from abc import ABC, abstractmethod
from typing import Any

from sam.runtime.context import ExecutionContext


class Capability(ABC):
    """Abstract base definition of a capability.

    Concrete capabilities should implement the ``execute`` method and
    expose a ``metadata`` attribute of type ``sam.models.Capability``.
    """

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> Any:
        """Execute the capability with the given context.

        Args:
            context: Runtime information for the execution.

        Returns:
            The result of the capability execution.
        """
        raise NotImplementedError