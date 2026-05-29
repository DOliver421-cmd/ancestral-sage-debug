FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY backend/ /app/backend/
COPY src/ /app/src/
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

ENV PYTHONPATH=/app/backend:/app
ENV SERVE_FRONTEND=1

WORKDIR /app/backend

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}
