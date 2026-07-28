"""
OP-294 — Provider Scheduler

Menjadwalkan provider berdasarkan prioritas, fallback, timeout, retry, circuit breaker.
Hanya tahu ProviderProtocol — tidak tahu OpenAI/Gemini secara langsung.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Callable
from datetime import datetime
import time


class ProviderProtocol(Protocol):
    """Protocol untuk provider — minimal interface."""
    def generate(self, request: Any) -> Any: ...
    def health(self) -> bool: ...
    def metadata(self) -> Any: ...


@dataclass(frozen=True)
class ProviderSlot:
    name: str
    priority: int
    timeout_ms: int
    retry_count: int
    circuit_breaker_threshold: int = 3
    circuit_breaker_reset_ms: int = 60000

    @property
    def timeout_s(self) -> float:
        return self.timeout_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "priority": self.priority,
            "timeout_ms": self.timeout_ms,
            "retry_count": self.retry_count,
            "circuit_breaker": self.circuit_breaker_threshold,
        }


@dataclass(frozen=True)
class SchedulerResult:
    success: bool
    provider_name: str
    response: Any
    latency_ms: float
    attempts: int
    circuit_breaker_open: bool
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "provider": self.provider_name,
            "latency_ms": self.latency_ms,
            "attempts": self.attempts,
            "circuit_breaker_open": self.circuit_breaker_open,
            "error": self.error,
        }


@dataclass(frozen=True)
class SchedulerReport:
    results: Tuple[SchedulerResult, ...] = ()
    overall_success: bool = False
    total_latency_ms: float = 0.0
    total_attempts: int = 0
    providers_tried: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_success": self.overall_success,
            "total_latency_ms": self.total_latency_ms,
            "total_attempts": self.total_attempts,
            "providers_tried": list(self.providers_tried),
            "results": [r.to_dict() for r in self.results],
        }


class CircuitBreaker:
    """Circuit breaker per provider."""
    def __init__(self, threshold: int = 3, reset_ms: int = 60000):
        self._threshold = threshold
        self._reset_ms = reset_ms
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._is_open = False

    @property
    def is_open(self) -> bool:
        if self._is_open:
            elapsed_ms = (time.time() - self._last_failure_time) * 1000
            if elapsed_ms >= self._reset_ms:
                self._is_open = False
                self._failure_count = 0
        return self._is_open

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._threshold:
            self._is_open = True

    def record_success(self) -> None:
        self._failure_count = 0

    def reset(self) -> None:
        self._failure_count = 0
        self._is_open = False


class ProviderScheduler:
    """
    Menjadwalkan provider berdasarkan prioritas.

    Fitur:
    - Provider priority: coba tertinggi dulu
    - Fallback chain: jika gagal → provider berikutnya
    - Timeout: per-provider configurable
    - Retry: per-provider configurable
    - Circuit breaker: per-provider threshold
    - Unavailable provider: skip, tidak crash
    - Provider health: cek health() sebelum generate
    """

    def __init__(self):
        self._providers: Dict[str, ProviderProtocol] = {}
        self._slots: Dict[str, ProviderSlot] = {}
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_slot = ProviderSlot(
            name="mock", priority=100, timeout_ms=30000, retry_count=1,
        )

    def register(self, name: str, provider: ProviderProtocol,
                 priority: int = 100, timeout_ms: int = 30000,
                 retry_count: int = 1,
                 circuit_breaker_threshold: int = 3) -> None:
        self._providers[name] = provider
        self._slots[name] = ProviderSlot(
            name=name, priority=priority, timeout_ms=timeout_ms,
            retry_count=retry_count,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                threshold=circuit_breaker_threshold,
            )

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)
        self._slots.pop(name, None)
        self._breakers.pop(name, None)

    def get_provider(self, name: str) -> Optional[ProviderProtocol]:
        return self._providers.get(name)

    def get_slot(self, name: str) -> Optional[ProviderSlot]:
        return self._slots.get(name)

    @property
    def providers(self) -> Tuple[str, ...]:
        return tuple(self._providers.keys())

    @property
    def active_providers(self) -> Tuple[str, ...]:
        """Provider yang sehat dan circuit breaker-nya tidak open."""
        result: list[str] = []
        for name in self._providers:
            cb = self._breakers.get(name)
            if cb and cb.is_open:
                continue
            p = self._providers[name]
            try:
                if p.health():
                    result.append(name)
            except Exception:
                continue
        return tuple(result)

    def schedule(self, request: Any,
                 preferred: str = "") -> SchedulerResult:
        """
        Jadwalkan reasoning request ke provider terbaik.

        1. Jika preferred tersedia dan sehat → pakai itu
        2. Urutkan provider berdasarkan priority
        3. Coba satu per satu (fallback chain)
        4. Retry sesuai config per provider
        """
        if preferred and preferred in self._providers:
            providers_to_try = [preferred]
        else:
            providers_to_try = self._sorted_providers()

        results: list[SchedulerResult] = []
        for name in providers_to_try:
            slot = self._slots.get(name, self._default_slot)
            cb = self._breakers.get(name)

            # Circuit breaker check
            if cb and cb.is_open:
                results.append(SchedulerResult(
                    success=False, provider_name=name,
                    response=None, latency_ms=0.0, attempts=0,
                    circuit_breaker_open=True,
                    error="Circuit breaker open",
                ))
                continue

            # Coba generate dengan retry
            for attempt in range(max(1, slot.retry_count + 1)):
                provider = self._providers.get(name)
                if not provider:
                    results.append(SchedulerResult(
                        success=False, provider_name=name,
                        response=None, latency_ms=0.0, attempts=attempt + 1,
                        circuit_breaker_open=False,
                        error="Provider not found",
                    ))
                    break

                # Health check
                try:
                    if not provider.health():
                        if attempt < slot.retry_count:
                            continue
                        results.append(SchedulerResult(
                            success=False, provider_name=name,
                            response=None, latency_ms=0.0,
                            attempts=attempt + 1,
                            circuit_breaker_open=False,
                            error="Provider unhealthy",
                        ))
                        break
                except Exception as e:
                    if attempt < slot.retry_count:
                        continue
                    results.append(SchedulerResult(
                        success=False, provider_name=name,
                        response=None, latency_ms=0.0,
                        attempts=attempt + 1,
                        circuit_breaker_open=False,
                        error=f"Health check failed: {e}",
                    ))
                    break

                # Generate
                try:
                    start = time.time()
                    response = provider.generate(request)
                    elapsed = (time.time() - start) * 1000

                    if cb:
                        cb.record_success()

                    result = SchedulerResult(
                        success=True, provider_name=name,
                        response=response, latency_ms=round(elapsed, 2),
                        attempts=attempt + 1,
                        circuit_breaker_open=False,
                    )
                    return result

                except Exception as e:
                    if cb:
                        cb.record_failure()

                    if attempt < slot.retry_count:
                        continue

                    results.append(SchedulerResult(
                        success=False, provider_name=name,
                        response=None, latency_ms=0.0,
                        attempts=attempt + 1,
                        circuit_breaker_open=bool(cb and cb.is_open),
                        error=f"Generation failed: {e}",
                    ))
                    break

        # All providers failed
        return SchedulerResult(
            success=False, provider_name="",
            response=None, latency_ms=0.0, attempts=sum(
                r.attempts for r in results
            ),
            circuit_breaker_open=True,
            error="All providers exhausted",
        )

    def schedule_all(self, request: Any) -> SchedulerReport:
        """Jalankan ke semua provider (untuk aggregation/merge)."""
        results: list[SchedulerResult] = []
        for name in self._sorted_providers():
            r = self.schedule(request, preferred=name)
            results.append(r)

        return SchedulerReport(
            results=tuple(results),
            overall_success=any(r.success for r in results),
            total_latency_ms=sum(r.latency_ms for r in results),
            total_attempts=sum(r.attempts for r in results),
            providers_tried=tuple(r.provider_name for r in results),
        )

    def reset_all_circuit_breakers(self) -> None:
        for cb in self._breakers.values():
            cb.reset()

    def reset_circuit_breaker(self, name: str) -> None:
        cb = self._breakers.get(name)
        if cb:
            cb.reset()

    def health_report(self) -> Dict[str, bool]:
        health: Dict[str, bool] = {}
        for name, p in self._providers.items():
            cb = self._breakers.get(name)
            cb_open = bool(cb and cb.is_open)
            try:
                provider_ok = p.health()
                health[name] = provider_ok and not cb_open
            except Exception:
                health[name] = False
        return health

    def _sorted_providers(self) -> List[str]:
        """Urutkan provider berdasarkan priority (tertinggi dulu)."""
        sorted_names = sorted(
            self._slots.keys(),
            key=lambda n: self._slots[n].priority,
            reverse=True,
        )
        return sorted_names
