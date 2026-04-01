# app/dlq/dlq_producer.py
from aiokafka import AIOKafkaProducer
import asyncio

KAFKA_BOOTSTRAP = "kafka:9092"
DLQ_TOPIC = "logs_dlq"

producer = None

async def init_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
        await producer.start()

async def send_to_dlq(msg_bytes: bytes):
    await init_producer()
    await producer.send_and_wait(DLQ_TOPIC, msg_bytes)