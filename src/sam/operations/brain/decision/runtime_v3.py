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
from .submission_plan import ApprovalSubmissionPlan
from .conversation_package import DecisionConversationPackageBridge
from .dashboard_package import DecisionDashboardPackageBridge
from .conversation_evaluation import DecisionConversationEvaluationBridge
from .dashboard_evaluation import DecisionDashboardEvaluationBridge
from .conversation_planning import DecisionConversationPlanningBridge
from .dashboard_planning import DecisionDashboardPlanningBridge
from .conversation_approval import DecisionConversationApprovalBridge
from .dashboard_approval import DecisionDashboardApprovalBridge
from .approval_bridge import ApprovalBridge
from .approval_status import ApprovalStatusMirrorStore, ApprovalStatusMirror, ApprovalState
from .conversation_adapter import DecisionConversationAdapterBridge
from .dashboard_adapter import DecisionDashboardAdapterBridge
from .submission_builder import SubmissionBuilder
from .submission_queue import SubmissionQueuePlanner, SubmissionQueue
from .conversation_submission import DecisionConversationSubmissionBridge
from .dashboard_submission import DecisionDashboardSubmissionBridge
from .approval_gateway import ApprovalGateway
from .conversation_gateway import DecisionConversationGatewayBridge
from .dashboard_gateway import DecisionDashboardGatewayBridge
from .session_builder import SessionBuilder
from .session_registry import SessionRegistry
from .session_history import SessionHistory
from .conversation_session import DecisionConversationSessionBridge
from .dashboard_session import DecisionDashboardSessionBridge
from .lifecycle_engine import LifecycleEngine
from .lifecycle_history import LifecycleHistory
from .conversation_lifecycle import DecisionConversationLifecycleBridge
from .dashboard_lifecycle import DecisionDashboardLifecycleBridge
from .activation_engine import ActivationEngine
from .activation_history import ActivationHistory
from .conversation_activation import DecisionConversationActivationBridge
from .dashboard_activation import DecisionDashboardActivationBridge
from .certification_engine import CertificationEngine
from .conversation_certification import DecisionConversationCertificationBridge
from .dashboard_certification import DecisionDashboardCertificationBridge


