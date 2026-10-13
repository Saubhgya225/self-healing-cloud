FROM python:3.11-slim

LABEL maintainer="Saubhagya <saubhagyadeept@gmail.com>"
LABEL description="Self-Healing Cloud Infrastructure Platform"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY dashboard/ ./dashboard/
RUN mkdir -p results

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
