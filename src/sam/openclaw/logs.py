"""
OpenClaw Log Analyzer — Phase 1

Membaca dan menganalisis log OpenClaw untuk mendeteksi issue.
"""

import re
import structlog
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = structlog.get_logger()


class OpenClawLogAnalyzer:
    """Analyzer untuk log OpenClaw — ekstraksi issue dan pattern."""

    SEVERITY_PATTERNS = {
        "CRITICAL": re.compile(r"\bCRITICAL\b", re.IGNORECASE),
        "ERROR": re.compile(r"\bERROR\b", re.IGNORECASE),
        "WARNING": re.compile(r"\bWARNING\b", re.IGNORECASE),
        "FATAL": re.compile(r"\bFATAL\b", re.IGNORECASE),
    }
    TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")

    def __init__(self, workspace_path: str = "./"):
        self.workspace_path = Path(workspace_path)
        # Cek beberapa kemungkinan lokasi log
        self._log_candidates = [
            self.workspace_path / "logs" / "openclaw.log",
            self.workspace_path / "openclaw.log",
            self.workspace_path / ".openclaw" / "logs" / "runtime.log",
            self.workspace_path / "log" / "openclaw.log",
        ]

    async def analyze(self, lines: int = 100) -> List[Dict[str, Any]]:
        """Analisis log OpenClaw.

        Args:
            lines: Jumlah baris terakhir yang dianalisis (default 100).

        Returns:
            List issue yang terdeteksi (error, warning, critical).
        """
        log_file = self._find_log_file()

        if not log_file:
            return [
                {
                    "type": "info",
                    "severity": "info",
                    "message": "OpenClaw log file not found in any known location",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ]

        return self._parse_log(log_file, lines)

    def _find_log_file(self) -> Optional[Path]:
        """Cari file log OpenClaw."""
        for candidate in self._log_candidates:
            if candidate.exists():
                logger.info("openclaw_log_found", path=str(candidate))
                return candidate

        # Fallback: scan for any .log file in workspace/logs
        logs_dir = self.workspace_path / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return log_files[0]

        return None

    def _parse_log(self, log_file: Path, max_lines: int) -> List[Dict[str, Any]]:
        """Parse file log dan ekstrak issue.

        Args:
            log_file: Path ke file log.
            max_lines: Maksimal baris yang dianalisis.

        Returns:
            List issue yang terdeteksi.
        """
        issues = []
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Ambil N baris terakhir
            last_lines = lines[-max_lines:]

            for line_num, line in enumerate(last_lines, start=1):
                severity = self._detect_severity(line)
                if severity:
                    timestamp = self._extract_timestamp(line)
                    issues.append({
                        "type": severity.lower(),
                        "severity": severity,
                        "message": line.strip()[:500],
                        "timestamp": timestamp,
                        "line": len(lines) - max_lines + line_num,
                    })

            logger.info(
                "openclaw_log_analysis_complete",
                file=str(log_file),
                total_lines=len(lines),
                issues_found=len(issues),
            )

        except IOError as e:
            logger.error("openclaw_log_read_failed", error=str(e))
            issues.append({
                "type": "error",
                "severity": "ERROR",
                "message": "Failed to read log: {0}".format(e),
                "timestamp": datetime.utcnow().isoformat(),
            })

        return issues

    def _detect_severity(self, line: str) -> Optional[str]:
        """Deteksi severity dari baris log."""
        for severity, pattern in self.SEVERITY_PATTERNS.items():
            if pattern.search(line):
                return severity
        return None

    def _extract_timestamp(self, line: str) -> str:
        """Ekstrak timestamp dari baris log."""
        match = self.TIMESTAMP_PATTERN.search(line)
        return match.group(0) if match else ""
