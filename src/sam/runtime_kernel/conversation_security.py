"""Conversation Security Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.security_manager import SecurityManager
from sam.runtime_kernel.access_controller import AccessController
from sam.runtime_kernel.audit_logger import AuditLogger
from sam.runtime_kernel.verdict_engine import VerdictEngine


class ConversationSecurity:
    def __init__(self, mgr: SecurityManager, ac: AccessController,
                 logger: AuditLogger, verdict: VerdictEngine) -> None:
        self._mgr = mgr
        self._ac = ac
        self._logger = logger
        self._verdict = verdict

    def get_manager(self) -> SecurityManager:
        return self._mgr

    def get_access_controller(self) -> AccessController:
        return self._ac

    def get_audit_logger(self) -> AuditLogger:
        return self._logger

    def get_verdict_engine(self) -> VerdictEngine:
        return self._verdict

    def describe_layers(self) -> List[str]:
        return ["policy", "access", "audit", "verdict"]

    def count_layers(self) -> int:
        return 4

    def get_policy_count(self) -> int:
        return self._mgr.count_policies()

    def get_audit_count(self) -> int:
        return self._mgr.count_audits()


class DashboardSecurity:
    def __init__(self, mgr: SecurityManager, ac: AccessController,
                 logger: AuditLogger) -> None:
        self._mgr = mgr
        self._ac = ac
        self._logger = logger

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Security Manager",
            description=f"{self._mgr.count_policies()} policies",
            status="ready",
            metrics={"policies": self._mgr.count_policies(),
                     "audits": self._mgr.count_audits()},
            items=["policy", "audit"],
        )

    def access_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Access Controller",
            description=f"{self._ac.count()} rules",
            status="ready",
            metrics={"rules": self._ac.count()},
            items=["access"],
        )

    def audit_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Audit Logger",
            description=f"{self._logger.count()} entries",
            status="ready",
            metrics={"entries": self._logger.count()},
            items=["audit"],
        )

    def verdict_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Verdict Engine",
            description="Security verdicts",
            status="ready",
            metrics={"verdicts": 0},
            items=["allow", "deny"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Security Summary",
            description="Ringkasan keamanan runtime",
            status="ready",
            metrics={"layers": 4, "policies": self._mgr.count_policies()},
            items=["policy", "access", "audit", "verdict"],
        )