class DecisionRuntimeV3:
    """
    Decision Runtime V3 — Full Pipeline with Approval Adapter.

    Pipeline:
        Receive → Validate → Normalize → Context Builder
        → Evaluate → Plan → Approval Preparation
        → Approval Adapter (NEW)

    Does NOT create missions, submit approvals, or execute.
    Approval adapter is preview only.
    """

    def __init__(self) -> None:
        self._consumer = PackageConsumer()
        self._normalizer = PackageNormalizer()
        self._validator = PackageValidator()
        self._context_builder = DecisionContextBuilder()
        self._evaluator = DecisionEvaluator()
        self._planner = DecisionPlanner()
        self._approval_builder = ApprovalBuilder()
        self._bridge = ApprovalBridge()
        self._status_store = ApprovalStatusMirrorStore()
        self._submission_builder = SubmissionBuilder()
        self._queue_planner = SubmissionQueuePlanner()
        self._submission_queue = None
        self._gateway = ApprovalGateway()
        self._session_builder = SessionBuilder()
        self._session_registry = SessionRegistry()
        self._session_history = SessionHistory()
        self._lifecycle_engine = LifecycleEngine()
        self._activation_engine = ActivationEngine()
        self._certification_engine = CertificationEngine()

        self._conversation = DecisionConversationPackageBridge(self)
        self._dashboard = DecisionDashboardPackageBridge(self)
        self._conversation_eval = DecisionConversationEvaluationBridge(self)
        self._dashboard_eval = DecisionDashboardEvaluationBridge(self)
        self._conversation_plan = DecisionConversationPlanningBridge(self)
        self._dashboard_plan = DecisionDashboardPlanningBridge(self)
        self._conversation_approval = DecisionConversationApprovalBridge(self)
        self._dashboard_approval = DecisionDashboardApprovalBridge(self)
        self._conversation_adapter = DecisionConversationAdapterBridge(self)
        self._dashboard_adapter = DecisionDashboardAdapterBridge(self)
        self._conversation_submission = DecisionConversationSubmissionBridge(self)
        self._dashboard_submission = DecisionDashboardSubmissionBridge(self)
        self._conversation_gateway = DecisionConversationGatewayBridge(self)
        self._dashboard_gateway = DecisionDashboardGatewayBridge(self)
        self._conversation_session = DecisionConversationSessionBridge(self)
        self._dashboard_session = DecisionDashboardSessionBridge(self)
        self._conversation_lifecycle = DecisionConversationLifecycleBridge(self)
        self._dashboard_lifecycle = DecisionDashboardLifecycleBridge(self)
        self._conversation_activation = DecisionConversationActivationBridge(self)
        self._dashboard_activation = DecisionDashboardActivationBridge(self)
        self._conversation_certification = DecisionConversationCertificationBridge(self)
        self._dashboard_certification = DecisionDashboardCertificationBridge(self)

        self._latest_incoming: Optional[IncomingDecisionPackage] = None
        self._latest_normalized: Optional[IncomingDecisionPackage] = None
        self._latest_validation: Optional[DecisionPackageValidationResult] = None
        self._latest_context: Optional[DecisionContext] = None
        self._latest_evaluation: Optional[DecisionEvaluation] = None
        self._latest_plan: Optional[DecisionPlan] = None
        self._latest_approval: Optional[ApprovalPreparation] = None
        self._latest_submission: Optional[ApprovalSubmissionPlan] = None
        self._consume_count: int = 0
        self._valid_count: int = 0
        self._evaluation_count: int = 0
        self._ready_count: int = 0
        self._blocked_count: int = 0
        self._plan_count: int = 0
        self._approval_count: int = 0
        self._approval_ready_count: int = 0
        self._submission_count: int = 0
        self._submission_ready_count: int = 0

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
    @property
    def conversation_adapter(self): return self._conversation_adapter
    @property
    def dashboard_adapter(self): return self._dashboard_adapter
    @property
    def conversation_submission(self): return self._conversation_submission
    @property
    def dashboard_submission(self): return self._dashboard_submission
    @property
    def conversation_gateway(self): return self._conversation_gateway
    @property
    def dashboard_gateway(self): return self._dashboard_gateway
    @property
    def conversation_session(self): return self._conversation_session
    @property
    def dashboard_session(self): return self._dashboard_session
    @property
    def conversation_lifecycle(self): return self._conversation_lifecycle
    @property
    def dashboard_lifecycle(self): return self._dashboard_lifecycle
    @property
    def conversation_activation(self): return self._conversation_activation
    @property
    def dashboard_activation(self): return self._dashboard_activation
    @property
    def conversation_certification(self): return self._conversation_certification
    @property
    def dashboard_certification(self): return self._dashboard_certification

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

            # Approval Adapter (NEW v5.13.0)
            import datetime
            bridge_result = self._bridge.bridge(approval)
            status_mirror = ApprovalStatusMirror(
                envelope_id=bridge_result["envelope_id"],
                state=ApprovalState.PENDING,
                timestamp=datetime.datetime.now().timestamp(),
                message="Prepared for approval — preview only",
                references={"approval_id": bridge_result["envelope_id"]},
            )
            self._status_store.record(status_mirror)

            # Submission Planning (NEW v5.14.0)
            if self._bridge.last_envelope:
                submission_plan = self._submission_builder.build(self._bridge.last_envelope)
                self._latest_submission = submission_plan; self._submission_count += 1
                if submission_plan.ready: self._submission_ready_count += 1
                self._submission_queue = self._queue_planner.plan([submission_plan])

                # Approval Gateway (NEW v5.15.0)
                gateway_result = self._gateway.process(submission_plan)

                # Approval Session (NEW v5.16.0)
                if gateway_result.success:
                    request = self._gateway.registry.last_request
                    if request:
                        session = self._session_builder.build(request)
                        self._session_registry.register(session)
                        self._session_history.record(
                            session_id=session.session_id,
                            event="created",
                            prev="NONE",
                            new_s=session.state.name,
                        )

                # Approval Lifecycle (NEW v5.17.0)
                if session:
                    lifecycle = self._lifecycle_engine.initialize(
                        session_id=session.session_id,
                        session_ready=session.ready,
                    )

                # Approval Activation (NEW v5.18.0)
                if lifecycle:
                    activation = self._activation_engine.evaluate(
                        lifecycle,
                        lifecycle_id=lifecycle.lifecycle_id,
                        session_id=lifecycle.session_id,
                    )

                # Approval Certification (NEW v5.19.0)
                if activation:
                    certification = self._certification_engine.certify(
                        activation,
                        activation_id=activation.activation_id,
                        lifecycle_id=activation.lifecycle_id,
                    )

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
            "bridge_count": self._bridge.bridge_count if self._bridge else 0,
            "submission_count": self._submission_count,
            "submission_ready": self._submission_ready_count,
            "gateway_count": self._gateway.gateway_count if self._gateway else 0,
            "session_count": self._session_registry.count if self._session_registry else 0,
            "lifecycle_count": self._lifecycle_engine.count if self._lifecycle_engine else 0,
            "activation_count": self._activation_engine.count if self._activation_engine else 0,
            "certification_count": self._certification_engine.count if self._certification_engine else 0,
            "has_latest": self._latest_incoming is not None,
            "has_evaluation": self._latest_evaluation is not None,
            "has_plan": self._latest_plan is not None,
            "has_approval": self._latest_approval is not None,
        }
