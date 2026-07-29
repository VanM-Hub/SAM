# OP-402 — Connector Capability
# Python 3.8, frozen DTO, synchronous, no execute/network/subprocess

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Set


BUILTIN_CAPABILITIES = (
    "read", "write", "create", "delete",
    "execute", "monitor", "approve", "rollback",
    "search", "notify",
)


@dataclass(frozen=True)
class Capability:
    name: str = ""
    description: str = ""
    risk_level: str = "low"
    requires_approval: bool = True
    requires_guardian: bool = False

    @staticmethod
    def builtin(name: str) -> "Capability":
        risk_map = {
            "read": "low", "search": "low", "monitor": "low",
            "notify": "low",
            "write": "medium", "create": "medium",
            "approve": "medium",
            "delete": "high", "execute": "high", "rollback": "high",
        }
        req_approval = {"write", "create", "delete", "execute",
                        "approve", "rollback"}
        req_guardian = {"delete", "execute", "rollback"}

        desc_map = {
            "read": "Read data from target",
            "write": "Write data to target",
            "create": "Create new resource on target",
            "delete": "Delete resource from target",
            "execute": "Execute command/action on target",
            "monitor": "Monitor target state",
            "approve": "Approve pending operations",
            "rollback": "Rollback previous operation",
            "search": "Search across target",
            "notify": "Send notification to target",
        }

        return Capability(
            name=name,
            description=desc_map.get(name, f"Capability: {name}"),
            risk_level=risk_map.get(name, "low"),
            requires_approval=name in req_approval,
            requires_guardian=name in req_guardian,
        )


@dataclass(frozen=True)
class CapabilitySet:
    capabilities: Tuple[Capability, ...] = field(default_factory=tuple)

    def contains(self, name: str) -> bool:
        return any(c.name == name for c in self.capabilities)

    def get(self, name: str) -> Optional[Capability]:
        for c in self.capabilities:
            if c.name == name:
                return c
        return None

    @property
    def names(self) -> Tuple[str, ...]:
        return tuple(c.name for c in self.capabilities)

    @property
    def high_risk(self) -> Tuple[Capability, ...]:
        return tuple(c for c in self.capabilities if c.risk_level == "high")

    @property
    def requires_approval(self) -> Tuple[Capability, ...]:
        return tuple(c for c in self.capabilities if c.requires_approval)

    @staticmethod
    def all_builtin() -> "CapabilitySet":
        return CapabilitySet(
            capabilities=tuple(Capability.builtin(n) for n in BUILTIN_CAPABILITIES)
        )


@dataclass(frozen=True)
class CapabilityReport:
    total: int = 0
    low_risk: int = 0
    medium_risk: int = 0
    high_risk: int = 0
    requires_approval: int = 0
    requires_guardian: int = 0
    names: Tuple[str, ...] = field(default_factory=tuple)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def from_set(cs: CapabilitySet) -> "CapabilityReport":
        caps = cs.capabilities
        return CapabilityReport(
            total=len(caps),
            low_risk=sum(1 for c in caps if c.risk_level == "low"),
            medium_risk=sum(1 for c in caps if c.risk_level == "medium"),
            high_risk=sum(1 for c in caps if c.risk_level == "high"),
            requires_approval=sum(1 for c in caps if c.requires_approval),
            requires_guardian=sum(1 for c in caps if c.requires_guardian),
            names=cs.names,
        )


class CapabilityMatcher:
    """Matches capabilities against connector declarations."""

    @staticmethod
    def match_required(
        declared: CapabilitySet, required: Tuple[str, ...]
    ) -> Tuple[str, ...]:
        missing: List[str] = []
        for req in required:
            if not declared.contains(req):
                missing.append(req)
        return tuple(missing)

    @staticmethod
    def match_any(
        declared: CapabilitySet, candidates: Tuple[str, ...]
    ) -> Tuple[str, ...]:
        return tuple(c for c in candidates if declared.contains(c))

    @staticmethod
    def match_risk_threshold(
        declared: CapabilitySet, max_risk: str
    ) -> Tuple[str, ...]:
        risk_order = {"low": 0, "medium": 1, "high": 2}
        max_val = risk_order.get(max_risk, 0)
        exceeding: List[str] = []
        for c in declared.capabilities:
            if risk_order.get(c.risk_level, 0) > max_val:
                exceeding.append(c.name)
        return tuple(exceeding)

    @staticmethod
    def requires_approval_details(
        declared: CapabilitySet, action: str
    ) -> Tuple[bool, bool]:
        cap = declared.get(action)
        if cap is None:
            return (True, False)
        return (cap.requires_approval, cap.requires_guardian)
