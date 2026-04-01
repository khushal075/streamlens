# app/messaging/base/producer.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseProducer(ABC):

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def send_batch(self, messages: List[Dict[str, Any]]):
        pass