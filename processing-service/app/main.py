# app/main.py
import asyncio
from app.consumers.kafka_consumer import main as consume
from prometheus_client import start_http_server

METRICS_PORT = 8001

def run_metrics_server():
    start_http_server(METRICS_PORT)
    print(f"[Metrics] Prometheus running on port {METRICS_PORT}")

async def main():
    run_metrics_server()
    await consume()

def async_main_wrapper():
    asyncio.run(main())