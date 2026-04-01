# app/enrichment/enricher.py
def enrich_log(log: dict) -> dict:
    # Example enrichment: add derived tags
    log["tags"] = [log["service"], "log"]
    return log