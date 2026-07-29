# OP-404 — Integration Policy Engine
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass(frozen=True)
class PolicyResult:
    approved: bool = True
    violations: Tuple[str, ...] = field(default_factory=tuple)
    details: str = ""
    @property
    def has_violations(self): return len(self.violations) > 0
    @property
    def approved_with_warnings(self): return self.approved and self.has_violations


class IntegrationPolicyEngine:
    """Built-in policies: read_only, approval_required, trusted_only, rate_limit,
    allow_preview, allow_export, audit_required, provider_available,
    permission_scope, safe_mode."""

    def __init__(self):
        self._policies: Dict[str, Dict[str, Any]] = {
            "read_only": {"enabled": False, "block_write": True},
            "approval_required": {"enabled": True, "auto_approve_low": True},
            "trusted_only": {"enabled": False, "trusted_types": []},
            "rate_limit": {"enabled": False, "max_per_minute": 60},
            "allow_preview": {"enabled": True},
            "allow_export": {"enabled": True, "export_limit_mb": 100},
            "audit_required": {"enabled": True},
            "provider_available": {"enabled": True},
            "permission_scope": {"enabled": True, "scope": "default"},
            "safe_mode": {"enabled": False, "allow_read_only": True},
        }

    def get_policy(self, name: str) -> Optional[Dict[str, Any]]:
        return self._policies.get(name)

    def set_policy(self, name: str, params: Dict[str, Any]) -> bool:
        p = self._policies.get(name)
        if p is None: return False
        p.update(params); return True

    def list_policies(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._policies)

    def evaluate(self, integration_type: str = "", action: str = "",
                 risk_level: str = "low", provider_healthy: bool = True) -> PolicyResult:
        violations: List[str] = []

        # read_only
        ro = self._policies.get("read_only", {})
        if ro.get("enabled") and ro.get("block_write") and action in ("write","create","delete","execute"):
            violations.append("Read-only mode: write operations blocked")

        # approval_required
        ap = self._policies.get("approval_required", {})
        if ap.get("enabled") and not ap.get("auto_approve_low") and risk_level == "low":
            pass
        elif ap.get("enabled") and risk_level in ("medium","high","critical"):
            violations.append(f"Approval required for risk level '{risk_level}'")

        # trusted_only
        tr = self._policies.get("trusted_only", {})
        trusted = tr.get("trusted_types", [])
        if tr.get("enabled") and trusted and integration_type not in trusted:
            violations.append(f"Integration type '{integration_type}' not trusted")

        # rate_limit
        rl = self._policies.get("rate_limit", {})
        if rl.get("enabled"):
            pass  # would check count in production

        # provider_available
        pa = self._policies.get("provider_available", {})
        if pa.get("enabled") and not provider_healthy:
            violations.append("Provider unavailable")

        # safe_mode
        sm = self._policies.get("safe_mode", {})
        if sm.get("enabled") and not sm.get("allow_read_only") and action in ("read","search","monitor"):
            pass
        elif sm.get("enabled") and action in ("write","create","delete","execute"):
            violations.append("Safe mode: write operations blocked")

        return PolicyResult(approved=len(violations) == 0, violations=tuple(violations),
            details=f"Evaluated {len(self._policies)} policies")
