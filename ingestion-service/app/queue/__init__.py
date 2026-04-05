# app/queue/__init__.py
from app.core.config import settings
from app.queue.redis_queue import redis_queue
from app.queue.in_memory_queue import in_memory_queue

# Strategy: Swap implementation based on MESSAGE_BROKER config
if settings.MESSAGE_BROKER.lower() == "redis":
    log_queue = redis_queue
else:
    log_queue = in_memory_queue

__all__ = ["log_queue"]