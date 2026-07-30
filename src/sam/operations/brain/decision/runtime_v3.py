"""
Decision Runtime V3 — Evaluation Layer.

Extends Decision Runtime with decision evaluation pipeline.
Does NOT modify existing decision logic.
Synchronous only. Preview only.
"""

from typing import Optional, Dict, Any
from .package_protocol import IncomingDecisionPackage
from .package_consumer import PackageConsumer
from .package_normalizer import PackageNormalizer
from .package_validator import PackageValidator, DecisionPackageValidationResult
from .package_context import DecisionContext, DecisionContextBuilder
from .evaluation import DecisionEvaluation
from .evaluation_engine import DecisionEvaluator
from .conversation_package import DecisionConversationPackageBridge
from .dashboard_package import DecisionDashboardPackageBridge
from .conversation_evaluation import DecisionConversationEvaluationBridge
from .dashboard_evaluation import DecisionDashboardEvaluationBridge


class DecisionRuntimeV3:
    """
    Decision Runtime V3 — Package Consumption + Evaluation.

    Pipeline:
        Receive Package → Validate → Normalize → Context Builder
        → Evaluate → Existing Decision Runtime

    Does NOT create missions, approvals, or execute.
    Backward compatible.
    """

    def __init__(self) -> None:
        self._consumer = PackageConsumer()
        self._normalizer = PackageNormalizer()
        self._validator = PackageValidator()
        self._context_builder = DecisionContextBuilder()
        self._evaluator = DecisionEvaluator()

        self._conversation = DecisionConversationPackageBridge(self)
        self._dashboard = DecisionDashboardPackageBridge(self)
        self._conversation_eval = DecisionConversationEvaluationBridge(self)
        self._dashboard_eval = DecisionDashboardEvaluationBridge(self)

        self._latest_incoming: Optional[IncomingDecisionPackage] = None
        self._latest_normalized: Optional[IncomingDecisionPackage] = None
        self._latest_validation: Optional[DecisionPackageValidationResult] = None
        self._latest_context: Optional[DecisionContext] = None
        self._latest_evaluation: Optional[DecisionEvaluation] = None
        self._consume_count: int = 0
        self._valid_count: int = 0
        self._evaluation_count: int = 0
        self._ready_count: int = 0
        self._blocked_count: int = 0

    @property
    def conversation(self) -> DecisionConversationPackageBridge:
        return self._conversation

    @property
    def dashboard(self) -> DecisionDashboardPackageBridge:
        return self._dashboard

    @property
    def conversation_eval(self) -> DecisionConversationEvaluationBridge:
        return self._conversation_eval

    @property
    def dashboard_eval(self) -> DecisionDashboardEvaluationBridge:
        return self._dashboard_eval

    def consume(self, package_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consume a Guardian DecisionPackage and evaluate.

        Pipeline:
            1. Receive package
            2. Validate
            3. Normalize
            4. Build context
            5. Evaluate

        Args:
            package_dict: Dict representation of a Guardian DecisionPackage.

        Returns:
            Dict with pipeline results.
        """
        # 1-4. Existing pipeline
        incoming = self._consumer.consume(package_dict)
        self._latest_incoming = incoming
        self._consume_count += 1

        validation = self._validator.validate(incoming)
        self._latest_validation = validation
        if validation.valid:
            self._valid_count += 1

        normalized = self._normalizer.normalize(incoming) if validation.valid else incoming
        self._latest_normalized = normalized

        context = self._context_builder.build(normalized) if validation.valid else None
        self._latest_context = context

        # 5. Evaluate
        evaluation = None
        if context:
            evaluation = self._evaluator.evaluate(context)
            self._latest_evaluation = evaluation
            self._evaluation_count += 1
            if evaluation.ready == "READY":
                self._ready_count += 1
            elif evaluation.ready == "BLOCKED":
                self._blocked_count += 1

        return {
            "package_id": incoming.package_id,
            "received": True,
            "valid": validation.valid,
            "validation_score": validation.score,
            "normalized": normalized is not None,
            "context_ready": context.is_ready if context else False,
            "evaluation_ready": evaluation.ready if evaluation else "NONE",
            "evaluation_confidence": evaluation.confidence if evaluation else "NONE",
            "total_consumed": self._consume_count,
            "total_valid": self._valid_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "consume_count": self._consume_count,
            "valid_count": self._valid_count,
            "evaluation_count": self._evaluation_count,
            "ready_count": self._ready_count,
            "blocked_count": self._blocked_count,
            "has_latest": self._latest_incoming is not None,
            "latest_valid": self._latest_validation.valid if self._latest_validation else False,
            "has_context": self._latest_context is not None,
            "has_evaluation": self._latest_evaluation is not None,
        }
