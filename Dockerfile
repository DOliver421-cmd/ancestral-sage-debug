FROM python:3.12-slim

WORKDIR /app

COPY backend/ /app/backend/
COPY src/ /app/src/

ENV PYTHONPATH=/app/backend:/app

WORKDIR /app/backend

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}
