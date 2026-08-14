"""Environment-adaptive: alur orkestrasi (DISCOVERY -> VERIFICATION).

Pipeline menghubungkan seluruh tahap TANPA asumsi jenis aplikasi:
  DISCOVERY -> IDENTIFICATION (candidate ward dari graph) -> OBSERVATION
  -> INVESTIGATION -> DIAGNOSIS -> AUTHORITY (delegated) -> EXECUTION
  (canonical) -> VERIFICATION -> LEARN (tanpa authority baru).

Capability providers (fixture: word/pdf/openclaw/github) DIDAFTARKAN ke
registry sebagai probe observasi TAMBAHAN, bukan sebagai katalog yang SAM
andalkan. Ward dipilih dari EVALUASI ENTITY (health/evidence), bukan dari
nama aplikasi.

Jika tidak ada entitas yang benar-benar perlu perhatian -> SAM jujur
"environment tampak sehat / tidak ada perbaikan perlu" (BUKAN mengarang
masalah).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sam.environment.confidence import (
    ConfidenceAssessor,
    Evidence,
)
from sam.environment.diagnosis import DiagnosisEngine, Hypothesis
from sam.environment.discovery import EnvironmentDiscovery
from sam.environment.entity import DiscoveryScan, Entity, EntityKind
from sam.environment.graph import EntityGraph
from sam.environment.providers import CapabilityProvider, ProviderRegistry
from sam.environment.remediation import (
    RemediationCandidate,
    RemediationPlanner,
)


@dataclass
class WardCandidate:
    """Kandidat ward = entitas yang layak diobservasi lebih lanjut.

    Dipilih dari graph & fakta health (BUKAN nama aplikasi):
      - process dengan health != ok
      - port tanpa process terikat
      - file dengan signature tidak valid
      - entitas yang punya banyak relasi (hub) di graph
    """

    entity: Entity
    reason: str
    priority: int  # lebih besar = lebih perlu perhatian

    def as_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity.as_dict(),
            "reason": self.reason,
            "priority": self.priority,
            "id": self.entity.id,
            "label": self.entity.label,
        }


@dataclass
class AdaptiveResult:
    """Hasil alur environment-adaptive (auditable, jujur)."""

    scan: Optional[DiscoveryScan] = None
    graph: Optional[EntityGraph] = None
    candidates: List[WardCandidate] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    remediation: List[RemediationCandidate] = field(default_factory=list)
    verdicts: Dict[str, str] = field(default_factory=dict)
    final_verdict: str = ""   # jujur: operational_permission_ok / no_action / escalate / blocked
    evidence: List[Evidence] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "candidates": [c.as_dict() for c in self.candidates],
            "hypotheses": [h.as_dict() for h in self.hypotheses],
            "remediation": [r.as_dict() for r in self.remediation],
            "verdicts": self.verdicts,
            "final_verdict": self.final_verdict,
            "evidence": [e.as_dict() for e in self.evidence],
        }


class AdaptiveEnvironmentPipeline:
    """Orkestrasi alur environment-adaptive.

    Providers: probe observasi tambahan terdaftar di registry. Optional.
    capacity: daftar capability remediation yang tersedia (execute_fn).
    """

    def __init__(
        self,
        discovery: Optional[EnvironmentDiscovery] = None,
        engine: Optional[DiagnosisEngine] = None,
        planner: Optional[RemediationPlanner] = None,
        assessor: Optional[ConfidenceAssessor] = None,
        registry: Optional[ProviderRegistry] = None,
    ) -> None:
        self._discovery = discovery or EnvironmentDiscovery()
        self._engine = engine or DiagnosisEngine()
        self._assessor = assessor or ConfidenceAssessor()
        self._planner = planner or RemediationPlanner()
        # registry provider (instance; TIDAK wajib). Provider hanya menambah
        # observasi bila didaftarkan; mesin generic tetap jalan tanpa itu.
        self._registry = registry or ProviderRegistry()
        # registry probe tambahan (fixture): name -> (entity_kind, callable)
        self._extra_probes: Dict[str, Callable[[], List[Evidence]]] = {}
        self._extra_evidence: Dict[str, List[Evidence]] = {}

    # --- registry provider (instance) ---

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    def register_provider(self, provider: CapabilityProvider) -> None:
        """Daftarkan satu capability provider (instance) sbg observasi tambahan.

        Provider TIDAK mengganti mesin generic; ia menambah source evidence
        observasi. Mesin generic tetap discovery/graph/diagnosis mandiri.
        """
        self._registry.register(provider)

    # --- daftarkan capability remediation (fixture) ---

    def register_remediation(self, capability: str,
                             fn: Optional[Callable[..., Any]]) -> None:
        self._planner.register(capability, fn)

    # --- daftarkan probe observasi tambahan (fixture; tidak wajib) ---

    def register_observation(self, name: str,
                             probe: Callable[[], List[Evidence]]) -> None:
        self._extra_probes[name] = probe

    # --- alur ---

    def run(self, candidate_limit: int = 8) -> AdaptiveResult:
        result = AdaptiveResult()
        # 1. DISCOVERY (generik, multi-sumber, jujur per-sumber)
        scan = self._discovery.discover()
        result.scan = scan

        # 2. IDENTIFICATION: bangun graph
        graph = EntityGraph.from_scan(scan.entities)
        result.graph = graph

        # 3. Candidate ward dari graph/fakta health (BUKAN nama aplikasi)
        candidates = self._select_candidates(scan.entities, graph)
        candidates.sort(key=lambda c: c.priority, reverse=True)
        result.candidates = candidates[:candidate_limit]

        # 3b. kumpulkan evidence tambahan dari provider (observation)
        for name, probe in self._extra_probes.items():
            try:
                ev = probe()
                self._extra_evidence[name] = ev
                result.evidence.extend(ev)
            except Exception:
                self._extra_evidence[name] = [Evidence(
                    name, "observation source failed - skipped",
                    strength=0.0)]
                result.evidence.append(Evidence(
                    name, "observation source failed - skipped", strength=0.0))

        # 3c. observasi dari provider instance (registry) - HANYA bila ada
        for provider in self._registry.all():
            obs = provider.observe()
            result.evidence.extend(obs.evidence)
            # simpan hasil observasi provider sbg fakta pipeline (auditable)
            result.verdicts[f"provider:{provider.name}"] = (
                "ok" if obs.ok else "failed")
            result.verdicts[f"provider:{provider.name}:evidence"] = str(
                len(obs.evidence))

        # Jika tidak ada kandidat -> jujur "no_action" (jangan mengarang)
        if not candidates:
            result.final_verdict = "no_action"
            result.verdicts["status"] = (
                "environment tampak sehat / tidak ada perbaikan diperlukan")
            return result

        # 4. INVESTIGATION + DIAGNOSIS per kandidat (tidak mengasumsikan app)
        for cand in candidates:
            hyp = self._engine.investigate(cand.entity, graph)
            result.hypotheses.extend(hyp)
            for h in hyp:
                result.verdicts[cand.entity.id] = h.level.value

        # 5. AUTHORITY (delegated): hanya remediasi bila confident
        # 6. EXECUTION: hanya lewat canonical recovery (di luar pipeline ini);
        #    pipeline hanya MEMILIH kandidat remediation (bukan eksekusi)
        for cand in candidates:
            for h in result.hypotheses:
                if h.confident and cand.entity.id in result.verdicts:
                    plan = self._planner.plan(cand.entity, h, self._engine)
                    result.remediation.extend(plan)
                    if any(p.available for p in plan):
                        result.final_verdict = "operational_permission_ok"
                    break

        if not result.final_verdict:
            # ada kandidat tapi tak ada remediation confidence -> escalate jujur
            result.final_verdict = "escalate"
            result.verdicts["note"] = (
                "evidence tidak cukup utk remediasi otomatis - perlu manusia")
        return result

    # --- seleksi kandidat generik (tanpa nama aplikasi) ---

    def _select_candidates(self, entities: List[Entity],
                           graph: EntityGraph) -> List[WardCandidate]:
        out: List[WardCandidate] = []
        for e in entities:
            if e.kind == EntityKind.PROCESS:
                health = e.attributes.get("health", "ok")
                if health != "ok":
                    out.append(WardCandidate(
                        e, f"process status={health}", 70))
                else:
                    out.append(WardCandidate(e, "process present", 10))
            elif e.kind == EntityKind.PORT:
                pid = e.attributes.get("pid")
                if not pid:
                    out.append(WardCandidate(
                        e, "port without bound process", 60))
                else:
                    out.append(WardCandidate(e, "port bound", 10))
            elif e.kind == EntityKind.FILE:
                # file dengan signature invalid
                if e.attributes.get("valid_signature") is False:
                    out.append(WardCandidate(
                        e, "file signature invalid", 80))
        return out
