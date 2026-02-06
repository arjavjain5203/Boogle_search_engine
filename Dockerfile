FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create storage directories
RUN mkdir -p boogle/storage/data/raw \
    && mkdir -p boogle/storage/data/index

# Render uses $PORT (usually 10000)
EXPOSE 10000

# Start with Gunicorn (PRODUCTION SAFE)
CMD gunicorn boogle.frontend.app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 120
