"""
In-Memory Queue
---------------
Role: Local development / Unit testing mock.
Logic: Uses an internal list with an Async Lock for thread-safety.
"""

import asyncio
from typing import List, Dict, Any

class InMemoryQueue:
    def __init__(self):
        self._queue = []
        self._lock = asyncio.Lock()

    async def connect(self):
        """Mock connect for interface consistency."""
        pass

    async def disconnect(self):
        """Mock disconnect for interface consistency."""
        pass

    async def push_batch(self, items: List[Dict[str, Any]]):
        """Adds a list of items to the internal buffer."""
        async with self._lock:
            self._queue.extend(items)

    async def pop_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """Removes and returns a batch of items from the buffer."""
        async with self._lock:
            batch = self._queue[:batch_size]
            self._queue = self._queue[batch_size:]
            return batch

    async def queue_size(self) -> int:
        """Returns current buffer count."""
        return len(self._queue)

# Global instance for the 'mock' strategy
in_memory_queue = InMemoryQueue()