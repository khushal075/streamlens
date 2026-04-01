import asyncio
from aiokafka import AIOKafkaConsumer

KAFKA_TOPIC = "logs"
KAFKA_BOOTSTRAP = "localhost:29092"
GROUP_ID = "processing-service"

async def handle_message(msg):
    print(f"[Message] {msg.topic}:{msg.partition}:{msg.offset} key={msg.key} value={msg.value}")

async def main():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )

    # Retry loop for broker readiness
    retries = 10
    while retries > 0:
        try:
            await consumer.start()
            print("[Consumer] Connected to Kafka broker")
            break
        except Exception as e:
            print(f"[Consumer] Kafka not ready, retrying... ({retries}) {e}")
            retries -= 1
            await asyncio.sleep(3)
    else:
        raise RuntimeError("Kafka consumer could not start after retries")

    try:
        async for msg in consumer:
            asyncio.create_task(handle_message(msg))
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())