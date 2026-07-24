import asyncio
import uuid
from datetime import datetime

from src.sam.core.event_bus import EventBus
from src.sam.core.events import Event, ServiceStarted


async def test_publish_subscribe():
    bus = EventBus()
    received = []

    async def handler(e: Event):
        received.append((e.type, e.id))

    bus.subscribe("service.started", handler)

    ev = ServiceStarted(id=str(uuid.uuid4()), source="test", payload={})
    await bus.publish(ev)

    assert len(received) == 1
    assert received[0][0] == "service.started"


async def test_wildcard():
    bus = EventBus()
    received = []

    async def handler(e: Event):
        received.append(e.type)

    bus.subscribe("*", handler)

    ev = Event(id=str(uuid.uuid4()), type="plugin.installed", source="test", payload={})
    await bus.publish(ev)

    assert "plugin.installed" in received


async def test_immutable_event():
    ev = Event(id=str(uuid.uuid4()), type="job.enqueued", source="test", payload={})
    try:
        ev.payload["x"] = 1
        immutable = False
    except Exception:
        immutable = True

    assert immutable


if __name__ == "__main__":
    asyncio.run(test_publish_subscribe())
    asyncio.run(test_wildcard())
    asyncio.run(test_immutable_event())
    print("OK")
