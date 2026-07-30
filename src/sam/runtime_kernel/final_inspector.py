"""Final Inspector — inspeksi akhir."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.kernel_final import ComponentHealth, KernelSummary, FinalVerdict


class FinalInspector:
    """Inspektor akhir — preview-only."""

    KERNEL_COMPONENTS = [
        "context", "registry", "state", "lifecycle", "bridge",
        "health", "security", "scheduler", "event", "coordinator",
        "telemetry",
    ]

    def inspect_components(self) -> List[ComponentHealth]:
        return [
            ComponentHealth(c, True, f"{c} ready")
            for c in self.KERNEL_COMPONENTS
        ]

    def generate_summary(self) -> KernelSummary:
        components = self.inspect_components()
        return KernelSummary(
            summary_id="ks_001",
            total_components=len(components),
            healthy_count=sum(1 for c in components if c.healthy),
            version="10.0.0-alpha.111",
        )

    def final_verdict(self, verdict_id: str) -> FinalVerdict:
        summary = self.generate_summary()
        ready = summary.healthy_count == summary.total_components
        return FinalVerdict(
            verdict_id=verdict_id,
            ready=ready,
            reason="All components healthy" if ready else "Some components unhealthy",
        )

    def count_components(self) -> int:
        return len(self.KERNEL_COMPONENTS)

    def list_components(self) -> List[str]:
        return list(self.KERNEL_COMPONENTS)
