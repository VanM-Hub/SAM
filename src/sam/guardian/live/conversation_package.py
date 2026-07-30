"""
Guardian Live Conversation Package Bridge.

10 DTO-only query methods for decision package.
"""

from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime
from .decision_package import DecisionPackage

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationPackageBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
    @property
    def query_count(self) -> int: return 10

    def latest_package(self) -> Dict[str,Any]:
        l = self._runtime.package_registry.latest
        return {"query":"latest_package","has_package":l is not None,"package":l.to_dict() if l else None}

    def package_history(self, limit:int=50) -> Dict[str,Any]:
        h = self._runtime.package_registry.history(limit)
        return {"query":"package_history","total":self._runtime.package_registry.count,"returned":len(h),"packages":[p.to_dict() for p in h]}

    def package_summary(self) -> Dict[str,Any]:
        return {"query":"package_summary","summary":self._runtime.package_registry.get_summary().to_dict()}

    def package_metadata(self) -> Dict[str,Any]:
        l = self._runtime.package_registry.latest
        return {"query":"package_metadata","metadata":l.metadata.to_dict() if l and l.metadata else {}}

    def package_validation(self) -> Dict[str,Any]:
        from .package_validator import PackageValidator
        l = self._runtime.package_registry.latest
        if not l: return {"query":"package_validation","valid":True}
        r = PackageValidator().validate(l)
        return {"query":"package_validation","result":r.to_dict()}

    def package_statistics(self) -> Dict[str,Any]:
        s = self._runtime.package_registry.get_statistics()
        return {"query":"package_statistics","statistics":s.to_dict()}

    def package_version(self) -> Dict[str,Any]:
        l = self._runtime.package_registry.latest
        v = l.metadata.version if l and l.metadata else "none"
        return {"query":"package_version","version":v}

    def latest_justification(self) -> Dict[str,Any]:
        l = self._runtime.package_registry.latest
        just = l.sections.get("justification",{}) if l else {}
        return {"query":"latest_justification","has_justification":bool(just),"justification":just}

    def latest_handoff(self) -> Dict[str,Any]:
        l = self._runtime.package_registry.latest
        di = l.sections.get("decision_input",{}) if l else {}
        return {"query":"latest_handoff","has_handoff":bool(di),"handoff":di}

    def overall_package(self) -> Dict[str,Any]:
        l = self._runtime.package_registry.latest
        if not l: return {"query":"overall_package","has_package":False}
        return {"query":"overall_package","has_package":True,"summary":self._runtime.package_registry.get_summary().to_dict(),
                "metadata":l.metadata.to_dict() if l.metadata else {},"total_sections":l.total_sections}
