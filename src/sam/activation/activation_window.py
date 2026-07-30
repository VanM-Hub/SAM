"""Activation Window — jendela waktu aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivationWindow:
    window_id: str = ""
    name: str = ""
    start: float = 0.0
    end: float = 0.0
    duration: float = 0.0
    urgency: str = "normal"  # low, normal, high, critical


class ActivationWindowManager:
    """Mengelola jendela waktu aktivasi."""

    def create(self, env: str, estimated_duration: float,
               timestamp: float = 0.0) -> ActivationWindow:
        urgency_map = {"emergency": "critical", "busy": "high",
                       "normal": "normal", "idle": "low"}
        urgency = urgency_map.get(env, "normal")

        duration = estimated_duration if env != "emergency" else estimated_duration * 0.5

        return ActivationWindow(
            window_id=f"win_{timestamp}",
            name=f"Window @ {env}",
            start=timestamp,
            end=timestamp + duration,
            duration=duration,
            urgency=urgency,
        )

    def is_expired(self, window: ActivationWindow,
                   current_time: float) -> bool:
        return current_time > window.end

    def remaining(self, window: ActivationWindow,
                  current_time: float) -> float:
        return max(0, window.end - current_time)
