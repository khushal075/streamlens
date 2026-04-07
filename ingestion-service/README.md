# 🟢 StreamLens — High-Throughput Log Ingestion Engine

[![CI Build](https://github.com/khushal075/streamlens/actions/workflows/ingestion-ci.yml/badge.svg)](https://github.com/khushal075/streamlens/actions/workflows/ingestion-ci.yml)
[![Coverage](https://img.shields.io/badge/Coverage-81%25-success)](https://github.com/khushal075/streamlens/actions/workflows/ingestion-ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**StreamLens** is a production-grade log ingestion platform designed for real-time observability at scale. It acts as a **Reliable Relay** between distributed applications and analytical data stores, ensuring every log is parsed, enriched, and safely persisted via a decoupled, fault-tolerant architecture.

---

## 🏗 System Architecture

StreamLens solves the "Slow Consumer" problem using a **Durable Write-Ahead Buffer** pattern. Incoming traffic is immediately offloaded to Redis, allowing the API to maintain ultra-low latency even during downstream Kafka or ClickHouse pressure.



### The Data Lifecycle
1.  **Ingestion Layer (API)**: FastAPI validates payloads and pushes to Redis (**Movement A**).
2.  **Enrichment Layer (Kafka Worker)**: Drains Redis, applies transformation strategies, and produces to Kafka.
3.  **Persistence Layer (ClickHouse Worker)**: Consumes from Kafka and performs high-speed batch inserts into ClickHouse (**Movement B**).
4.  **Archival Layer**: Simultaneously converts batches to compressed Parquet for S3 cold storage.

---

## ⚡ Key Engineering Patterns

### 1. Strategy Pattern (Log Transformation)
The system uses a **Strategy Pattern** for log enrichment. Each log source (Kubernetes, Docker, Cisco) has a dedicated `Processor` class. This makes the system **Open/Closed**: you can add support for a new log format by adding a single class without touching the core worker logic.

### 2. Observer Pattern (Worker Polling)
The `KafkaWorker` implements an **Observer-style** polling loop on Redis. It utilizes `BRPOP` (Blocking Right Pop) to ensure zero-CPU waste when the queue is empty, while maintaining near-instant reactivity when data arrives.

### 3. Reliable Relay & At-Least-Once Delivery
To prevent data loss:
* **Kafka Production**: Records are only cleared from the Redis buffer after a successful Kafka `ACK`.
* **ClickHouse Insertion**: Kafka offsets are only committed *after* ClickHouse confirms a successful batch write.



---

## 🛠 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **API Framework** | FastAPI (Asynchronous) |
| **Primary Buffer** | Redis (LPUSH / BRPOP) |
| **Message Broker** | Kafka (aiokafka) |
| **Analytics DB** | ClickHouse (Batch Optimized) |
| **Cold Storage** | AWS S3 / MinIO (Parquet) |
| **Configuration** | Pydantic Settings v2 |
| **Test Suite** | Pytest (81% Coverage) |

---

## 🚀 Running the Project

### Option 1: Local Development
**Prerequisites:** Python 3.11+, Poetry, Redis, Kafka, ClickHouse.

```bash
# 1. Clone & Install
git clone https://github.com/khushal075/streamlens.git
cd ingestion-service
poetry install

# 2. Start Services
# Terminal 1: API
poetry run uvicorn app.main:app --reload

# Terminal 2: Ingest Worker (Redis -> Kafka)
poetry run python -m app.workers.kafka_worker

# Terminal 3: Sink Worker (Kafka -> ClickHouse)
poetry run python -m app.workers.clickhouse_worker
```

### Option 2: Docker Compose (Full Stack)
```bash
docker compose up --build
```

---

## 🧪 Quality Assurance

We maintain a strict quality gate to ensure the reliability of the ingestion pipeline.

* **Linting**: `flake8` (Strict exclusion of library dependencies).
* **Unit Testing**: Comprehensive mocking of Kafka and ClickHouse drivers.
* **Coverage Gate**: **81%** (Minimum 80% required to pass CI).

```bash
# Run tests with coverage
poetry run pytest --cov=app --cov-report=term-missing
```

---

## 📝 API Reference

### Batch Log Ingestion
`POST /api/v1/logs`

**Header:** `X-Tenant-ID: customer_01`

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/logs \
  -H "X-Tenant-ID: customer_01" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "kubernetes",
    "logs": [{"raw_payload": "{\"status\": \"error\", \"code\": 500}", "timestamp": 1712445000}]
  }'
```

---

## 📂 Project Structure

```text
ingestion-service/
├── app/
│   ├── api/             # FastAPI routes, Middleware, & Rate Limiting
│   ├── workers/         # Background Workers (Kafka & ClickHouse loops)
│   ├── services/
│   │   └── processors/  # Strategy Pattern: Log Transformation logic
│   ├── messaging/       # Kafka Client Factories (aiokafka)
│   ├── storage/         # ClickHouse & S3/Parquet Providers
│   ├── queue/           # Redis connection logic
│   └── models/          # Pydantic Schemas (LogRecord, BatchRequest)
├── tests/               # Unit/Integration tests (Pytest)
└── k8s/                 # Production Manifests (API, Workers, HPA)
```

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.