"""Kernel Reporter — laporan akhir kernel."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.kernel_final import KernelFinalReport


class KernelReporter:
    """Pembuat laporan kernel — preview-only."""

    def generate_final_report(self, report_id: str, version: str,
                              components: List[str] = None,
                              metrics: Dict[str, int] = None) -> KernelFinalReport:
        return KernelFinalReport(
            report_id=report_id,
            version=version,
            status="complete",
            components=components or [],
            metrics=metrics or {},
        )

    def count(self, reports: List[KernelFinalReport]) -> int:
        return len(reports)
