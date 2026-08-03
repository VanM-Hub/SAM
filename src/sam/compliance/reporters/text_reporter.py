"""Text reporter — formats ComplianceReport as plain text per P1-001 §6.4."""

from __future__ import annotations

from typing import List

from ..models.report import ComplianceReport
from ..models.finding import ComplianceFinding
from ..models.severity import Severity
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory


_SEPARATOR = "=" * 43
_SUBSEPARATOR = "-" * 43


class TextReporter:
    """Formats a ComplianceReport as plain text.

    Output matches the format defined in P1-001 §6.4.
    """

    @staticmethod
    def format(report: ComplianceReport) -> str:
        """Format a ComplianceReport as a plain text string."""
        lines: List[str] = []

        # Header
        lines.append(_SEPARATOR)
        lines.append("  RUNTIME COMPLIANCE REPORT")
        lines.append(_SEPARATOR)
        lines.append("")
        lines.append("Runtime Identity:  %s" % report.runtime_identity)
        lines.append("Timestamp:         %s" % report.timestamp)
        lines.append("Baseline Ref:      %s" % report.baseline_ref)
        lines.append("Compliance Suite:  %s v1.0" % report.suite_version)
        lines.append("Session ID:        %s" % report.session_id)
        lines.append("Duration:          %.2fs" % report.duration_seconds)
        lines.append("")

        # Verdict
        lines.append(_SUBSEPARATOR)
        lines.append("  OVERALL VERDICT:  %s — %s" % (
            report.verdict.grade.value, report.verdict.label
        ))
        lines.append(_SUBSEPARATOR)
        lines.append("")

        # Level summary
        lines.append("Level Summary:")
        for lvl in ComplianceLevel.all_levels():
            key = lvl.value
            if key in report.level_summaries:
                ls = report.level_summaries[key]
                status = "PASSED" if ls.is_pass else "FAILED"
            else:
                status = "N/A"
                ls = None

            label = {
                "L0": "Structural",
                "L1": "Specification",
                "L2": "ADR",
                "L3": "Behavioral",
                "L4": "System",
            }.get(key, key)

            if ls:
                line = "  Level %s (%s):  %s  (%d/%d passed)" % (
                    key, label, status, ls.passed, ls.total_checks
                )
            else:
                line = "  Level %s (%s):  %s  (0 checks)" % (key, label, status)
            lines.append(line)

        lines.append("")

        # Findings summary
        lines.append(_SUBSEPARATOR)
        lines.append("  FINDINGS SUMMARY")
        lines.append(_SUBSEPARATOR)
        lines.append("CRITICAL:  %d" % report.verdict.critical_count)
        lines.append("MAJOR:     %d" % report.verdict.major_count)
        lines.append("MINOR:     %d" % report.verdict.minor_count)
        lines.append("INFO:      %d" % report.verdict.info_count)
        lines.append("")

        # Findings detail
        if report.findings:
            lines.append(_SUBSEPARATOR)
            lines.append("  FINDINGS DETAIL (%d total)" % len(report.findings))
            lines.append(_SUBSEPARATOR)
            for i, finding in enumerate(report.findings):
                check = None
                # Try to get check from category mapping
                lines.append("[Finding #%d]" % (i + 1))
                lines.append("  Check ID:      %s" % finding.check_id)
                lines.append("  Classification: %s" % finding.classification.value)
                lines.append("  Severity:      %s" % finding.severity.value)
                if finding.description:
                    lines.append("  Description:   %s" % finding.description)
                if finding.recommendation:
                    lines.append("  Recommendation: %s" % finding.recommendation)
                if finding.baseline_ref:
                    lines.append("  Baseline:      %s" % finding.baseline_ref)
                lines.append("")

        # Category summary
        lines.append(_SUBSEPARATOR)
        lines.append("  CATEGORY SUMMARY")
        lines.append(_SUBSEPARATOR)
        for cat in ComplianceCategory.all_categories():
            key = cat.value
            summary = report.category_summaries.get(key)
            if summary:
                total = summary.total_findings
                lines.append("%s:  %d findings (C=%d M=%d m=%d I=%d)" % (
                    key, total,
                    summary.critical_count,
                    summary.major_count,
                    summary.minor_count,
                    summary.info_count,
                ))
            else:
                lines.append("%s:  0 findings" % key)

        lines.append("")
        lines.append(_SUBSEPARATOR)
        lines.append("  REPORT COMPLETE")
        lines.append(_SUBSEPARATOR)

        return "\n".join(lines)
