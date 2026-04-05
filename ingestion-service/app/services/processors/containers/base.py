import json
from ..base import BaseLogProcessor
from typing import Dict, Any


class ContainerBase(BaseLogProcessor):
    """
    Parent: Handles JSON unwrapping for Kubernetes/Docker.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        try:
            # 1. Try to parse the wrapper
            payload = json.loads(raw_message)

            # 2. Extract standard container metadata
            container_meta = {
                "container_id": payload.get("container_id"),
                "namespace": payload.get("namespace", "default"),
                "stream": payload.get("stream", "stdout")
            }

            # 3. Pass the inner 'log' or 'msg' to the child specialist
            inner_msg = payload.get("log") or payload.get("message") or raw_message
            return {**container_meta, **self.specialize(inner_msg)}

        except json.JSONDecodeError:
            # If it's not JSON, just treat it as a raw string
            return self.specialize(raw_message)

    @abstractmethod
    def specialize(self, content: str) -> Dict[str, Any]:
        """Children like KubernetesProcessor implement this."""
        pass