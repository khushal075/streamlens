# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN pip install --no-cache-dir uv

# Set working directory to root to see both folders
WORKDIR /build

# Copy the common library and the service
COPY common/ ./common/
COPY ingestion-service/ ./ingestion-service/

# Install the common library first, then the service
# This ensures common is available as a package
RUN cd common && pip install .
RUN cd ingestion-service && pip install .

# Stage 2: Final Image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only the application code
COPY ingestion-service/app ./app

# Default environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Note: The 'command' will be overridden in docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]