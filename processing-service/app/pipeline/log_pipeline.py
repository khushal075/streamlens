import time
from app.parser.json_parser import parse_json_log
from app.schema.normalizer import normalize_log
from app.enrichment.enricher import enrich_log
from app.indexer.es_indexer import index_log
from app.dlq.dlq_producer import send_to_dlq
from app.kafka.schema_registry import validate_message
from app.metrics.prometheus_metrics import kafka_processed, kafka_failed, processing_latency
from app.tracing.tracer import tracer

class LogPipeline:

    async def process(self, raw_message: dict):
        start_time = time.time()
        with tracer.start_as_current_span("log_pipeline") as span:
            try:
                # 1. Schema Validation
                validate_message("logs", raw_message)

                # 2. Parse
                parsed = parse_json_log(raw_message)

                # 3. Normalize
                normalized = normalize_log(parsed)

                # 4. Enrich
                enriched = enrich_log(normalized)

                # 5. Index
                await index_log(enriched)

                kafka_processed.inc()

            except Exception as e:
                kafka_failed.inc()
                await send_to_dlq(raw_message, str(e))
            finally:
                processing_latency.observe(time.time() - start_time)