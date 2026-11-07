# Stage 1: React SPA
# The SPA is built locally and committed under frontend/build/ (un-ignored on
# 2026-11-07).  Railway deploys the COMMITTED build verbatim — no Docker rebuild
# of the SPA — so the exact tested bundle (main.37112e99.js, all routes inlined,
# every lazy chunk present) is what reaches the live site.  A Docker rebuild here
# silently re-introduced the stale data-router bundle that crashed navigation.
FROM scratch AS frontend-builder

COPY frontend/build /frontend/build

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
