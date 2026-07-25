"""Workflow engine for executing a sequence of capabilities."""

import structlog
from typing import List, Any

from .context import ExecutionContext
from .runtime import CapabilityRuntime


class WorkflowEngine:
    """Executes a list of capability steps sequentially using the same context."""

    def __init__(self, runtime: CapabilityRuntime) -> None:
        self.runtime = runtime
        self.logger = structlog.get_logger()

    async def run(self, steps: List[str], context: ExecutionContext) -> List[Any]:
        """Run each step in order.

        Args:
            steps: List of capability IDs to execute.
            context: ExecutionContext shared across steps.

        Returns:
            List of results from each step.

        Raises:
            Exception: Propagates the first exception encountered.
        """
        results: list = []
        for step_id in steps:
            self.logger.info("Executing workflow step", step=step_id)
            try:
                result = await self.runtime.execute_capability(step_id, context)
                results.append(result)
            except Exception as exc:  # pragma: no cover - passthrough
                self.logger.error("Step failed", step=step_id, error=str(exc))
                raise
        return results