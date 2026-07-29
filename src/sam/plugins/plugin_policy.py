# OP-414 — Plugin Policy Engine
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass(frozen=True)
class PluginPolicyResult:
    approved: bool = True
    violations: Tuple[str, ...] = field(default_factory=tuple)
    details: str = ""
    @property
    def has_violations(self): return len(self.violations) > 0

BUILTIN_PLUGIN_POLICIES = (
    "read_only","approval_required","trusted_plugin","sandbox",
    "version_match","dependency_valid","safe_mode","permission_scope","audit_required",
)


class PluginPolicyEngine:
    def __init__(self):
        self._policies: Dict[str, Dict[str, Any]] = {
            "read_only": {"enabled": True, "block_write": True},
            "approval_required": {"enabled": True, "auto_approve_readonly": True},
            "trusted_plugin": {"enabled": False, "trusted_ids": []},
            "sandbox": {"enabled": False},
            "version_match": {"enabled": True, "min_version": "4.0.0"},
            "dependency_valid": {"enabled": True},
            "safe_mode": {"enabled": False},
            "permission_scope": {"enabled": True, "scope": "default"},
            "audit_required": {"enabled": True},
        }

    def get_policy(self, name: str) -> Optional[Dict[str, Any]]: return self._policies.get(name)
    def set_policy(self, name: str, params: Dict[str, Any]) -> bool:
        p = self._policies.get(name)
        if p is None: return False; p.update(params); return True
    def list_policies(self) -> Dict[str, Dict[str, Any]]: return dict(self._policies)

    def evaluate(self, plugin_name: str = "", action: str = "",
                 read_only: bool = True, risk_level: str = "low",
                 healthy: bool = True, enabled: bool = True) -> PluginPolicyResult:
        violations: List[str] = []

        ro = self._policies.get("read_only", {})
        if ro.get("enabled") and ro.get("block_write") and action in ("write","create","delete","execute"):
            violations.append("Read-only: write operations blocked")

        ap = self._policies.get("approval_required", {})
        if ap.get("enabled") and not ap.get("auto_approve_readonly") and read_only:
            pass
        elif ap.get("enabled") and not read_only:
            violations.append(f"Plugin '{plugin_name}' requires approval for non-readonly operation")

        tr = self._policies.get("trusted_plugin", {})
        trusted = tr.get("trusted_ids", [])
        if tr.get("enabled") and trusted and plugin_name not in trusted:
            violations.append(f"Plugin '{plugin_name}' not trusted")

        sm = self._policies.get("safe_mode", {})
        if sm.get("enabled") and action in ("write","create","delete","execute"):
            violations.append("Safe mode: write operations blocked")

        dv = self._policies.get("dependency_valid", {})
        if dv.get("enabled") and not enabled:
            violations.append(f"Plugin '{plugin_name}' is disabled")

        return PluginPolicyResult(approved=len(violations)==0, violations=tuple(violations),
            details=f"Evaluated {len(self._policies)} policies")
