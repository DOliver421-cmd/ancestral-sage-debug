FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — this layer is cached unless requirements.txt changes.
# Heavy packages (tiktoken, pydantic-core, cryptography) only recompile when
# requirements.txt is modified, keeping normal code-change builds under 2 minutes.
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (changes frequently — fast layer)
COPY . .

EXPOSE 10000

# Use shell form so Railway's $PORT variable is expanded correctly
CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}
