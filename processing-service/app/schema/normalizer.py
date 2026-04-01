# app/schema/normalizer.py
from typing import Dict, Any

def normalize_log(raw_log: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "tenant": raw_log.get("tenant_id"),
        "service": raw_log.get("service").lower(),
        "ts": raw_log.get("timestamp"),
        "msg": raw_log.get("message"),
        "metadata": raw_log.get("metadata", {}),
        "msg_length": len(raw_log.get("message", "")),
    }
    return normalized