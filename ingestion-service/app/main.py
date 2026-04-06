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
from app.workers.kafka_worker import run_worker as kafka_ingestion_worker
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
    # 💡 FIX: We call the functions directly.
    # These functions internally create the Class and run the .start() loop.
    app.state.kafka_task = asyncio.create_task(kafka_ingestion_worker())
    app.state.ch_task = asyncio.create_task(ch_worker())

    logger.info("✅ [Startup] API and Workers are now active ...")

    yield

    # --- SHUTDOWN ---
    logger.info("🛑 [Shutdown] Stopping services...")

    # 1. Cancel the tasks.
    # Since our workers handle asyncio.CancelledError, they will
    # trigger their own .stop() logic internally!
    for task_name, task in [("Kafka", app.state.kafka_task), ("ClickHouse", app.state.ch_task)]:
        task.cancel()
        try:
            # Give them a moment to finish the current batch
            await asyncio.wait_for(task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            logger.info(f"Worker task '{task_name}' stopped.")

    # 2. Final Cleanup
    await log_buffer.disconnect()
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