# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

ARG CACHE_BUST=20260609a
COPY frontend/ ./

# REACT_APP_BACKEND_URL is baked in at build time.
# On Railway, set this in the service's Variables panel.
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npm run build

# Stage 2: Python backend — includes the built frontend so SERVE_FRONTEND=1 works
FROM python:3.11-slim

WORKDIR /app

COPY backend/ /app/backend/
COPY src/ /app/src/
COPY app/ /app/app/

# Copy the built React app into the location server.py checks first
COPY --from=frontend-builder /frontend/build /app/frontend/build

ENV PYTHONPATH=/app/backend:/app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

WORKDIR /app

EXPOSE 8080

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
