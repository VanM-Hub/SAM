"""Workflow Engine for executing WorkflowDefinition DSL."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.runtime.context import ExecutionContext
from sam.runtime.runtime import CapabilityRuntime
from sam.runtime.registry import CapabilityRegistry
from sam.workflow.models import WorkflowDefinition, WorkflowStep, WorkflowTransition
from sam.workflow.checkpoint import WorkflowCheckpoint, CheckpointStore, CheckpointStatus
from sam.models import CorrelationContext
from sam.persistence.database import Database
from sam.persistence.repositories import WorkflowStateRepository
from sam.reporting import ReportGenerator
from sam.events import EventBus, Event

logger = structlog.get_logger(__name__)


class WorkflowEngine:
    """Executes a WorkflowDefinition by running steps sequentially with transitions.

    Features:
    - Sequential step execution with on_success/on_failure/on_timeout transitions
    - Per-step execution tracking in executions table
    - Workflow state persistence in workflow_states table
    - Checkpoint after every step (pause/resume/recover via optional CheckpointStore)
    - CorrelationContext propagation across all steps
    - Automatic report generation on completion (success or failure)
    - Resume capability for paused workflows via checkpoint
    """

    def __init__(
        self,
        runtime: CapabilityRuntime,
        registry: CapabilityRegistry,
        db: Database,
        event_bus: EventBus,
        checkpoint_store: Optional[CheckpointStore] = None,
    ) -> None:
        self.runtime = runtime
        self.registry = registry
        self.db = db
        self.event_bus = event_bus
        self.workflow_repo = WorkflowStateRepository(db)
        self.checkpoint_store = checkpoint_store or CheckpointStore(db)
        self.logger = logger.bind(component="WorkflowEngine")

    async def run(
        self,
        definition: WorkflowDefinition,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a workflow definition.

        Args:
            definition: Parsed WorkflowDefinition from DSL
            context: ExecutionContext with correlation, services, stores

        Returns:
            Dictionary with workflow results including step results and final status
        """
        workflow_id = context.workflow_id or str(uuid.uuid4())
        correlation = context.correlation or CorrelationContext.new(workflow_id=workflow_id)
        correlation = correlation.with_workflow(workflow_id)

        # Serialize definition for persistence
        definition_json = definition.model_dump_json()

        # Create initial workflow state
        started_at = datetime.now(timezone.utc).isoformat()
        state_id = str(uuid.uuid4())
        await self.workflow_repo.create({
            "id": state_id,
            "workflow_id": workflow_id,
            "correlation_id": correlation.correlation_id,
            "definition": definition_json,
            "current_step": definition.steps[0].id if definition.steps else None,
            "status": "running",
            "started_at": started_at,
            "completed_at": None,
            "metadata": "{}",
        })

        # Emit workflow started event
        await self.event_bus.publish(Event(
            type="WorkflowStarted",
            source="workflow_engine",
            payload={
                "workflow_id": workflow_id,
                "workflow_name": definition.name,
                "version": definition.version,
                "correlation_id": correlation.correlation_id,
                "step_count": len(definition.steps),
            }
        ))

        step_results: List[Dict[str, Any]] = []
        cur_step: Optional[WorkflowStep] = definition.steps[0] if definition.steps else None
        final_status = "completed"
        error_info: Optional[str] = None

        all_step_ids = definition.get_step_ids()

        try:
            while cur_step is not None:
                # Update current step in state
                await self.workflow_repo.update(workflow_id, {
                    "current_step": cur_step.id,
                })

                # Execute the step
                step_result = await self._execute_step(
                    cur_step, definition, workflow_id, correlation, context
                )
                step_results.append(step_result)

                # Compute completed and pending steps
                completed_ids = [r["step_id"] for r in step_results]
                pending_ids = [sid for sid in all_step_ids if sid not in completed_ids and sid != cur_step.id]

                # Save checkpoint after each step
                checkpoint = WorkflowCheckpoint(
                    workflow_id=workflow_id,
                    correlation_id=correlation.correlation_id,
                    current_step=cur_step.id,
                    completed_steps=completed_ids,
                    pending_steps=pending_ids,
                    retry_count=0,
                    timestamp=datetime.now(timezone.utc),
                    status=CheckpointStatus.RUNNING.value,
                )
                await self.checkpoint_store.save(checkpoint)

                # Determine next step based on transition
                if step_result["success"]:
                    next_step_id = cur_step.transition.on_success
                else:
                    next_step_id = cur_step.transition.on_failure

                # Find next step
                cur_step = None
                if next_step_id:
                    cur_step = definition.get_step(next_step_id)
                    if cur_step is None:
                        self.logger.warning(
                            "Transition references unknown step",
                            next_step_id=next_step_id,
                            current_step=step_result["step_id"]
                        )
                        break
                else:
                    # No transition defined - end workflow
                    break

        except Exception as e:
            self.logger.exception("Workflow execution failed", workflow_id=workflow_id, error=str(e))
            final_status = "failed"
            error_info = str(e)
            error_info_json = json.dumps({"error": error_info})
            await self.workflow_repo.update(workflow_id, {
                "status": final_status,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "metadata": error_info_json,
            })
            raise
        else:
            # Workflow completed successfully
            completed_at = datetime.now(timezone.utc).isoformat()
            await self.workflow_repo.update(workflow_id, {
                "status": final_status,
                "completed_at": completed_at,
                "current_step": None,
            })

            await self.event_bus.publish(Event(
                type="WorkflowCompleted",
                source="workflow_engine",
                payload={
                    "workflow_id": workflow_id,
                    "workflow_name": definition.name,
                    "correlation_id": correlation.correlation_id,
                    "step_results": step_results,
                }
            ))

        finally:
            # Generate report for the workflow using correlation_id
            try:
                report_generator = ReportGenerator(self.db, self.event_bus)
                # We need to find the workflow execution_id to generate report
                # For workflow, we'll use the first execution's ID or correlation_id
                # Let's query executions for this workflow_id
                exec_rows = await self.db.fetch_all(
                    "SELECT id FROM executions WHERE workflow_id = ? ORDER BY started_at ASC",
                    [workflow_id]
                )
                if exec_rows:
                    # Generate report for the workflow as a whole using the correlation_id
                    # For now, generate report for each execution
                    for exec_row in exec_rows:
                        try:
                            await report_generator.generate(exec_row["id"])
                        except Exception as report_err:
                            self.logger.warning(
                                "Failed to generate report for workflow execution",
                                execution_id=exec_row["id"],
                                error=str(report_err)
                            )
            except Exception as report_err:
                self.logger.warning(
                    "Failed to generate workflow reports",
                    workflow_id=workflow_id,
                    error=str(report_err)
                )

        return {
            "workflow_id": workflow_id,
            "workflow_name": definition.name,
            "status": final_status,
            "step_results": step_results,
            "error": error_info,
            "correlation_id": correlation.correlation_id,
        }

    async def _execute_step(
        self,
        step: WorkflowStep,
        definition: WorkflowDefinition,
        workflow_id: str,
        correlation: CorrelationContext,
        parent_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a single workflow step.

        Creates a new execution_id for this step, inherits correlation_id,
        runs the capability, and records execution in database.
        """
        execution_id = str(uuid.uuid4())
        step_correlation = correlation.with_execution(execution_id)

        self.logger.info(
            "Executing workflow step",
            workflow_id=workflow_id,
            step_id=step.id,
            capability=step.capability,
            execution_id=execution_id,
        )

        # Record execution start
        started_at = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """
            INSERT INTO executions (id, correlation_id, capability_id, workflow_id, step_name, status, started_at, inputs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [execution_id, step_correlation.correlation_id, step.capability, workflow_id, step.id, "running", started_at, json.dumps(step.inputs)]
        )

        # Create step-specific context
        step_context = ExecutionContext(
            execution_id=uuid.UUID(execution_id),
            workflow_id=workflow_id,
            step_name=step.id,
            inputs=step.inputs,
            evidence=parent_context.evidence,
            knowledge=parent_context.knowledge,
            services=parent_context.services,
            correlation=step_correlation,
            parent_context=parent_context,
        )

        # Emit step started event
        await self.event_bus.publish(Event(
            type="WorkflowStepStarted",
            source="workflow_engine",
            payload={
                "workflow_id": workflow_id,
                "step_id": step.id,
                "capability_id": step.capability,
                "execution_id": execution_id,
                "correlation_id": step_correlation.correlation_id,
            }
        ))

        try:
            # Execute capability with optional timeout
            timeout = step.timeout if step.timeout else None
            result = await self.runtime.execute_capability(
                step.capability,
                step_context,
                timeout=timeout,
            )

            # Record success
            completed_at = datetime.now(timezone.utc).isoformat()
            await self.db.execute(
                """
                UPDATE executions SET status = ?, completed_at = ?, result = ? WHERE id = ?
                """,
                ["success", completed_at, json.dumps(result), execution_id]
            )

            step_result = {
                "step_id": step.id,
                "capability_id": step.capability,
                "execution_id": execution_id,
                "success": True,
                "result": result,
                "error": None,
            }

            await self.event_bus.publish(Event(
                type="WorkflowStepCompleted",
                source="workflow_engine",
                payload={
                    "workflow_id": workflow_id,
                    "step_id": step.id,
                    "execution_id": execution_id,
                    "result": result,
                }
            ))

            self.logger.info(
                "Workflow step completed",
                workflow_id=workflow_id,
                step_id=step.id,
                execution_id=execution_id,
            )
            return step_result

        except Exception as e:
            # Record failure
            completed_at = datetime.now(timezone.utc).isoformat()
            await self.db.execute(
                """
                UPDATE executions SET status = ?, completed_at = ?, error = ? WHERE id = ?
                """,
                ["failed", completed_at, str(e), execution_id]
            )

            step_result = {
                "step_id": step.id,
                "capability_id": step.capability,
                "execution_id": execution_id,
                "success": False,
                "result": None,
                "error": str(e),
            }

            await self.event_bus.publish(Event(
                type="WorkflowStepFailed",
                source="workflow_engine",
                payload={
                    "workflow_id": workflow_id,
                    "step_id": step.id,
                    "execution_id": execution_id,
                    "error": str(e),
                }
            ))

            self.logger.error(
                "Workflow step failed",
                workflow_id=workflow_id,
                step_id=step.id,
                execution_id=execution_id,
                error=str(e),
            )
            return step_result

    async def get_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state."""
        return await self.workflow_repo.get(workflow_id)

    async def resume(
        self,
        workflow_id: str,
        context: Optional[ExecutionContext] = None,
    ) -> Dict[str, Any]:
        """Resume a paused workflow from its latest checkpoint.

        Loads the checkpoint, restores state, and continues execution
        from the current_step onwards. Steps already completed are
        skipped.

        Args:
            workflow_id: The workflow to resume.
            context: Optional fresh context. If not provided, the checkpoint
                     payload is used to reconstruct minimal context.

        Returns:
            Dictionary with workflow results (same as run()).
        """
        checkpoint = await self.checkpoint_store.get(workflow_id)
        if not checkpoint:
            raise ValueError(f"No checkpoint found for workflow: {workflow_id}")

        if checkpoint.status not in (CheckpointStatus.RUNNING.value, CheckpointStatus.PAUSED.value):
            raise ValueError(
                f"Cannot resume workflow {workflow_id} in status: {checkpoint.status}"
            )

        self.logger.info(
            "Resuming workflow from checkpoint",
            workflow_id=workflow_id,
            current_step=checkpoint.current_step,
            completed_steps=len(checkpoint.completed_steps),
        )

        # Reconstruct context from checkpoint if not provided
        if context is None:
            from sam.runtime.context import ExecutionContext as EC
            from sam.models import CorrelationContext as CC
            from uuid import UUID
            context = EC(
                execution_id=UUID(checkpoint.workflow_id[:36] if len(checkpoint.workflow_id) >= 36 else "00000000-0000-0000-0000-000000000000"),
                workflow_id=checkpoint.workflow_id,
                inputs=checkpoint.payload.get("inputs", {}),
                services=checkpoint.payload.get("services", {}),
                evidence=checkpoint.payload.get("evidence", []),
                knowledge=checkpoint.payload.get("knowledge", {}),
                correlation=CC(
                    correlation_id=checkpoint.correlation_id,
                    workflow_id=checkpoint.workflow_id,
                ),
            )

        # Get workflow definition from the checkpoint payload or from DB state
        state = await self.workflow_repo.get(workflow_id)
        if not state or not state.get("definition"):
            raise ValueError(f"Workflow state not found for: {workflow_id}")

        definition = WorkflowDefinition.model_validate_json(state["definition"])

        # Mark as running
        await self.checkpoint_store.save(WorkflowCheckpoint(
            workflow_id=checkpoint.workflow_id,
            correlation_id=checkpoint.correlation_id,
            current_step=checkpoint.current_step,
            completed_steps=checkpoint.completed_steps,
            pending_steps=checkpoint.pending_steps,
            evidence_ids=checkpoint.evidence_ids,
            payload=checkpoint.payload,
            retry_count=checkpoint.retry_count,
            timestamp=datetime.now(timezone.utc),
            status=CheckpointStatus.RUNNING.value,
        ))

        # Build set of completed step IDs so we can skip them
        completed_set = set(checkpoint.completed_steps)

        # Determine starting step
        start_step_id = checkpoint.current_step
        start_step = definition.get_step(start_step_id)
        if not start_step:
            raise ValueError(f"Checkpoint references unknown step: {start_step_id}")

        # Execute from start_step onwards; skip already completed steps
        # by re-running the current_step (it may have been partially executed)
        step_results: List[Dict[str, Any]] = []
        cur_step: Optional[WorkflowStep] = start_step
        final_status = "completed"
        error_info: Optional[str] = None

        # Pre-populate results for completed steps
        for cid in checkpoint.completed_steps:
            if cid != start_step_id:
                step_results.append({
                    "step_id": cid,
                    "capability_id": cid,
                    "success": True,
                    "result": {"restored_from_checkpoint": True},
                    "error": None,
                })

        all_step_ids = definition.get_step_ids()

        try:
            while cur_step is not None:
                # Update current step in state
                await self.workflow_repo.update(workflow_id, {
                    "current_step": cur_step.id,
                })

                # Execute the step
                step_result = await self._execute_step(
                    cur_step, definition, workflow_id,
                    context.correlation, context
                )
                step_results.append(step_result)

                # Save checkpoint after each resumed step
                completed_ids = [r["step_id"] for r in step_results]
                pending_ids = [sid for sid in all_step_ids if sid not in completed_ids and sid != cur_step.id]
                await self.checkpoint_store.save(WorkflowCheckpoint(
                    workflow_id=workflow_id,
                    correlation_id=checkpoint.correlation_id,
                    current_step=cur_step.id,
                    completed_steps=completed_ids,
                    pending_steps=pending_ids,
                    retry_count=checkpoint.retry_count,
                    timestamp=datetime.now(timezone.utc),
                    status=CheckpointStatus.RUNNING.value,
                ))

                # Determine next step
                if step_result["success"]:
                    next_step_id = cur_step.transition.on_success
                else:
                    next_step_id = cur_step.transition.on_failure

                cur_step = None
                if next_step_id:
                    cur_step = definition.get_step(next_step_id)
                    if cur_step is None:
                        self.logger.warning(
                            "Transition references unknown step",
                            next_step_id=next_step_id,
                            current_step=step_result["step_id"]
                        )
                        break
                else:
                    break

        except Exception as e:
            self.logger.exception("Workflow resume failed", workflow_id=workflow_id, error=str(e))
            final_status = "failed"
            error_info = str(e)
            await self.workflow_repo.update(workflow_id, {
                "status": final_status,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "metadata": json.dumps({"error": error_info}),
            })
            await self.checkpoint_store.save(WorkflowCheckpoint(
                workflow_id=workflow_id,
                correlation_id=checkpoint.correlation_id,
                current_step=checkpoint.current_step,
                completed_steps=checkpoint.completed_steps,
                pending_steps=checkpoint.pending_steps,
                evidence_ids=checkpoint.evidence_ids,
                payload=checkpoint.payload,
                retry_count=checkpoint.retry_count,
                timestamp=datetime.now(timezone.utc),
                status=CheckpointStatus.FAILED.value,
            ))
            raise
        else:
            # Completed successfully
            completed_at = datetime.now(timezone.utc).isoformat()
            await self.workflow_repo.update(workflow_id, {
                "status": final_status,
                "completed_at": completed_at,
                "current_step": None,
            })
            await self.checkpoint_store.save(WorkflowCheckpoint(
                workflow_id=workflow_id,
                correlation_id=checkpoint.correlation_id,
                current_step=checkpoint.current_step,
                completed_steps=list(all_step_ids),
                pending_steps=[],
                evidence_ids=checkpoint.evidence_ids,
                payload=checkpoint.payload,
                retry_count=checkpoint.retry_count,
                timestamp=datetime.now(timezone.utc),
                status=CheckpointStatus.COMPLETED.value,
            ))

            await self.event_bus.publish(Event(
                type="WorkflowResumed",
                source="workflow_engine",
                payload={
                    "workflow_id": workflow_id,
                    "correlation_id": checkpoint.correlation_id,
                    "step_results": step_results,
                },
            ))

        return {
            "workflow_id": workflow_id,
            "status": final_status,
            "step_results": step_results,
            "error": error_info,
            "resumed": True,
        }