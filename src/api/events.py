import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List

logger = logging.getLogger(__name__)

class EventBroadcaster:
    """In-memory event hub for Server-Sent Events (SSE)."""

    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    async def subscribe(self) -> AsyncGenerator[Dict[str, Any], None]:
        queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        logger.debug(f"New SSE client subscribed. Total: {len(self._subscribers)}")
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            if queue in self._subscribers:
                self._subscribers.remove(queue)
            logger.debug(f"SSE client unsubscribed. Total: {len(self._subscribers)}")

    def publish(self, event_type: str, payload: Dict[str, Any]):
        message = {
            "type": event_type,
            "data": payload,
        }
        # Non-blocking push to all active queues
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass

event_broadcaster = EventBroadcaster()
