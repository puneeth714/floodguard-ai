import asyncio
from typing import AsyncGenerator

class SSEManager:
    """
    Lightweight, in-memory async publish/subscribe manager to stream
    real-time event data (Server-Sent Events) to multiple browser clients.
    """
    def __init__(self):
        self.listeners = []

    def subscribe(self) -> asyncio.Queue:
        """Subscribes a client and returns their event queue."""
        q = asyncio.Queue()
        self.listeners.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """Unsubscribes a client by removing their event queue."""
        if q in self.listeners:
            self.listeners.remove(q)

    async def broadcast(self, data: dict):
        """Broadcasts a payload message to all active listeners."""
        for q in self.listeners:
            await q.put(data)

sse_manager = SSEManager()
