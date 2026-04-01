from prometheus_client import Counter, Histogram

kafka_processed = Counter(
    "kafka_messages_processed_total", "Total Kafka messages processed"
)
kafka_failed = Counter(
    "kafka_messages_failed_total", "Total Kafka messages failed"
)
processing_latency = Histogram(
    "log_processing_latency_seconds", "Time spent processing each log"
)