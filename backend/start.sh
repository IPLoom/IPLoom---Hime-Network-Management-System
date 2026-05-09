#!/bin/bash

# Extract APP_ENV from .env file safely (avoiding issues with unquoted spaces/comments)
if [ -f .env ]; then
    APP_ENV=$(grep '^APP_ENV=' .env | cut -d '=' -f2 | tr -d '\r')
fi

# Default settings
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
APP_MODULE=${APP_MODULE:-"app.main:app"}

echo "🚀 Starting IPLoom in $APP_ENV mode..."

if [ "$APP_ENV" = "development" ]; then
    echo "🛠️  Development mode: Hot reload enabled."
    # Use --reload-dir app to avoid glob expansion errors on Windows
    exec python -m uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --reload --reload-dir app
else
    echo "🏭 Production mode: Running with $WORKERS worker(s)."
    exec python -m uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --workers "$WORKERS"
fi
