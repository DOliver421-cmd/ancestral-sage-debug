FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY backend/ /app/backend/
COPY src/ /app/backend/src/
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

WORKDIR /app/backend

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}
