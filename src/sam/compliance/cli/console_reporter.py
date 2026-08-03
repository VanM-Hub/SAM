"""ConsoleReporter — renders deterministic console output for the CLI.

The reporter format is stable and deterministic: given the same
session/report/listing it always produces identical text. It renders:

- run: summary, findings, verdict, statistics, execution duration
- list: table of checks
- info: full metadata for a single check
- summary: catalog/manifest statistics

All output is deterministic — no timestamps in body, no random order.
"""

from __future__ import annotations

from typing import List, Optional

from ..catalog.catalog import ComplianceCheckCatalog
from ..catalog.models import CheckMetadata
from ..manifest.manifest import ComplianceManifest
from .session_runner import SessionResult, SessionFilter


class ConsoleReporter:
    """Formats CLI output deterministically."""

    def __init__(self) -> None:
        pass

    # -- Run reporting --------------------------------------------------------

    def report_run(self, result: SessionResult) -> str:
        """Render the output of a 'compliance run' session."""
        report = result.report
        out = []
        out.append("Compliance Session")
        out.append("=" * 40)
        out.append("session_id      : %s" % result.session_id)
        out.append("started_at      : %s" % result.started_at)
        out.append("completed_at    : %s" % result.completed_at)
        out.append("executed_checks : %d" % result.executed_checks)
        out.append("skipped_checks  : %d" % result.skipped_checks)
        out.append("total_checks    : %d" % result.total_checks)
        out.append("")
        out.append(self._statistics(report))
        out.append("")
        out.append(self._findings(report))
        out.append("")
        out.append(self._verdict(report))
        out.append("")
        out.append("duration_seconds: %.4f" % report.duration_seconds)
        return "\n".join(out)

    def _statistics(self, report) -> str:
        """Render passed/failed/skipped statistics."""
        out = ["Statistics"]
        out.append("-" * 40)
        out.append("total_checks : %d" % report.total_checks)
        out.append("executed     : %d" % report.total_executed)
        out.append("passed       : %d" % report.total_passed)
        out.append("failed       : %d" % report.total_failed)
        out.append("skipped      : %d" % report.total_skipped)
        return "\n".join(out)

    def _findings(self, report) -> str:
        """Render findings (deviating only, in deterministic order)."""
        out = ["Findings"]
        out.append("-" * 40)
        deviating = [f for f in report.findings if f.is_deviating()]
        if not deviating:
            out.append("(none)")
            return "\n".join(out)
        for finding in deviating:
            out.append("%s %-8s %s" % (
                finding.check_id, finding.severity.value, finding.description))
        return "\n".join(out)

    def _verdict(self, report) -> str:
        """Render the final verdict line."""
        verdict = report.verdict
        grade = verdict.grade.value
        out = ["Verdict: %s (%s) [%s]" % (
            grade, verdict.label, _grade_word(grade))]
        out.append("critical: %d  major: %d  minor: %d  info: %d" % (
            verdict.critical_count, verdict.major_count,
            verdict.minor_count, verdict.info_count))
        return "\n".join(out)

    # -- List reporting -------------------------------------------------------

    def report_list(
        self,
        checks: List[CheckMetadata],
        check_filter: Optional[SessionFilter] = None,
    ) -> str:
        """Render a list of checks as a deterministic table."""
        out = []
        out.append("Compliance Checks (%d)" % len(checks))
        out.append("=" * 60)
        if check_filter and not check_filter.is_empty():
            out.append("filter: %s" % _filter_str(check_filter))
        out.append("%-8s %-8s %-14s %-24s %s" % (
            "ID", "Level", "Category", "Authority", "Name"))
        out.append("-" * 60)
        for c in checks:
            out.append("%-8s %-8s %-14s %-24s %s" % (
                c.check_id, c.level.value, c.category.value,
                c.authority.value, c.name))
        return "\n".join(out)

    # -- Info reporting -------------------------------------------------------

    def report_info(self, metadata: CheckMetadata, enabled: bool) -> str:
        """Render full metadata for a single check."""
        out = []
        out.append("Check: %s" % metadata.check_id)
        out.append("=" * 40)
        out.append("name            : %s" % metadata.name)
        out.append("level           : %s" % metadata.level.value)
        out.append("category        : %s" % metadata.category.value)
        out.append("severity        : %s" % metadata.severity.value)
        out.append("authority       : %s" % metadata.authority.value)
        out.append("evidence_type   : %s" % metadata.evidence_type.value)
        out.append("checker_class   : %s" % metadata.checker_class.value)
        out.append("expected_verdict: %s" % metadata.expected_verdict)
        out.append("source_document : %s" % metadata.source_document)
        out.append("baseline_ref    : %s" % metadata.baseline_ref)
        out.append("description     : %s" % metadata.description)
        out.append("recommendation  : %s" % (metadata.recommendation or "-"))
        out.append("tags            : %s" % (", ".join(metadata.tags) or "-"))
        out.append("manifest_status : %s" % ("enabled" if enabled else "disabled"))
        return "\n".join(out)

    # -- Summary reporting ----------------------------------------------------

    def report_summary(
        self,
        manifest: ComplianceManifest,
        catalog: ComplianceCheckCatalog,
    ) -> str:
        """Render catalog + manifest statistics."""
        out = []
        out.append("Compliance Summary")
        out.append("=" * 40)
        out.append("catalog_checks    : %d" % catalog.count)
        out.append("manifest_entries  : %d" % manifest.count())
        out.append("manifest_enabled  : %d" % len(manifest.enabled()))
        out.append("manifest_disabled : %d" % len(manifest.disabled()))
        out.append("")
        out.append("By Level")
        out.append("-" * 40)
        for level, count in sorted(catalog.level_distribution().items()):
            out.append("  %-4s : %d" % (level, count))
        out.append("")
        out.append("By Authority")
        out.append("-" * 40)
        for auth, count in sorted(catalog.authority_distribution().items()):
            out.append("  %-14s : %d" % (auth, count))
        return "\n".join(out)


def _grade_word(grade: str) -> str:
    mapping = {
        "A": "CERTIFIED",
        "B": "MINOR FINDING",
        "C": "MAJOR FINDING",
        "D": "NOT COMPLIANT",
    }
    return mapping.get(grade, grade)


def _filter_str(check_filter: SessionFilter) -> str:
    parts = []
    if check_filter.check_id:
        parts.append("check=%s" % check_filter.check_id)
    if check_filter.level:
        parts.append("level=%s" % check_filter.level)
    if check_filter.category:
        parts.append("category=%s" % check_filter.category)
    if check_filter.authority:
        parts.append("authority=%s" % check_filter.authority)
    if check_filter.tag:
        parts.append("tag=%s" % check_filter.tag)
    return ", ".join(parts) or "(all)"
