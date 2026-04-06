import json
from abc import abstractmethod  # 👈 REQUIRED for the @abstractmethod decorator
from typing import Dict, Any
from ..base import BaseLogProcessor


class ContainerBase(BaseLogProcessor):
    """
    Parent: Handles JSON unwrapping for Kubernetes/Docker.
    Provides a skeleton for specialized container parsers.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        try:
            # 1. Try to parse the wrapper (Docker/K8s usually wrap logs in JSON)
            payload = json.loads(raw_message)

            # 2. Extract standard container metadata
            container_meta = {
                "container_id": payload.get("container_id"),
                "namespace": payload.get("namespace", "default"),
                "stream": payload.get("stream", "stdout")
            }

            # 3. Pass the inner 'log' or 'msg' to the child specialist
            # We check multiple common keys because Docker uses 'log' and K8s uses 'message'
            inner_msg = payload.get("log") or payload.get("message") or raw_message

            # Merge the container shell info with the application-specific info
            return {**container_meta, **self.specialize(inner_msg)}

        except json.JSONDecodeError:
            # If it's not JSON, just treat it as a raw string and let the child specialize it
            return self.specialize(raw_message)

    @abstractmethod
    def specialize(self, content: str) -> Dict[str, Any]:
        """
        Children like KubernetesProcessor or DockerProcessor implement this
        to parse the application-specific parts of the log.
        """
        pass