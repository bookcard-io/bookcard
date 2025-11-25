#!/bin/bash
set -e

# Function to handle shutdown gracefully
shutdown() {
    echo "Received shutdown signal, stopping services..."
    if [ -n "$BACKEND_PID" ]; then
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    fi
    # Wait for processes to exit
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT

# Start backend in background using full path to uvicorn from virtual environment
echo "Starting backend server on port 8000..."
/opt/venv/bin/uvicorn fundamental.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start frontend in background
echo "Starting frontend server on port 3000..."
cd /app/web && npm start &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
