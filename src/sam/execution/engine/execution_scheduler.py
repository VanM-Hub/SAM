# OP-415 — Execution Scheduler
# Python 3.8, frozen DTO, synchronous, no execution

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_task import ExecutionTask, TaskGroup, TaskDependency, TaskStatus
from .execution_builder import ExecutionPackage


@dataclass(frozen=True)
class ExecutionStage:
    stage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: Tuple[ExecutionTask, ...] = field(default_factory=tuple)
    parallel: bool = False
    estimated_duration_seconds: int = 0
    stage_order: int = 0


@dataclass(frozen=True)
class ExecutionQueue:
    queue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stages: Tuple[ExecutionStage, ...] = field(default_factory=tuple)
    total_stages: int = 0
    total_tasks: int = 0
    estimated_duration_seconds: int = 0


@dataclass(frozen=True)
class ScheduleSummary:
    total_stages: int = 0
    total_tasks: int = 0
    parallel_groups: int = 0
    estimated_duration_seconds: int = 0
    requires_sequential: bool = False
    requires_approval: bool = True


class ExecutionScheduler:
    """Schedules execution tasks into stages with ordering and parallelism.

    Groups tasks into sequential stages, parallel within each stage.
    Respects dependency ordering and priority.
    """

    def schedule(self, package: ExecutionPackage) -> ExecutionQueue:
        """Create an execution schedule from an execution package.

        Stages are sequential. Tasks within a stage can be parallel.
        Tasks in the same parallel_group are in the same stage.
        """
        if not package.tasks:
            return ExecutionQueue()

        # Use existing groups as stages
        stages: List[ExecutionStage] = []

        for gidx, group in enumerate(package.groups):
            stage = ExecutionStage(
                name=group.name,
                tasks=group.tasks,
                parallel=group.parallel,
                estimated_duration_seconds=group.estimated_duration_seconds,
                stage_order=gidx + 1,
            )
            stages.append(stage)

        total_duration = sum(s.estimated_duration_seconds for s in stages)
        total_tasks = sum(len(s.tasks) for s in stages)

        return ExecutionQueue(
            stages=tuple(stages),
            total_stages=len(stages),
            total_tasks=total_tasks,
            estimated_duration_seconds=total_duration,
        )

    def reorder_by_dependency(self, queue: ExecutionQueue) -> ExecutionQueue:
        """Re-order tasks within each stage by dependency order."""
        # Within each stage, sort tasks so dependencies come first
        reordered_stages: List[ExecutionStage] = []

        for stage in queue.stages:
            stage_tasks = list(stage.tasks)
            # Simple topological sort within stage
            task_ids = set(t.task_id for t in stage_tasks)
            deps_met: Set[str] = set()
            ordered: List[ExecutionTask] = []
            remaining = list(stage_tasks)

            while remaining:
                for task in remaining[:]:
                    deps = [d.depends_on for d in task.dependencies
                            if d.required and d.depends_on in task_ids]
                    if all(d in deps_met for d in deps):
                        ordered.append(task)
                        deps_met.add(task.task_id)
                        remaining.remove(task)

                if remaining and ordered == [t for t in stage_tasks if t in ordered]:
                    # Cycle or remaining tasks with unmet external deps — just append
                    ordered.extend(remaining)
                    break

            reordered_stages.append(ExecutionStage(
                stage_id=stage.stage_id,
                name=stage.name,
                tasks=tuple(ordered),
                parallel=stage.parallel,
                estimated_duration_seconds=stage.estimated_duration_seconds,
                stage_order=stage.stage_order,
            ))

        return ExecutionQueue(
            queue_id=queue.queue_id,
            stages=tuple(reordered_stages),
            total_stages=queue.total_stages,
            total_tasks=queue.total_tasks,
            estimated_duration_seconds=queue.estimated_duration_seconds,
        )

    def to_summary(self, queue: ExecutionQueue) -> ScheduleSummary:
        """Convert queue to summary DTO."""
        parallel = sum(1 for s in queue.stages if s.parallel)
        requires_approval = any(
            t.requires_approval for s in queue.stages for t in s.tasks
        )
        return ScheduleSummary(
            total_stages=queue.total_stages,
            total_tasks=queue.total_tasks,
            parallel_groups=parallel,
            estimated_duration_seconds=queue.estimated_duration_seconds,
            requires_sequential=queue.total_stages > 0 and parallel == 0,
            requires_approval=requires_approval,
        )
