# Use Python 3.10 Slim for minimal image size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=boogle.frontend.app

# Install system dependencies
# build-essential: for compiling some python extensions
# curl: for healthchecks or downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Use CPU-only PyTorch index to keep image size small (~1GB instead of 3GB)
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Download NLTK data (stopwords) during build to avoid runtime download
RUN python3 -c "import nltk; nltk.download('stopwords')"

# Copy project files
COPY . .

# Create storage directory structure
RUN mkdir -p boogle/storage/data/raw \
    && mkdir -p boogle/storage/data/index \
    && chmod -R 777 boogle/storage

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port (Documentation only, usually ignored by PaaS)
EXPOSE 5000

# Use the entrypoint script
CMD ["./entrypoint.sh"]
