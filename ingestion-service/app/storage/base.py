from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseStorageClient(ABC):
    """
    Abstract contract for all storage providers (OLAP, Data Lake, etc.)
    """
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def insert_logs(self, batch: List[Dict[str, Any]]) -> None:
        """Persist a batch of processed logs."""
        pass