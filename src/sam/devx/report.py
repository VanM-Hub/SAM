"""Developer Experience - installation report builder.

Menyusun laporan instalasi (text & dict) dari hasil bootstrap untuk
ditampilkan ke pengguna (installation report / diagnostics output).
"""

from __future__ import annotations

from typing import Dict, List

from .state import DependencyCheck, InstallPhase, InstallationReport


__all__ = ["InstallationReportBuilder"]


class InstallationReportBuilder:
    """Membangun ringkasan & representasi teks laporan instalasi."""

    def build_summary(self, report: InstallationReport) -> Dict[str, str]:
        summary: Dict[str, str] = {}
        summary["status"] = "success" if report.success else "failed"
        summary["phases_run"] = str(len(report.phases_run))
        summary["steps_ok"] = str(report.ok_steps)
        summary["steps_total"] = str(len(report.steps))
        summary["blocking_deps"] = str(len(report.blocking_dependencies_failed))
        summary["component_failures"] = str(len(report.component_failures))
        report.summary = summary
        return summary

    def to_text(self, report: InstallationReport) -> str:
        lines: List[str] = []
        lines.append("=== SAM Bootstrap Installation Report ===")
        lines.append("Status: {0}".format("OK" if report.success else "FAILED"))
        for s in report.steps:
            marker = "OK  " if s.ok else "FAIL"
            flag = " [blocking]" if s.blocking else ""
            lines.append("  [{0}] {1}{2}: {3}".format(marker, s.phase.value, flag, s.message))
            if s.detail:
                lines.append("       -> {0}".format(s.detail))
        if report.dependency_checks:
            lines.append("Dependencies:")
            for d in report.dependency_checks:
                lines.append("  - {0}: {1} {2}".format(d.name, d.status.value, d.message))
        if report.component_checks:
            lines.append("Environment:")
            for c in report.component_checks:
                lines.append("  - {0}: {1} {2}".format(c.component, c.status.value, c.message or c.status.value))
        for key, values in report.diagnostics.items():
            lines.append("Diagnostics[{0}]: {1}".format(key, "; ".join(values)))
        return "\n".join(lines)

    def to_dict(self, report: InstallationReport) -> Dict[str, object]:
        return {
            "success": report.success,
            "summary": dict(report.summary),
            "phases_run": [p.value for p in report.phases_run],
            "steps": [
                {
                    "phase": s.phase.value,
                    "ok": s.ok,
                    "blocking": s.blocking,
                    "message": s.message,
                }
                for s in report.steps
            ],
            "dependencies": [
                {
                    "name": d.name,
                    "status": d.status.value,
                    "blocking": d.is_blocking,
                    "message": d.message,
                }
                for d in report.dependency_checks
            ],
            "environment": [
                {
                    "component": c.component,
                    "status": c.status.value,
                    "message": c.message,
                }
                for c in report.component_checks
            ],
            "diagnostics": report.diagnostics,
        }
