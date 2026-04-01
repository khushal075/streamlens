# app/main.py

from fastapi import FastAPI
import asyncio

from app.api.logs import router as logs_router
from app.workers.kafka_worker import kafka_worker

app = FastAPI(title="StreamLens Ingestion Service")

app.include_router(logs_router)


@app.on_event("startup")
async def startup():
    pass
    #asyncio.create_task(kafka_worker())