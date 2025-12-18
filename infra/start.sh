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

# Function to ensure BOOKCARD_FERNET_KEY is set
ensure_fernet_key() {
    local key_file="/data/fernet_key"

    # If already set in environment, use it
    if [ -n "$BOOKCARD_FERNET_KEY" ]; then
        echo "Using BOOKCARD_FERNET_KEY from environment"
        return
    fi

    # If key file exists, read from it
    if [ -f "$key_file" ]; then
        echo "Reading BOOKCARD_FERNET_KEY from persisted file"
        export BOOKCARD_FERNET_KEY=$(cat "$key_file")
        return
    fi

    # Generate new key and save it
    echo "Generating new BOOKCARD_FERNET_KEY and saving to $key_file"
    export BOOKCARD_FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "$BOOKCARD_FERNET_KEY" > "$key_file"
    chmod 600 "$key_file"
    echo "BOOKCARD_FERNET_KEY saved to $key_file"
}

# Ensure Fernet key is set before starting services
ensure_fernet_key

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT

# Start backend in background using full path to uvicorn from virtual environment
echo "Starting backend server on port 8000..."
/opt/venv/bin/uvicorn bookcard.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start frontend in background
echo "Starting frontend server on port 3000..."
cd /app/web && npm start &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
