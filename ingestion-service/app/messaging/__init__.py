"""
Messaging Module
----------------
Exposes the global messaging producer instance for the application.
"""

from app.messaging.factory import messaging_producer

# This allows other modules to use: from app.messaging import messaging_producer
__all__ = ["messaging_producer"]