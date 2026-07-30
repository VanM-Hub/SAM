"""
Guardian Package Registry.

Ring buffer for DecisionPackage history.
No persistence. In-memory only.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
import uuid

from .decision_package import DecisionPackage, PackageStatistics, PackageSnapshot, PackageVersion, PackageSummary


class PackageRegistry:
    """Ring buffer for DecisionPackage history."""

    def __init__(self, max_size: int = 200) -> None:
        self._max_size = max_size
        self._packages: List[DecisionPackage] = []

    def register(self, package: DecisionPackage) -> None:
        self._packages.append(package)
        if len(self._packages) > self._max_size:
            self._packages.pop(0)

    @property
    def latest(self) -> Optional[DecisionPackage]:
        return self._packages[-1] if self._packages else None

    @property
    def count(self) -> int:
        return len(self._packages)

    def history(self, limit: int = 50) -> List[DecisionPackage]:
        return self._packages[-limit:] if limit > 0 else list(self._packages)

    def lookup(self, package_id: str) -> Optional[DecisionPackage]:
        for p in reversed(self._packages):
            if p.package_id == package_id:
                return p
        return None

    def get_statistics(self) -> PackageStatistics:
        by_version: Dict[str, int] = defaultdict(int)
        total_sec = 0
        for p in self._packages:
            v = p.metadata.version if p.metadata else "unknown"
            by_version[v] += 1
            total_sec += p.total_sections
        avg = round(total_sec / len(self._packages), 2) if self._packages else 0.0
        return PackageStatistics(total=len(self._packages), by_version=dict(by_version),
                                 average_sections=avg, total_sections=total_sec)

    def create_snapshot(self) -> PackageSnapshot:
        stats = self.get_statistics()
        return PackageSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            total_packages=self.count,
            packages=list(self._packages[-20:]),
            statistics=stats,
        )

    def get_summary(self) -> PackageSummary:
        l = self.latest
        return PackageSummary(
            total=self.count,
            latest_package_id=l.package_id if l else "",
            total_sections=sum(p.total_sections for p in self._packages),
            versions=list(set(p.metadata.version for p in self._packages if p.metadata)),
            latest_timestamp=l.metadata.created_at if l and l.metadata else 0.0,
        )

    def clear(self) -> None:
        self._packages.clear()
