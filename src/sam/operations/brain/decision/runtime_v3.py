"""
Decision Runtime V3 — Package Consumption Layer.

Extends existing Decision Runtime with package consumption pipeline.
Does NOT modify existing decision logic.
Synchronous only. Preview only.
"""

from typing import Optional, Dict, Any
from .package_protocol import IncomingDecisionPackage
from .package_consumer import PackageConsumer
from .package_normalizer import PackageNormalizer
from .package_validator import PackageValidator, DecisionPackageValidationResult
from .package_context import DecisionContext, DecisionContextBuilder
from .conversation_package import DecisionConversationPackageBridge
from .dashboard_package import DecisionDashboardPackageBridge


class DecisionRuntimeV3:
    """
    Decision Runtime V3 — Package Consumption.

    Pipeline:
        Receive Package → Validate → Normalize → Context Builder

    Does NOT create missions, approvals, or execute.
    Backward compatible with Decision Runtime V2.
    """

    def __init__(self) -> None:
        self._consumer = PackageConsumer()
        self._normalizer = PackageNormalizer()
        self._validator = PackageValidator()
        self._context_builder = DecisionContextBuilder()
        self._conversation = DecisionConversationPackageBridge(self)
        self._dashboard = DecisionDashboardPackageBridge(self)

        self._latest_incoming: Optional[IncomingDecisionPackage] = None
        self._latest_normalized: Optional[IncomingDecisionPackage] = None
        self._latest_validation: Optional[DecisionPackageValidationResult] = None
        self._latest_context: Optional[DecisionContext] = None
        self._consume_count: int = 0
        self._valid_count: int = 0

    @property
    def conversation(self) -> DecisionConversationPackageBridge:
        return self._conversation

    @property
    def dashboard(self) -> DecisionDashboardPackageBridge:
        return self._dashboard

    def consume(self, package_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consume a Guardian DecisionPackage.

        Pipeline:
            1. Receive package
            2. Validate
            3. Normalize
            4. Build context

        Args:
            package_dict: Dict representation of a Guardian DecisionPackage.

        Returns:
            Dict with pipeline results.
        """
        # 1. Receive
        incoming = self._consumer.consume(package_dict)
        self._latest_incoming = incoming
        self._consume_count += 1

        # 2. Validate
        validation = self._validator.validate(incoming)
        self._latest_validation = validation
        if validation.valid:
            self._valid_count += 1

        # 3. Normalize
        normalized = self._normalizer.normalize(incoming) if validation.valid else incoming
        self._latest_normalized = normalized

        # 4. Build context
        context = self._context_builder.build(normalized) if validation.valid else None
        self._latest_context = context

        return {
            "package_id": incoming.package_id,
            "received": True,
            "valid": validation.valid,
            "validation_score": validation.score,
            "normalized": normalized is not None,
            "context_ready": context.is_ready if context else False,
            "total_consumed": self._consume_count,
            "total_valid": self._valid_count,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "consume_count": self._consume_count,
            "valid_count": self._valid_count,
            "has_latest": self._latest_incoming is not None,
            "latest_valid": self._latest_validation.valid if self._latest_validation else False,
            "has_context": self._latest_context is not None,
            "context_ready": self._latest_context.is_ready if self._latest_context else False,
        }
