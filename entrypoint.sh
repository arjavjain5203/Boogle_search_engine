#!/bin/bash
set -e

# Default to port 5000 if PORT is not set
PORT=${PORT:-5000}

# Start Gunicorn
# -w 1: One worker (save ram)
# --threads 4: Concurrency
# --timeout 120: Allow slow searches
exec gunicorn boogle.frontend.app:app \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 120
