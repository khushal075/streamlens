import time
from collections import defaultdict

RATE_LIMIT = 1000  # logs per second per tenant

tenant_counters = defaultdict(lambda: {"count": 0, "timestamp": time.time()})

def is_allowed(tenant_id: str, logs_count: int) -> bool:
    data = tenant_counters[tenant_id]
    now = time.time()

    if now - data["timestamp"] > 1:
        data["count"] = 0
        data["timestamp"] = now

    if data["count"] + logs_count > RATE_LIMIT:
        return False

    data["count"] += logs_count
    return True