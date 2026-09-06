# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

ARG CACHE_BUST=20260831
COPY frontend/ ./

# REACT_APP_BACKEND_URL is baked in at build time.
# On Railway, set this in the service's Variables panel.
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# CRA fails the build on ESLint warnings when CI=true. CI=false keeps the
# build deterministic across environments while still failing on real
# errors (rules-of-hooks and other error-severity issues fail either way).
ENV CI=false

# Hardening for Railway builds (Node 18 / OpenSSL 3 / limited build RAM):
#  - --openssl-legacy-provider: Node 17+ OpenSSL 3 breaks webpack's MD4
#    hashing -> "digital envelope routines::unsupported" build crash.
#  - --max-old-space-size: CRA/craco builds can exceed Railway's default
#    build RAM and get silently OOM-killed mid-build.
ENV NODE_OPTIONS=--openssl-legacy-provider --max-old-space-size=2048

RUN npm run build

# Stage 2: Python backend — includes the built frontend so SERVE_FRONTEND=1 works
FROM python:3.11-slim

WORKDIR /app

COPY backend/ /app/backend/

# Copy the seeded content (starter-library manuscripts) into the image —
# served by GET /api/media/content/{path}
COPY content/ /app/content/

# Copy the built React app into the location server.py checks first
COPY --from=frontend-builder /frontend/build /app/frontend/build

# Copy entrypoint script for proper signal handling and PORT variable substitution
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENV PYTHONPATH=/app:/app/backend

# Serve the baked React SPA from the backend (single-service topology) so the
# frontend's same-origin /api calls reach this server without CORS or a
# separate frontend deployment. Override with SERVE_FRONTEND=0 for API-only.
ENV SERVE_FRONTEND=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libc-dev \
    libpq-dev \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
