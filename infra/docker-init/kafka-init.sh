#!/bin/bash
# kafka-init.sh
set -e

echo "[Kafka Init] Waiting for Kafka broker..."

# Wait until Kafka is ready
cub kafka-ready -b localhost:9092 1 20

# Create main topics
kafka-topics --create --topic logs \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

kafka-topics --create --topic logs_dlq \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1 \
    --if-not-exists

echo "[Kafka Init] Topics ready."