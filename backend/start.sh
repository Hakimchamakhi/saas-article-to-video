#!/bin/bash
# Start script that runs both the web server and Celery worker

# Start Celery worker in the background
celery -A worker.celery_app worker --loglevel=info &

# Start the FastAPI web server in the foreground
uvicorn main:app --host 0.0.0.0 --port $PORT
