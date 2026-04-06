"""
StreamLens Common Library
-------------------------
Shared utilities, models, and configurations for the StreamLens ecosystem.
"""

from streamlens_common.config.settings import GlobalSettings  # 👈 Export the Class
from streamlens_common.models.base_models import LogEnvelope

__all__ = ["GlobalSettings", "LogEnvelope"]
__version__ = "0.1.0"