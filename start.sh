#!/bin/bash
# Start Celery worker in the background
celery -A src.worker.celery_app worker --loglevel=info --concurrency=1 &

# Start FastAPI server in the foreground
uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-10000}


#uvicorn api.server:app --host 0.0.0.0 --port 10000