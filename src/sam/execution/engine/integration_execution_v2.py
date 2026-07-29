# OP-418 — Integration Execution V2
# Python 3.8, frozen DTO, synchronous, no connector execution

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_builder import ExecutionBuilder, ExecutionPackage
from .execution_validator import ExecutionValidator, ValidationReport
from .rollback_planner import RollbackPlanner, RollbackPlan, RollbackSummary
from .execution_scheduler import ExecutionScheduler, ExecutionQueue, ScheduleSummary
from .conversation_execution_v2 import ConversationExecutionV2Bridge, ExecutionQueryResultV2
from .dashboard_execution_v2 import ExecutionDashboardV2Builder, ExecutionDashboardV2

from sam.execution.execution_request import ExecutionPlan


@dataclass(frozen=True)
class EnginePipelineResult:
    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    package: Optional[ExecutionPackage] = None
    validation: Optional[ValidationReport] = None
    rollback_plan: Optional[RollbackPlan] = None
    schedule: Optional[ExecutionQueue] = None
    conversation_result: Optional[ExecutionQueryResultV2] = None
    dashboard: Optional[ExecutionDashboardV2] = None
    pipeline_complete: bool = False
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ExecutionEnginePipeline:
    """Integration pipeline: Plan → Builder → Validator → Rollback → Scheduler → Guardian → Conversation → Dashboard.

    Pipeline:
    Execution Plan → Execution Builder → Validator → Rollback Planner → Scheduler → Guardian → Conversation → Dashboard

    No connector execution — produces ready-to-execute package.
    """

    def __init__(
        self,
        builder: Optional[ExecutionBuilder] = None,
        validator: Optional[ExecutionValidator] = None,
        rollback_planner: Optional[RollbackPlanner] = None,
        scheduler: Optional[ExecutionScheduler] = None,
        conversation_bridge: Optional[ConversationExecutionV2Bridge] = None,
        dashboard_builder: Optional[ExecutionDashboardV2Builder] = None,
    ) -> None:
        self._builder = builder or ExecutionBuilder()
        self._validator = validator or ExecutionValidator()
        self._rollback_planner = rollback_planner or RollbackPlanner()
        self._scheduler = scheduler or ExecutionScheduler()
        self._conversation_bridge = conversation_bridge or ConversationExecutionV2Bridge(
            self._builder, self._validator,
            self._rollback_planner, self._scheduler,
        )
        self._dashboard_builder = dashboard_builder or ExecutionDashboardV2Builder()

    # --- Pipeline Steps ---

    def build_package(self, plan: ExecutionPlan) -> ExecutionPackage:
        """Step 1: Build execution package from plan."""
        return self._builder.build(plan)

    def validate_package(self, pkg: ExecutionPackage) -> ValidationReport:
        """Step 2: Validate execution package."""
        return self._validator.validate(pkg)

    def plan_rollback(self, pkg: ExecutionPackage) -> RollbackPlan:
        """Step 3: Plan rollback."""
        return self._rollback_planner.plan(pkg)

    def create_schedule(self, pkg: ExecutionPackage) -> ExecutionQueue:
        """Step 4: Create execution schedule."""
        queue = self._scheduler.schedule(pkg)
        return self._scheduler.reorder_by_dependency(queue)

    # --- Full Pipeline ---

    def run(self, plan: ExecutionPlan) -> EnginePipelineResult:
        """Run the full execution engine pipeline."""
        try:
            pkg = self.build_package(plan)
            report = self.validate_package(pkg)
            rp = self.plan_rollback(pkg)
            queue = self.create_schedule(pkg)
            conv = self._conversation_bridge.query("execution package")
            dash = ExecutionDashboardV2Builder.build(pkg, report, rp, queue)

            return EnginePipelineResult(
                package=pkg,
                validation=report,
                rollback_plan=rp,
                schedule=queue,
                conversation_result=conv,
                dashboard=dash,
                pipeline_complete=True,
            )

        except Exception as e:
            return EnginePipelineResult(
                pipeline_complete=False,
                error=str(e),
            )

    def run_from_requests(self, *requests) -> EnginePipelineResult:
        """Convenience: create plan from requests and run pipeline."""
        plan = ExecutionPlan(requests=requests)
        return self.run(plan)
