"""
Worker Entrypoint
-----------------
Starts the background processing loops for ClickHouse and Kafka.
"""
import asyncio
import logging
from app.workers.clickhouse_worker import run_clickhouse_worker
from app.workers.kafka_worker import run_kafka_worker

logging.basicConfig(level=logging.INFO)

async def main():
    # Run both workers concurrently in the same process
    # Note: In huge systems, you'd run these in separate Docker containers
    await asyncio.gather(
        run_clickhouse_worker(),
        run_kafka_worker()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping workers...")