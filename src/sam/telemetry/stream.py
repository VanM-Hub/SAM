"""
SSE (Server-Sent Events) stream for real-time telemetry.
"""

import asyncio
import json
from typing import AsyncGenerator

from .event import TelemetryEvent
from .service import TelemetryService


async def event_stream(service: TelemetryService) -> AsyncGenerator[str, None]:
    """Generate SSE-formatted event stream.

    Yields ``data: <json>\\n\\n`` lines for each new event.
    """
    async for event in service.follow():
        payload = json.dumps({
            "id": event.id,
            "type": event.type.value,
            "component": event.component.value,
            "severity": event.severity.value,
            "category": event.category.value,
            "message": event.message,
            "timestamp": event.timestamp.isoformat(),
        }, default=str)
        yield "data: {}\n\n".format(payload)
        await asyncio.sleep(0)


async def sse_handler(scope, receive, send):
    """ASGI-compatible SSE handler for use with FastAPI/Starlette."""
    raise NotImplementedError("Use FastAPI StreamingResponse directly with event_stream()")
