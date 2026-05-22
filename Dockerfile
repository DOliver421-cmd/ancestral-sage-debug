FROM python:3.11-slim

WORKDIR /app

# Copy Python source files
COPY server.py /app/
COPY requirements.txt /app/

# Copy subdirectories that contain Python modules
COPY ai/ /app/ai/
COPY billing/ /app/billing/
COPY contracts/ /app/contracts/
COPY crm/ /app/crm/
COPY migrations/ /app/migrations/
COPY prompts/ /app/prompts/
COPY scripts/ /app/scripts/

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}
