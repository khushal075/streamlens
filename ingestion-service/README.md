# 🟢 StreamLens — High-Throughput Log Ingestion Engine

A production-grade log ingestion platform designed for real-time observability at scale. Built to demonstrate high-concurrency patterns, durable buffering, and automated data archival. StreamLens acts as a reliable bridge between distributed applications and analytical data stores, ensuring every log is parsed, enriched, and safely persisted.

---

## What It Does

StreamLens provides a multi-tenant API to receive raw, unstructured logs from various sources (Kubernetes, Docker, Cisco, etc.). It solves the "slow consumer" problem by immediately offloading incoming data to a high-speed Redis buffer, returning a `202 Accepted` to the client in milliseconds.

A specialized fleet of background workers then drains this buffer, applies transformation strategies (Regex/JSON enrichment), and facilitates a **Reliable Relay** to Kafka and ClickHouse.

---

## Architecture

StreamLens operates on a **decoupled pipeline** to ensure that a spike in log volume never crashes the API or slows down the application source.



```
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│   Source Systems     │      │   Ingestion Layer    │      │    Storage Layer     │
│ (K8s, Apps, Syslog)  │      │      (FastAPI)       │      │     (ClickHouse)     │
└──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
           │                             │                             ▲
           │ 1. POST /api/v1/logs        │                             │
           └────────────────────────────►│                             │ 4. Batch Insert
                                         │                             │
                                 ┌───────┴───────┐             ┌───────┴───────┐
                                 │ Durable Buffer│             │ Message Broker│
                                 │    (Redis)    │             │    (Kafka)    │
                                 └───────┬───────┘             └───────▲───────┘
                                         │                             │
                                         │ 2. Pop & Transform          │ 3. Produce
                                         │                             │
                                 ┌───────▼───────┐             ┌───────┴───────┐
                                 │  Ingest Worker│             │  Sink Worker  │
                                 │ (Kafka Prod)  │             │ (CH Consumer) │
                                 └───────────────┘             └───────────────┘
```

### The "Reliable Relay" Pattern

To prevent data loss during network partitions or database outages:
1. **Movement A**: Logs are buffered in Redis. The `KafkaWorker` only removes them once successfully acknowledged by the Kafka Broker.
2. **Movement B**: The `ClickHouseWorker` uses **At-Least-Once** delivery. It only commits Kafka offsets *after* ClickHouse confirms a successful batch insert.

---

## Data Pipeline

The system uses a **Strategy Pattern** for log enrichment. The transformation logic is decoupled from the worker loop, allowing for easy extension to new log formats.

```
Raw Payload (JSON/String)
         │
         ▼
┌─────────────────────────────────┐
│     Enrichment Strategy         │
│ - Detect Source (K8s/Docker)    │
│ - Apply Regex Patterns          │
│ - Inject Metadata (Tenant ID)   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     Batching Engine             │
│ - Aggregate 1,000+ records      │
│ - Compression (Snappy/Gzip)     │
└────────────────┬────────────────┘
                 │
                 ▼
          Kafka / S3 Parquet
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (Asynchronous) |
| **Primary Buffer** | Redis (LPUSH/BRPOP) |
| **Message Broker** | Kafka (aiokafka) |
| **Hot Analytics** | ClickHouse |
| **Cold Storage** | AWS S3 (Parquet format) |
| **Config Management** | Pydantic Settings v2 |
| **Testing** | Pytest + Coverage (81%+) |
| **Packaging** | Poetry |

---

## Running the Project

### Option 1 — Local Development

**Prerequisites:** Python 3.11+, Redis, Kafka, ClickHouse

```bash
# 1. Clone and Install
git clone <repo-url>
cd ingestion-service
poetry install

# 2. Setup Environment
cp .env.example .env
```

**Start the Stack:**
```bash
# Terminal 1: API
poetry run uvicorn app.main:app --reload

# Terminal 2: Redis-to-Kafka Worker
poetry run python -m app.workers.kafka_worker

# Terminal 3: Kafka-to-ClickHouse Worker
poetry run python -m app.workers.clickhouse_worker
```

---

### Option 2 — Docker Compose

```bash
docker compose up --build
```

| Service | Port | Role |
|---|---|---|
| `ingestion_api` | 8000 | Log acceptance |
| `kafka_worker` | — | Enrichment & Production |
| `clickhouse_worker` | — | Persistence |
| `redis` | 6379 | Internal Buffer |
| `clickhouse` | 8123 | Analytics DB |

---

## API Reference

### Batch Ingest Logs
`POST /api/v1/logs`

**Header:** `X-Tenant-ID: <id>`

```bash
curl -X POST http://localhost:8000/api/v1/logs \
  -H "X-Tenant-ID: customer_alpha" \
  -d '{
    "source": "kubernetes",
    "logs": [{"raw_payload": "user_login_success", "timestamp": 1712445000}]
  }'
```

---

## Project Structure

```
ingestion-service/
├── app/
│   ├── api/             # FastAPI routes & Rate Limiters
│   ├── workers/         # Movement A (Kafka) & Movement B (CH) Workers
│   ├── services/
│   │   └── processors/  # Strategy Pattern Transformation logic
│   ├── messaging/       # Kafka Client Factories (Producer/Consumer)
│   ├── storage/         # ClickHouse & S3/Parquet Adapters
│   ├── queue/           # Redis connection logic
│   └── models/          # Pydantic Schemas (LogRecord, BatchRequest)
├── tests/               # Unit/Integration tests (81% Coverage)
└── k8s/                 # Deployment, ConfigMaps, and HPA
```

---

## Key Design Decisions

**Durable Write-Ahead Buffering** — By using Redis as an intermediary, we decouple the API's availability from Kafka's availability.

**ThreadPool Transformation** — Log parsing is CPU-bound. Workers offload transformation to a `ThreadPoolExecutor` to prevent blocking the event loop's IO operations.

**Batch Persistance** — ClickHouse performance is dependent on large inserts. The `ClickHouseWorker` aggregates messages into 1.0MB+ batches before committing, drastically reducing disk IO.

**Environmental Parity** — CI/CD overrides `BATCH_SIZE` to 1,000 for load testing, while dev defaults to 500. This is handled via Pydantic Settings without code changes.

---

## Requirements

- Python 3.11+
- Poetry
- Docker & Docker Compose
- 4GB+ RAM (Required for Kafka + ClickHouse local stack)