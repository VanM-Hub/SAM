"""
Decision Runtime V3 — Approval Preparation Layer.

Extends Decision Runtime with approval preparation pipeline.
Does NOT modify existing decision logic.
Does NOT submit approvals.
"""

from typing import Optional, Dict, Any
from .package_protocol import IncomingDecisionPackage
from .package_consumer import PackageConsumer
from .package_normalizer import PackageNormalizer
from .package_validator import PackageValidator, DecisionPackageValidationResult
from .package_context import DecisionContext, DecisionContextBuilder
from .evaluation import DecisionEvaluation
from .evaluation_engine import DecisionEvaluator
from .planning import DecisionPlan
from .planner import DecisionPlanner
from .approval_preparation import ApprovalPreparation
from .approval_builder import ApprovalBuilder
from .conversation_package import DecisionConversationPackageBridge
from .dashboard_package import DecisionDashboardPackageBridge
from .conversation_evaluation import DecisionConversationEvaluationBridge
from .dashboard_evaluation import DecisionDashboardEvaluationBridge
from .conversation_planning import DecisionConversationPlanningBridge
from .dashboard_planning import DecisionDashboardPlanningBridge
from .conversation_approval import DecisionConversationApprovalBridge
from .dashboard_approval import DecisionDashboardApprovalBridge


class DecisionRuntimeV3:
    """
    Decision Runtime V3 — Full Preparation Pipeline.

    Pipeline:
        Receive → Validate → Normalize → Context Builder
        → Evaluate → Plan → Approval Preparation

    Does NOT create missions, submit approvals, or execute.
    """

    def __init__(self) -> None:
        self._consumer = PackageConsumer()
        self._normalizer = PackageNormalizer()
        self._validator = PackageValidator()
        self._context_builder = DecisionContextBuilder()
        self._evaluator = DecisionEvaluator()
        self._planner = DecisionPlanner()
        self._approval_builder = ApprovalBuilder()

        self._conversation = DecisionConversationPackageBridge(self)
        self._dashboard = DecisionDashboardPackageBridge(self)
        self._conversation_eval = DecisionConversationEvaluationBridge(self)
        self._dashboard_eval = DecisionDashboardEvaluationBridge(self)
        self._conversation_plan = DecisionConversationPlanningBridge(self)
        self._dashboard_plan = DecisionDashboardPlanningBridge(self)
        self._conversation_approval = DecisionConversationApprovalBridge(self)
        self._dashboard_approval = DecisionDashboardApprovalBridge(self)

        self._latest_incoming: Optional[IncomingDecisionPackage] = None
        self._latest_normalized: Optional[IncomingDecisionPackage] = None
        self._latest_validation: Optional[DecisionPackageValidationResult] = None
        self._latest_context: Optional[DecisionContext] = None
        self._latest_evaluation: Optional[DecisionEvaluation] = None
        self._latest_plan: Optional[DecisionPlan] = None
        self._latest_approval: Optional[ApprovalPreparation] = None
        self._consume_count: int = 0
        self._valid_count: int = 0
        self._evaluation_count: int = 0
        self._ready_count: int = 0
        self._blocked_count: int = 0
        self._plan_count: int = 0
        self._approval_count: int = 0
        self._approval_ready_count: int = 0

    @property
    def conversation(self): return self._conversation
    @property
    def dashboard(self): return self._dashboard
    @property
    def conversation_eval(self): return self._conversation_eval
    @property
    def dashboard_eval(self): return self._dashboard_eval
    @property
    def conversation_plan(self): return self._conversation_plan
    @property
    def dashboard_plan(self): return self._dashboard_plan
    @property
    def conversation_approval(self): return self._conversation_approval
    @property
    def dashboard_approval(self): return self._dashboard_approval

    def consume(self, package_dict: Dict[str, Any]) -> Dict[str, Any]:
        incoming = self._consumer.consume(package_dict)
        self._latest_incoming = incoming; self._consume_count += 1

        validation = self._validator.validate(incoming)
        self._latest_validation = validation
        if validation.valid: self._valid_count += 1

        normalized = self._normalizer.normalize(incoming) if validation.valid else incoming
        self._latest_normalized = normalized

        context = self._context_builder.build(normalized) if validation.valid else None
        self._latest_context = context

        evaluation = None
        if context:
            evaluation = self._evaluator.evaluate(context)
            self._latest_evaluation = evaluation; self._evaluation_count += 1
            if evaluation.ready == "READY": self._ready_count += 1
            elif evaluation.ready == "BLOCKED": self._blocked_count += 1

        plan = None
        if evaluation:
            plan = self._planner.plan(evaluation)
            self._latest_plan = plan; self._plan_count += 1

        approval = None
        if plan:
            approval = self._approval_builder.build(plan)
            self._latest_approval = approval; self._approval_count += 1
            if approval.ready_for_submission: self._approval_ready_count += 1

        return {
            "package_id": incoming.package_id, "received": True,
            "valid": validation.valid, "validation_score": validation.score,
            "normalized": normalized is not None,
            "context_ready": context.is_ready if context else False,
            "evaluation_ready": evaluation.ready if evaluation else "NONE",
            "plan_alternatives": len(plan.alternatives) if plan else 0,
            "approval_ready": approval.ready_for_submission if approval else False,
            "total_consumed": self._consume_count, "total_valid": self._valid_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "consume_count": self._consume_count, "valid_count": self._valid_count,
            "evaluation_count": self._evaluation_count, "ready_count": self._ready_count,
            "blocked_count": self._blocked_count, "plan_count": self._plan_count,
            "approval_count": self._approval_count, "approval_ready": self._approval_ready_count,
            "has_latest": self._latest_incoming is not None,
            "has_evaluation": self._latest_evaluation is not None,
            "has_plan": self._latest_plan is not None,
            "has_approval": self._latest_approval is not None,
        }
