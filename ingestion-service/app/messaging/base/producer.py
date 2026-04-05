"""
Base Producer Interface
-----------------------
Role: The abstract contract for all messaging implementations.
Pattern: Abstract Base Class (ABC).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseProducer(ABC):
    """
    Abstract interface for messaging producers.

    This class defines the lifecycle (start/stop) and the primary
    data-out method (send_batch) that all concrete producers
    must implement.
    """

    @abstractmethod
    async def start(self) -> None:
        """
        Initialize the connection to the message broker.
        Should be called during the application startup lifespan.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Gracefully close the broker connection.
        Should be called during the application shutdown lifespan.
        """
        pass

    @abstractmethod
    async def send_batch(self, messages: List[Dict[str, Any]]) -> None:
        """
        Publishes a batch of messages to the configured broker.

        Args:
            messages (List[Dict[str, Any]]): A list of processed log envelopes.
        """
        pass