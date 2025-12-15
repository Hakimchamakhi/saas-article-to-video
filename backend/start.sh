#!/bin/bash
# Start script that runs both the web server and Celery worker

# Start Celery worker in the background with ONE process
celery -A worker.celery_app worker --loglevel=info --concurrency=1 &

# Start the FastAPI web server in the foreground
uvicorn main:app --host 0.0.0.0 --port $PORT
