"""
StreamLens Ingestion Service Entry Point
----------------------------------------
Role: The Orchestrator.
1. FastAPI: Handles incoming REST requests (The Producer).
2. Kafka/CH Workers: Background services (The Consumers).
3. Lifecycle: Manages the 'Warm-up' and 'Cool-down' of shared resources.
"""

import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.logs import router as logs_router
from app.services.buffer import log_buffer
from app.services.storage_service import storage_service
# Import the class-based worker instances
from app.workers.kafka_worker import kafka_ingestion_worker
from app.workers.clickhouse_worker import ch_worker

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern FastAPI Lifespan management.
    Synchronizes the startup/shutdown of the API and Background Workers.
    """
    # --- STARTUP ---
    logger.info("🚀 [Startup] Initializing StreamLens Services...")

    # 1. Warm up Shared Infrastructure (Redis)
    await log_buffer.connect()

    # 2. Launch Background Workers
    # We use asyncio.create_task to run the class-based .start() methods
    # These are managed as 'State' so we can access them during shutdown
    app.state.kafka_task = asyncio.create_task(kafka_ingestion_worker.start())
    app.state.ch_task = asyncio.create_task(ch_worker.start())

    logger.info("✅ [Startup] API, Kafka Worker, and ClickHouse Worker are active.")

    yield

    # --- SHUTDOWN ---
    logger.info("🛑 [Shutdown] Stopping services...")

    # 1. Signal Workers to stop (Triggers the internal .stop() logic)
    kafka_ingestion_worker.is_running = False
    ch_worker.is_running = False

    # 2. Cancel the tasks and wait for them to finish their final batch
    for task_name, task in [("Kafka", app.state.kafka_task), ("ClickHouse", app.state.ch_task)]:
        task.cancel()
        try:
            await task
            logger.info(f"Worker task '{task_name}' stopped gracefully.")
        except asyncio.CancelledError:
            pass

    # 3. Final Cleanup of DB Clients
    await storage_service.clickhouse_client.close()
    logger.info("👋 [Shutdown] Cleanup complete. System offline.")


# Initialize FastAPI
app = FastAPI(
    title="StreamLens Ingestion Service",
    description="High-performance multi-tenant log ingestion engine.",
    lifespan=lifespan
)

# Register API Routes
app.include_router(logs_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Liveness probe: Checks if the buffer is overflowing."""
    return {
        "status": "healthy",
        "buffer_size": await log_buffer.get_buffer_size()
    }