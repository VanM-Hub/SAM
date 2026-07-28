"""
OP-255 — Mission Orchestrator.

Groups related recommendations into operational packages.

Each OperationalPackage:
  - unique package ID
  - title + description (auto-generated from contents)
  - list of contained recommendation/proposal IDs
  - combined priority score (max of members)
  - dependency graph within package
  - submission strategy: "sequential" | "parallel" | "any"

Orchestrator provides:
  - group_by_source: group recs sharing affected resources
  - group_by_priority: group recs by priority band
  - group_by_type: group recs by recommendation type
  - auto_package: smart grouping that combines all approaches
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class OperationalPackage:
    """A group of related recommendations/proposals."""

    package_id: str
    title: str
    description: str
    member_ids: List[str]
    member_priorities: List[str]
    combined_score: float  # max priority score of all members
    combined_priority: str
    strategy: str  # "sequential" | "parallel" | "any"
    dependencies: Dict[str, List[str]]  # member_id -> depends on
    source_summary: Dict[str, int]  # source -> count
    affected_resources: Set[str]


@dataclass
class OrchestratorConfig:
    """Configuration for auto-packaging behavior."""

    max_package_size: int = 5
    min_affected_overlap: float = 0.3  # 30% resource overlap required
    same_priority_group: bool = True
    separate_critical: bool = True  # critical recs get own package


# ── Orchestrator ───────────────────────────────────────────────────


class MissionOrchestrator:
    """
    Groups recommendations into operational packages.

    Input: list of recommendation dicts (or score dicts).
    Output: list of OperationalPackage.
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self._config = config or OrchestratorConfig()
        self._last_packages: List[OperationalPackage] = []

    # ── Public API ─────────────────────────────────────────────────

    @property
    def config(self) -> OrchestratorConfig:
        return self._config

    @property
    def last_packages(self) -> List[OperationalPackage]:
        return self._last_packages

    def group_by_source(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[OperationalPackage]:
        """Group by shared affected resources."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for rec in recommendations:
            resources = rec.get("affected_resources", rec.get("affected_sources", []))
            for res in resources:
                if res not in grouped:
                    grouped[res] = []
                grouped[res].append(rec)

        packages = []
        for resource, recs in grouped.items():
            package = self._build_package(
                recs, f"Resource: {resource}", strategy="sequential"
            )
            packages.append(package)
            self._last_packages = packages
        return packages

    def group_by_priority(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[OperationalPackage]:
        """Group by priority band."""
        bands = {"critical": "Critical Issues", "high": "High Priority",
                 "medium": "Medium Priority", "low": "Low Priority"}

        packages = []
        for priority, title in bands.items():
            recs = [
                r for r in recommendations
                if r.get("priority", "low") == priority
            ]
            if recs:
                package = self._build_package(
                    recs, title, strategy="parallel"
                )
                packages.append(package)
        self._last_packages = packages
        return packages

    def group_by_type(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[OperationalPackage]:
        """Group by recommendation type/source finding."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for rec in recommendations:
            stype = rec.get("source_finding_id", rec.get("finding_type", "other"))
            if stype not in grouped:
                grouped[stype] = []
            grouped[stype].append(rec)

        packages = []
        for rtype, recs in grouped.items():
            package = self._build_package(
                recs, f"Type: {rtype}", strategy="sequential"
            )
            packages.append(package)
        self._last_packages = packages
        return packages

    def auto_package(
        self,
        recommendations: List[Dict[str, Any]],
        priority_scores: Optional[List[Dict[str, Any]]] = None,
    ) -> List[OperationalPackage]:
        """
        Smart grouping: combines source, priority, and type grouping.

        Algorithm:
          1. Separate critical recs (each gets own package)
          2. Group remaining by shared affected resources
          3. Sub-group by priority band
          4. Merge any remaining singletons into a "Misc" package
        """
        packages: List[OperationalPackage] = []

        # Score lookup if provided
        score_map: Dict[str, float] = {}
        if priority_scores:
            for ps in priority_scores:
                score_map[ps.get("item_id", "")] = ps.get("score", 0.5)

        # 1. Separate critical
        critical: List[Dict[str, Any]] = []
        others: List[Dict[str, Any]] = []
        for rec in recommendations:
            pid = score_map.get(
                rec.get("id", rec.get("recommendation_id", "")),
                0.5,
            )
            is_critical = (
                rec.get("priority") == "critical"
                or pid >= 0.8
            )
            if is_critical and self._config.separate_critical:
                critical.append(rec)
            else:
                others.append(rec)

        # Each critical becomes its own package
        for rec in critical:
            title = rec.get("title", "Critical Issue")
            package = self._build_package(
                [rec], f"[CRITICAL] {title}", strategy="any"
            )
            packages.append(package)

        # 2. Group remaining by resource overlap
        resource_groups: Dict[str, List[Dict[str, Any]]] = {}
        for rec in others:
            resources = rec.get(
                "affected_resources",
                rec.get("affected_sources", ["system"]),
            )
            # Find best matching group
            matched = self._find_matching_group(resource_groups, rec, resources)
            if matched:
                resource_groups[matched].append(rec)
            else:
                key = "_".join(resources) if resources else "system"
                if key not in resource_groups:
                    resource_groups[key] = []
                resource_groups[key].append(rec)

        # Build packages from groups
        for group_key, recs in resource_groups.items():
            if not recs:
                continue
            # Sub-group by priority band
            priority_order = ["critical", "high", "medium", "low"]
            for band in priority_order:
                band_recs = [r for r in recs
                             if r.get("priority", "low") == band]
                if band_recs:
                    title = f"Package: {group_key} ({band})"
                    package = self._build_package(
                        band_recs, title, strategy="sequential",
                    )
                    packages.append(package)

        # 3. Merge leftovers
        used_ids = {mid for p in packages for mid in p.member_ids}
        leftovers = [r for r in recommendations
                     if r.get("recommendation_id", r.get("id")) not in used_ids]
        if leftovers:
            package = self._build_package(
                leftovers, f"Maintenance ({len(leftovers)} items)",
                strategy="parallel",
            )
            packages.append(package)

        self._last_packages = packages
        return packages

    # ── Internal ───────────────────────────────────────────────────

    def _build_package(
        self,
        recs: List[Dict[str, Any]],
        title: str,
        strategy: str = "sequential",
    ) -> OperationalPackage:
        member_ids = []
        member_priorities = []
        all_resources: Set[str] = set()
        dependencies: Dict[str, List[str]] = {}
        source_count: Dict[str, int] = {}

        for i, rec in enumerate(recs):
            rec_id = rec.get("recommendation_id", rec.get("id", str(uuid.uuid4())))
            member_ids.append(rec_id)
            member_priorities.append(rec.get("priority", "low"))

            resources = rec.get(
                "affected_resources",
                rec.get("affected_sources", []),
            )
            for r in resources:
                all_resources.add(r)

            stype = rec.get("source_finding_id", rec.get("finding_type", "unknown"))
            source_count[stype] = source_count.get(stype, 0) + 1

            # Sequential: each item depends on previous
            if strategy == "sequential" and i > 0:
                dependencies[rec_id] = [member_ids[i - 1]]

        # Combined priority: max of members
        priority_values = {
            "critical": 4, "high": 3, "medium": 2, "low": 1,
        }
        max_pval = max(
            (priority_values.get(p, 0) for p in member_priorities),
            default=1,
        )
        rev = {4: "critical", 3: "high", 2: "medium", 1: "low"}
        combined_priority = rev.get(max_pval, "low")
        combined_score = max_pval / 4.0

        return OperationalPackage(
            package_id=f"pkg_{uuid.uuid4().hex[:8]}",
            title=title,
            description=f"Package containing {len(member_ids)} items: {', '.join(member_ids[:5])}",
            member_ids=member_ids,
            member_priorities=member_priorities,
            combined_score=combined_score,
            combined_priority=combined_priority,
            strategy=strategy,
            dependencies=dependencies,
            source_summary=source_count,
            affected_resources=all_resources,
        )

    def _find_matching_group(
        self,
        groups: Dict[str, List[Dict[str, Any]]],
        rec: Dict[str, Any],
        rec_resources: List[str],
    ) -> Optional[str]:
        """Find a group whose resources overlap >= threshold."""
        for group_key, group_recs in groups.items():
            if not group_recs:
                continue
            # Get resources of first item in group
            sample = group_recs[0]
            group_resources = set(
                sample.get("affected_resources", sample.get("affected_sources", []))
            )
            rec_set = set(rec_resources)
            if not group_resources or not rec_set:
                continue
            overlap = len(group_resources & rec_set) / max(
                len(group_resources | rec_set), 1
            )
            if overlap >= self._config.min_affected_overlap:
                return group_key
        return None


# ── Convenience ────────────────────────────────────────────────────


def auto_orchestrate(
    recommendations: List[Dict[str, Any]],
    priority_scores: Optional[List[Dict[str, Any]]] = None,
) -> List[OperationalPackage]:
    """One-shot: auto-package recommendations."""
    orchestrator = MissionOrchestrator()
    return orchestrator.auto_package(recommendations, priority_scores)
