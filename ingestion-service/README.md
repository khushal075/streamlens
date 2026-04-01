# 🟢 StreamLens Ingestion Service

[![CI](https://github.com/khushal075/streamlens/actions/workflows/ci.yml/badge.svg)](https://github.com/khushal075/streamlens/actions/workflows/ci.yml)

**StreamLens Ingestion Service** is a high-throughput, multi-tenant logging ingestion service built with **FastAPI**, designed for **real-time log collection**. It supports **durable queues** via **Redis** and can integrate with any message broker like **Kafka**.

---

## ⚡ Features

* Multi-tenant log ingestion via HTTP API (`/logs`)
* Rate limiting per tenant
* Durable queue using **Redis**
* Parallel enqueue for high throughput (`asyncio.gather`)
* Extensible for Kafka/Redis consumers
* Production-ready structure for scaling

---

## 🏗 Architecture

```
Client → FastAPI Ingestion → Rate Limiter → Durable Queue (Redis) → Consumer (Kafka / Processing Service)
```

### Components

* **API Layer**: FastAPI endpoints for log ingestion
* **Queue Layer**: Async, durable Redis queue
* **Worker Layer**: Background workers (future: Kafka producers)
* **Rate Limiter**: Tenant-level rate limiting
* **Models**: Pydantic models for structured logging
* **Services**: Business logic and buffering
* **Messaging**: Abstract layer to decouple queue/broker

---

## 📦 Installation

### 1. Clone Repository

```bash
git clone https://github.com/khushal075/streamlens.git
cd streamlens/ingestion-service
```

### 2. Install Dependencies

Using **uv (universe/poetry-style)** or `pip`:

```bash
uv install
# or
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start Redis

```bash
docker-compose -f ../infra/docker-compose.yml up -d redis
```

---

## 🚀 Running the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:

```
INFO:     Application startup complete.
```

---

## 📝 API Usage

### Endpoint

`POST /logs`

### Request

```json
{
  "tenant_id": "t1",
  "service": "test",
  "logs": [
    {"message": "This is a log", "timestamp": 1710000000}
  ]
}
```

### Response

```json
{
  "status": "accepted",
  "count": 1,
  "queue_size": 0
}
```

### Rate Limiting

* Controlled by `MAX_QUEUE_THRESHOLD` and tenant-level limits
* If exceeded: HTTP 429 or HTTP 503 returned

---

## 🔧 Queue

* **Redis** is used as a durable queue (`log_queue`)
* Logs are pushed using `enqueue()` in parallel (`asyncio.gather`)
* Consumers can later pull logs for processing

```bash
docker exec -it streamlens-redis redis-cli
127.0.0.1:6379> LLEN log_queue
(integer) 1
```

---

## 🛠 Folder Structure

```
ingestion-service/
├── app/
│   ├── api/          # FastAPI endpoints
│   ├── core/         # Config, logger
│   ├── queue/        # Redis queue / in-memory
│   ├── services/     # Business logic
│   ├── messaging/    # Kafka / Redis abstractions
│   ├── models/       # Pydantic models
│   └── workers/      # Background workers (Kafka producer)
├── pyproject.toml
├── Dockerfile
└── tests/
```

---

## ⚡ Production Tips

1. **Use Redis cluster** for high availability.
2. **Configure MAX_QUEUE_THRESHOLD** per your processing capacity.
3. **Run multiple ingestion instances** behind a load balancer.
4. **Integrate with Kafka / other message brokers** via `messaging/` abstraction.
5. **Monitor Redis queue** and alert if backlog grows.

---

## 📦 Docker Support

Build and run service with Docker:

```bash
docker build -t streamlens-ingestion .
docker run -p 8000:8000 --network host streamlens-ingestion
```

Or use **docker-compose**:

```yaml
services:
  ingestion-service:
    build: ./ingestion-service
    ports:
      - "8000:8000"
    depends_on:
      - redis
```

---

## ✅ Next Steps

* Implement **consumers** (Kafka / Redis) for processing logs.
* Add **DLQ support** for failed logs.
* Extend **pipeline** with enrichment, normalization, and indexing.

---

## 💡 References

* [FastAPI Docs](https://fastapi.tiangolo.com/)
* [Redis Docs](https://redis.io/docs/)
* [Asyncio](https://docs.python.org/3/library/asyncio.html)
* [aioredis](https://aioredis.readthedocs.io/)

---
