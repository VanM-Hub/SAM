"""
Conversation Integration — executor → Conversation pipeline.

Pipeline:
  1. Plan diterima dari Conversation
  2. Policy evaluation (risk → approval)
  3. Jika butuh approval → simpan di ApprovalV2Workflow
  4. Jika auto-execute (SAFE/LOW) → execute di sandbox
  5. Verify hasil
  6. Record audit
  7. Observasi ulang sistem
  8. Update ConversationObject
  9. Buat HumanAnswer baru
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .execution_plan import ExecutionPlan, ExecutionPlanBuilder, PlanStatus
from .execution_policy import ExecutionPolicy, ExecutionDecision
from .sandbox import ExecutionSandbox
from .real_executor import FilesystemExecutor, CommandExecutor, ProcessExecutor, WorkspaceExecutor
from .verification import VerificationEngine, VerificationOutcome
from .approval_v2 import ApprovalV2Workflow
from .simulation import SimulationEngine
from .audit import AuditEventType, get_audit_trail


@dataclass
class ConversationExecutionResult:
    """Hasil eksekusi lengkap — dari Conversation perspective."""
    plan_id: str
    plan_title: str

    # Pipeline stages
    policy_decisions: List[Any] = field(default_factory=list)
    approval_items: List[Any] = field(default_factory=list)
    execution_result: Optional[Any] = None
    verification_results: List[Any] = field(default_factory=list)

    # Complete
    success: bool = False
    error_message: str = ""
    audit_entry_ids: List[str] = field(default_factory=list)

    # Conversation
    summary_text: str = ""

    def to_text(self) -> str:
        return self.summary_text or "Execution completed."

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "plan_title": self.plan_title,
            "success": self.success,
            "policy_count": len(self.policy_decisions),
            "approval_count": len(self.approval_items),
            "verification_count": len(self.verification_results),
            "audit_count": len(self.audit_entry_ids),
            "error_message": self.error_message,
        }


class ConversationExecutionPipeline:
    """Pipeline eksekusi dari Conversation perspective.

    Method utama:
      execute_from_plan(plan, conversation) -> ConversationExecutionResult
      execute_from_decision(proposal, conversation) -> ConversationExecutionResult

    Pipeline:
      Plan → Policy → (Approval) → Execute → Verify → Audit → Re-observe → Update Conversation
    """

    def __init__(self, sandbox: Optional[ExecutionSandbox] = None,
                 approval: Optional[ApprovalV2Workflow] = None,
                 policy: Optional[ExecutionPolicy] = None,
                 simulation: bool = True):
        self._sandbox = sandbox or ExecutionSandbox()
        self._approval = approval or ApprovalV2Workflow()
        self._policy = policy or ExecutionPolicy()
        self._simulation = simulation
        self._audit = get_audit_trail()

        # Executors
        self._filesystem = FilesystemExecutor(self._sandbox)
        self._command = CommandExecutor(self._sandbox)
        self._process = ProcessExecutor(self._sandbox)
        self._workspace = WorkspaceExecutor(self._sandbox)

    def execute_from_plan(self, plan: ExecutionPlan,
                          conversation=None,
                          approved_ids: List[str] = None) -> ConversationExecutionResult:
        """Execute plan melalui pipeline lengkap.

        Args:
            plan: ExecutionPlan
            conversation: Conversation object untuk re-observe
            approved_ids: ID approval yang sudah di-approve

        Returns:
            ConversationExecutionResult
        """
        result = ConversationExecutionResult(
            plan_id=plan.plan_id,
            plan_title=plan.source_decision_title or plan.plan_id,
        )
        approved_ids = approved_ids or []

        # Step 1: Policy evaluation
        policy_decs = self._policy.evaluate(plan, approved_ids, simulation_mode=self._simulation)
        result.policy_decisions = policy_decs

        # Step 2: Check if all approved
        if not ExecutionPolicy.can_execute(policy_decs):
            # Needs approval — create approval items
            for dec in policy_decs:
                if dec.decision == ExecutionDecision.NEEDS_APPROVAL:
                    item = self._approval.submit(
                        title=dec.action_title,
                        description=dec.blocking_reason,
                        plan_id=plan.plan_id,
                    )
                    result.approval_items.append(item)

            result.summary_text = "Action blocked — needs human approval. {} item(s) created in approval queue.".format(
                len(result.approval_items))
            return result

        # Step 3: Execute (simulation or sandbox)
        if self._simulation:
            result.execution_result = SimulationEngine(self._policy).simulate(plan)
            # In simulation, skip real executors
            result.success = result.execution_result.predicted_success
        else:
            # Route actions to appropriate executor
            all_action_logs = []
            executors = [
                (self._filesystem, ["filesystem"]),
                (self._command, ["command"]),
                (self._process, ["process"]),
                (self._workspace, ["workspace"]),
            ]

            all_ok = True
            for executor, categories in executors:
                executor_plan = self._filter_plan_by_category(plan, categories)
                if executor_plan and executor_plan.actions:
                    executor.prepare(executor_plan)
                    ex_result = executor.execute(executor_plan)
                    all_action_logs.extend(ex_result.action_results)
                    if not executor.verify(executor_plan, ex_result):
                        all_ok = False

            result.success = all_ok

        # Step 4: Verification
        engine = VerificationEngine()
        verifications = engine.verify_plan(plan)
        result.verification_results = verifications

        # Step 5: Audit
        entry = self._audit.record(
            AuditEventType.EXECUTION_COMPLETED if result.success else AuditEventType.EXECUTION_FAILED,
            plan.plan_id, "conversation_pipeline",
            "Plan execution: {}".format("SUCCESS" if result.success else "FAILURE"),
            description="Actions: {}".format(len(plan.actions)),
            actor="ConversationExecutionPipeline",
        )
        result.audit_entry_ids.append(entry.id)

        # Step 6: Re-observe (if conversation available)
        if conversation and hasattr(conversation, 'observe'):
            try:
                conversation.observe()
            except Exception:
                pass

        # Step 7: Summary
        result.summary_text = "Execution {status} — {ok}/{total} actions completed, {v} verifications, audit #{audit}".format(
            status="PASSED" if result.success else "FAILED",
            ok=len(result.policy_decisions),
            total=len(plan.actions),
            v=len(verifications),
            audit=entry.id,
        )

        return result

    def execute_from_proposal(self, proposal, conversation=None,
                              approved_ids: List[str] = None) -> ConversationExecutionResult:
        """Build plan from proposal, then execute."""
        plan = ExecutionPlanBuilder.from_decision_proposal(proposal)
        return self.execute_from_plan(plan, conversation, approved_ids)

    def _filter_plan_by_category(self, plan: ExecutionPlan, categories: List[str]) -> Optional[ExecutionPlan]:
        """Filter plan hanya untuk satu kategori executor."""
        filtered_actions = [
            a for a in plan.actions
            if getattr(a, 'category', 'general').lower() in [c.lower() for c in categories]
        ]
        if not filtered_actions:
            return None

        from .execution_plan import ExecutionPlan
        return ExecutionPlan(
            plan_id=plan.plan_id + "_" + categories[0],
            source_decision_id=plan.source_decision_id,
            source_decision_title=plan.source_decision_title,
            actions=filtered_actions,
            verification_steps=plan.verification_steps,
            rollback_steps=plan.rollback_steps,
        )
