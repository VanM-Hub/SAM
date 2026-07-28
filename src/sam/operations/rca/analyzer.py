"""
RootCauseAnalyzer — evidence-based RCA.

Pipeline:
  Observation → Evidence Collection → Candidate Cause → Evidence Scoring → Confidence
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import RootCauseModel, CandidateCause, RootCauseEvidence, RootCauseReport

logger = structlog.get_logger()


# Thresholds untuk deteksi
CPU_HIGH_THRESHOLD = 80.0          # %
MEMORY_HIGH_THRESHOLD = 85.0       # %
QUEUE_GROWING_THRESHOLD = 5        # pending operations
QUEUE_HIGH_LATENCY_MS = 2000       # ms
DISK_NEAR_FULL_THRESHOLD = 85.0    # %
TEMPFILE_HIGH_THRESHOLD = 500      # count atau MB
UPTIME_LOW_THRESHOLD = 300         # detik (5 menit)


class RootCauseAnalyzer:
    """Menganalisis akar penyebab berbasis evidence real-time."""

    def __init__(self, runtime_provider=None, workspace_provider=None, telemetry_service=None):
        self._rp = runtime_provider
        self._wp = workspace_provider
        self._telemetry = telemetry_service

    def analyze(self, question: str, context: Optional[Dict[str, Any]] = None) -> RootCauseModel:
        """Analisis satu pertanyaan 'Why?' dengan evidence dari sumber yang tersedia.

        Args:
            question: Pertanyaan seperti "Why is CPU high?" atau "Why is queue growing?"
            context: Konteks tambahan (opsional)

        Returns:
            RootCauseModel — selalu berisi evidence, tanpa asumsi
        """
        ctx = context or {}
        model = RootCauseModel(
            question=question,
            observed_event=self._extract_observed_event(question, ctx),
        )

        # Kumpulkan evidence dari semua sumber
        if self._rp:
            runtime = self._rp.get_latest()
        else:
            runtime = None

        if self._wp:
            ws = self._wp.observe()
        else:
            ws = None

        # Kategorikan pertanyaan
        q_lower = question.lower()

        if "cpu" in q_lower:
            self._analyze_cpu(model, runtime, ws, ctx)
        elif "memory" in q_lower or "mem" in q_lower:
            self._analyze_memory(model, runtime, ws, ctx)
        elif "queue" in q_lower or "growing" in q_lower or "pending" in q_lower:
            self._analyze_queue(model, runtime, ws, ctx)
        elif "disk" in q_lower or "storage" in q_lower:
            self._analyze_disk(model, ws, ctx)
        elif "everything" in q_lower or "normal" in q_lower:
            self._analyze_normal(model, runtime, ws, ctx)
        else:
            # Unknown question — report apa yang tersedia
            self._analyze_general(model, runtime, ws, ctx)

        # Hitung overall confidence
        if model.possible_causes:
            model.confidence = max(c.confidence for c in model.possible_causes)
        else:
            model.confidence = 0.0
            model.missing_information.append("No candidate cause identified from available evidence.")

        # Recommended next observation
        if not model.possible_causes or model.confidence < 0.5:
            missing = []
            if not self._rp:
                missing.append("RuntimeProvider — CPU, memory, queue data")
            if not self._wp:
                missing.append("WorkspaceProvider — disk, cache, temp data")
            if not self._telemetry:
                missing.append("TelemetryService — historical event data")
            if missing:
                model.recommended_next_observation = missing

        logger.info("rca_completed",
            question=question,
            causes=len(model.possible_causes),
            confidence=model.confidence,
        )
        return model

    def to_report(self, model: RootCauseModel) -> RootCauseReport:
        """Konversi RootCauseModel ke RootCauseReport siap Conversation."""
        if not model.possible_causes:
            return RootCauseReport(
                summary="Insufficient evidence. Cannot determine root cause.",
                confidence=0.0,
                missing_observations=model.recommended_next_observation,
            )

        best = model.possible_causes[0]
        return RootCauseReport(
            summary="Root cause identified with {:.0f}% confidence.".format(best.confidence * 100),
            root_cause=best.hypothesis,
            confidence=best.confidence,
            supporting_evidence=[
                "{}: {} {} (threshold: {})".format(e.source, e.metric, e.value, e.threshold)
                for e in best.evidence[:5]
            ],
            missing_observations=best.missing_evidence,
        )

    def _extract_observed_event(self, question: str, ctx: Dict) -> str:
        """Ekstrak event yang diamati dari pertanyaan."""
        if not ctx:
            return question

        observed = ctx.get("observed_event", "")
        if observed:
            return observed

        # Default dari snapshot
        if self._rp:
            snap = self._rp.get_latest()
            if snap:
                return "CPU: {:.1f}% | Memory: {:.1f}% | Queue depth: {}".format(
                    snap.cpu_percent, snap.memory_percent, snap.queue_depth
                )
        return question

    def _analyze_cpu(self, model, runtime, ws, ctx):
        observed = runtime
        if not observed:
            model.missing_information.append("CPU data unavailable — RuntimeProvider not connected")
            model.recommended_next_observation.append("Connect RuntimeProvider for CPU data")
            return

        cpu = observed.cpu_percent
        cause = CandidateCause(
            hypothesis="CPU is high ({:.1f}%) because active operations are consuming resources.".format(cpu),
            confidence=0.0,
        )

        # Evidence 1: Nilai CPU
        cause.evidence.append(RootCauseEvidence(
            source="runtime_provider",
            metric="cpu_percent",
            value=cpu,
            threshold=CPU_HIGH_THRESHOLD,
            severity="warning" if cpu > CPU_HIGH_THRESHOLD else "normal",
            detail="CPU usage {:.1f}% vs threshold {:.0f}%".format(cpu, CPU_HIGH_THRESHOLD),
        ))

        # Evidence 2: Queue
        queue = observed.queue_depth
        active = observed.active_operations
        if queue > 0 or active > 0:
            cause.evidence.append(RootCauseEvidence(
                source="queue_monitor",
                metric="queue_depth",
                value=queue,
                threshold=QUEUE_GROWING_THRESHOLD,
                severity="warning" if queue > QUEUE_GROWING_THRESHOLD else "normal",
                detail="Queue depth {} ({} active)".format(queue, active),
            ))
            cause.hypothesis = "CPU is high ({:.1f}%) because queue has {} pending operations ({} active).".format(
                cpu, queue, active
            )

        # Evidence 3: Uptime (kalau baru restart, CPU wajar tinggi)
        uptime = observed.uptime_seconds
        if uptime < UPTIME_LOW_THRESHOLD:
            cause.evidence.append(RootCauseEvidence(
                source="runtime_provider",
                metric="uptime_seconds",
                value=uptime,
                threshold=UPTIME_LOW_THRESHOLD,
                severity="normal",
                detail="System recently started ({:.0f}s ago) — CPU spike expected".format(uptime),
            ))

        # Confidence
        if cpu > CPU_HIGH_THRESHOLD and queue > 0:
            cause.confidence = 0.85
        elif cpu > CPU_HIGH_THRESHOLD:
            cause.confidence = 0.65
            cause.missing_evidence.append(
                "Queue depth is 0 — insufficient evidence to link CPU to queue activity"
            )
            if not self._telemetry:
                cause.missing_evidence.append(
                    "Telemetry data unavailable — cannot check historical CPU trends"
                )
        else:
            cause.confidence = 0.3
            cause.hypothesis = "CPU is within normal range ({:.1f}%). No anomaly detected.".format(cpu)

        if cause.evidence:
            model.possible_causes.append(cause)

    def _analyze_memory(self, model, runtime, ws, ctx):
        observed = runtime
        if not observed:
            model.missing_information.append("Memory data unavailable — RuntimeProvider not connected")
            return

        mem = observed.memory_percent
        cause = CandidateCause(
            hypothesis="Memory usage at {:.1f}%.".format(mem),
            confidence=0.0,
        )

        cause.evidence.append(RootCauseEvidence(
            source="runtime_provider",
            metric="memory_percent",
            value=mem,
            threshold=MEMORY_HIGH_THRESHOLD,
            severity="warning" if mem > MEMORY_HIGH_THRESHOLD else "normal",
            detail="Memory {:.1f}% vs threshold {:.0f}%".format(mem, MEMORY_HIGH_THRESHOLD),
        ))

        # Korelasi queue
        if runtime.queue_depth > 0:
            cause.evidence.append(RootCauseEvidence(
                source="queue_monitor",
                metric="queue_depth",
                value=runtime.queue_depth,
                threshold=QUEUE_GROWING_THRESHOLD,
                severity="info",
                detail="{} operations in queue may contribute to memory usage".format(runtime.queue_depth),
            ))

        if mem > MEMORY_HIGH_THRESHOLD and runtime.queue_depth > 0:
            cause.hypothesis = "Memory is high ({:.1f}%) likely due to {} pending operations consuming memory.".format(
                mem, runtime.queue_depth
            )
            cause.confidence = 0.8
        elif mem > MEMORY_HIGH_THRESHOLD:
            cause.confidence = 0.6
            cause.missing_evidence.append("No queue activity — memory usage may be from external processes or leak")
            if not self._wp:
                cause.missing_evidence.append("Workspace data unavailable — cannot check cached files")
        else:
            cause.confidence = 0.3
            cause.hypothesis = "Memory within normal range ({:.1f}%). No anomaly.".format(mem)

        if cause.evidence:
            model.possible_causes.append(cause)

    def _analyze_queue(self, model, runtime, ws, ctx):
        observed = runtime
        if not observed:
            model.missing_information.append("Queue data unavailable — RuntimeProvider not connected")
            return

        queue = observed.queue_depth
        active = observed.active_operations
        latency = observed.avg_latency_ms
        throughput = observed.throughput
        status = observed.queue_status

        cause = CandidateCause(
            hypothesis="Queue status: {} (depth={}, active={})".format(status, queue, active),
            confidence=0.0,
        )

        cause.evidence.append(RootCauseEvidence(
            source="queue_monitor",
            metric="queue_depth",
            value=queue,
            threshold=QUEUE_GROWING_THRESHOLD,
            severity="warning" if queue > QUEUE_GROWING_THRESHOLD else "normal",
            detail="Queue depth {} active {}".format(queue, active),
        ))

        cause.evidence.append(RootCauseEvidence(
            source="queue_monitor",
            metric="avg_latency_ms",
            value=latency,
            threshold=QUEUE_HIGH_LATENCY_MS,
            severity="warning" if latency > QUEUE_HIGH_LATENCY_MS else "normal",
            detail="Avg latency {:.0f}ms".format(latency),
        ))

        # Korelasi CPU
        cpu = observed.cpu_percent
        if cpu > CPU_HIGH_THRESHOLD:
            cause.evidence.append(RootCauseEvidence(
                source="runtime_provider",
                metric="cpu_percent",
                value=cpu,
                threshold=CPU_HIGH_THRESHOLD,
                severity="warning",
                detail="CPU {:.1f}% — queue processing may be causing CPU spike".format(cpu),
            ))

        if status in ("growing", "overloaded"):
            cause.hypothesis = "Queue is {} ({} pending, {} active). CPU at {:.1f}% indicates processing bottleneck.".format(
                status, queue, active, cpu
            )
            cause.confidence = 0.9
            cause.missing_evidence.append("Throughput: {:.1f} ops/s — rate may be insufficient to drain queue".format(throughput))
            if not self._telemetry:
                cause.missing_evidence.append("Historical telemetry unavailable — cannot determine if queue is growing faster than usual")
        elif status == "processing":
            cause.confidence = 0.6
            cause.hypothesis = "Queue is processing ({} active operations)".format(active)
            cause.missing_evidence.append("Normal operation — queue should drain when operations complete")
        else:
            cause.confidence = 0.3
            cause.hypothesis = "Queue is {}. No anomaly.".format(status)

        if cause.evidence:
            model.possible_causes.append(cause)

    def _analyze_disk(self, model, ws, ctx):
        if not ws:
            model.missing_information.append("Disk data unavailable — WorkspaceProvider not connected")
            return

        disk = ws.disk
        cause = CandidateCause(
            hypothesis="",
            confidence=0.0,
        )

        cause.evidence.append(RootCauseEvidence(
            source="workspace_provider",
            metric="disk_percent",
            value=disk.percent,
            threshold=DISK_NEAR_FULL_THRESHOLD,
            severity="warning" if disk.percent > DISK_NEAR_FULL_THRESHOLD else "normal",
            detail="Disk {:.1f}% used ({:.1f} GB / {:.1f} GB)".format(
                disk.percent, disk.used_gb, disk.total_gb
            ),
        ))

        # Korelasi temp files
        if ws.temp.count > 0:
            cause.evidence.append(RootCauseEvidence(
                source="workspace_provider",
                metric="temp_file_count",
                value=ws.temp.count,
                threshold=TEMPFILE_HIGH_THRESHOLD,
                severity="warning" if ws.temp.count > TEMPFILE_HIGH_THRESHOLD else "normal",
                detail="Temp files: {} ({:.1f} MB)".format(ws.temp.count, ws.temp.size_mb),
            ))

        # Korelasi cache
        if ws.cache.size_mb > 100:
            cause.evidence.append(RootCauseEvidence(
                source="workspace_provider",
                metric="cache_size_mb",
                value=ws.cache.size_mb,
                threshold=200,
                severity="info",
                detail="Cache: {:.1f} MB".format(ws.cache.size_mb),
            ))

        if disk.percent > DISK_NEAR_FULL_THRESHOLD:
            if ws.temp.count > TEMPFILE_HIGH_THRESHOLD:
                cause.hypothesis = "Disk near full ({:.1f}%). Main contributor: {} temp files ({:.1f} MB).".format(
                    disk.percent, ws.temp.count, ws.temp.size_mb
                )
                cause.confidence = 0.9
            elif ws.cache.size_mb > 200:
                cause.hypothesis = "Disk near full ({:.1f}%). Cache at {:.1f} MB may be contributing.".format(
                    disk.percent, ws.cache.size_mb
                )
                cause.confidence = 0.75
            else:
                cause.hypothesis = "Disk near full ({:.1f}%) but no temp or cache contributor identified.".format(disk.percent)
                cause.confidence = 0.5
                cause.missing_evidence.append("No workspace data available on file distribution")
                if not self._rp:
                    cause.missing_evidence.append("No runtime queue data — cannot detect if processes are writing data")
        else:
            cause.confidence = 0.3
            cause.hypothesis = "Disk within normal range ({:.1f}%).".format(disk.percent)

        if cause.evidence:
            model.possible_causes.append(cause)

    def _analyze_normal(self, model, runtime, ws, ctx):
        """Ketika ditanya 'Why is everything normal?' — validasi."""
        cause = CandidateCause(
            hypothesis="All systems operating within normal parameters.",
            confidence=0.0,
        )

        if runtime:
            cause.evidence.append(RootCauseEvidence(
                source="runtime_provider",
                metric="cpu_percent",
                value=runtime.cpu_percent,
                threshold=CPU_HIGH_THRESHOLD,
                severity="normal",
                detail="CPU {:.1f}%".format(runtime.cpu_percent),
            ))
            cause.evidence.append(RootCauseEvidence(
                source="runtime_provider",
                metric="memory_percent",
                value=runtime.memory_percent,
                threshold=MEMORY_HIGH_THRESHOLD,
                severity="normal",
                detail="Memory {:.1f}%".format(runtime.memory_percent),
            ))

            if runtime.queue_depth == 0:
                cause.evidence.append(RootCauseEvidence(
                    source="queue_monitor",
                    metric="queue_depth",
                    value=0,
                    threshold=QUEUE_GROWING_THRESHOLD,
                    severity="normal",
                    detail="Queue idle",
                ))
                cause.confidence = 0.95
            else:
                cause.confidence = 0.7
                cause.missing_evidence.append("Queue has {} pending operations — not entirely idle".format(runtime.queue_depth))
        else:
            cause.confidence = 0.3
            cause.missing_evidence.append("No runtime data available to verify normal state")

        if cause.evidence:
            model.possible_causes.append(cause)

    def _analyze_general(self, model, runtime, ws, ctx):
        """Pertanyaan umum — report semua evidence yang tersedia tanpa cause spesifik."""
        if runtime:
            cause = CandidateCause(
                hypothesis="Observing system state. No specific anomaly detected.",
                confidence=0.5,
            )
            cause.evidence.append(RootCauseEvidence(
                source="runtime_provider",
                metric="cpu_percent",
                value=runtime.cpu_percent,
                threshold=CPU_HIGH_THRESHOLD,
                severity="warning" if runtime.cpu_percent > CPU_HIGH_THRESHOLD else "normal",
            ))
            cause.evidence.append(RootCauseEvidence(
                source="runtime_provider",
                metric="memory_percent",
                value=runtime.memory_percent,
                threshold=MEMORY_HIGH_THRESHOLD,
                severity="warning" if runtime.memory_percent > MEMORY_HIGH_THRESHOLD else "normal",
            ))
            cause.evidence.append(RootCauseEvidence(
                source="queue_monitor",
                metric="queue_depth",
                value=runtime.queue_depth,
                threshold=QUEUE_GROWING_THRESHOLD,
                severity="warning" if runtime.queue_depth > QUEUE_GROWING_THRESHOLD else "normal",
            ))
            model.missing_information.append("Question is not specific — reporting all available metrics without targeted analysis")
            model.possible_causes.append(cause)
        else:
            model.missing_information.append("No runtime data available. Unable to analyze.")
