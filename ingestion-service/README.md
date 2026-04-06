# 🟢 StreamLens Ingestion Service

[![CI](https://github.com/khushal075/streamlens/actions/workflows/ci.yml/badge.svg)](https://github.com/khushal075/streamlens/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com/)

**StreamLens** is a high-performance, multi-tenant log ingestion engine designed for real-time observability. It acts as a reliable bridge between distributed applications and analytical data stores, ensuring data is parsed, enriched, and safely persisted.

---

## 🏗 System Architecture

StreamLens operates a **Reliable Relay** model across two distinct data movements:



### 1️⃣ Movement A: Ingestion & Enrichment
* **API Layer**: FastAPI receives batches of raw logs and performs tenant-level rate limiting.
* **Durable Buffer**: Logs are immediately offloaded to **Redis** to ensure low-latency responses (HTTP 202).
* **Kafka Worker**: A dedicated background process that drains Redis, applies **Regex/JSON Transformations** via a Strategy Pattern, and pushes structured data to **Kafka**.

### 2️⃣ Movement B: Persistence & Archival
* **ClickHouse Worker**: Subscribes to Kafka topics and performs high-speed **Batch Inserts** into **ClickHouse**.
* **Data Lake Archiver**: Simultaneously converts log batches into compressed **Parquet** files for long-term storage in **S3**.

---

## ⚡ Key Features

* **Smart Parsing**: Automatic detection and parsing for Docker, Kubernetes, Cisco, and generic JSON logs.
* **Threaded Transformation**: Uses a `ThreadPoolExecutor` to handle CPU-intensive Regex parsing without blocking the IO loop.
* **At-Least-Once Delivery**: Kafka offsets are only committed after successful database confirmation.
* **Columnar Archival**: Built-in support for Snappy-compressed Parquet archival to S3/MinIO.
* **Adaptive Back-off**: Workers automatically slow down during downstream outages to prevent cascading failures.

---

## 🛠 Project Structure

```text
ingestion-service/
├── app/
│   ├── api/                # FastAPI Endpoints & Rate Limiting
│   ├── workers/            # Background Workers (Kafka & ClickHouse)
│   ├── services/
│   │   └── processors/     # Transformation Logic (Strategy Pattern)
│   ├── messaging/          # Kafka Producer/Consumer Factory
│   ├── storage/            # ClickHouse & S3/Parquet Providers
│   ├── queue/              # Redis Integration
│   └── models/             # Pydantic Schemas
├── Dockerfile
└── pyproject.toml
```

---

## 🚀 Getting Started

### 1. Requirements
* Python 3.12+ (Optimized for 3.14)
* Redis (Buffer)
* Kafka (Message Broker)
* ClickHouse (Hot Analytics)

### 2. Installation
```bash
git clone https://github.com/khushal075/streamlens.git
cd streamlens/ingestion-service
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file based on `app/core/config.py`:
```env
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
CLICKHOUSE_HOST=localhost
S3_LOG_BUCKET=streamlens-cold-storage
```

### 4. Running the Service
```bash
# Starts the API + Kafka Worker + ClickHouse Worker in a single event loop
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📝 API Guide

### Ingest Logs
`POST /api/v1/logs`

**Payload:**
```json
{
  "tenant_id": "cust_99",
  "source": "kubernetes",
  "logs": [
    {
      "raw_payload": "{\"log\":\"User login successful\",\"container_id\":\"a1b2\"}",
      "timestamp": 1712445000
    }
  ]
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "batch_id": "uuid-v4-here",
  "queue_depth": 450
}
```

---

## 🔧 Worker Internals

### The Kafka Worker (Movement A)
Uses the **Observer Pattern** to poll Redis. It offloads transformation to a thread pool:
```python
# app/workers/kafka_worker.py
processed_logs = await loop.run_in_executor(executor, transform_logic, batch)
```

### The ClickHouse Worker (Movement B)
Optimized for **Bulk Inserts**. It does not write row-by-row; it gathers Kafka messages into batches of 1,000+ for maximum ClickHouse performance.

---

## 📊 Monitoring & Health
* **Liveness**: `GET /health` returns the current Redis buffer depth.
* **Metrics**: Prometheus metrics available for tracking transformation latency and Kafka lag (Coming Soon).

---

## 💡 License
Distributed under the MIT License. See `LICENSE` for more information.

---