# Use Python 3.10 Slim for smaller image size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Point Flask to the app
    FLASK_APP=boogle.frontend.app

# Install system dependencies (needed for some python packages like numpy/faiss)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create storage directory structure
RUN mkdir -p boogle/storage/data/raw \
    && mkdir -p boogle/storage/data/index

# Expose port 5000
EXPOSE 5000

# Default command (can be overridden by docker-compose)
CMD ["python3", "-m", "boogle.frontend.app"]
