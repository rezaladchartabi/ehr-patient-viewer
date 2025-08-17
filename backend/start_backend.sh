#!/bin/bash

# Backend startup script - ensures correct directory and proper startup

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Starting backend from: $SCRIPT_DIR"

# Change to the backend directory
cd "$SCRIPT_DIR" || {
    echo "ERROR: Failed to change to backend directory: $SCRIPT_DIR"
    exit 1
}

# Check if we're in the right directory (should contain main.py)
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in current directory. Current directory: $(pwd)"
    echo "Expected to be in: $SCRIPT_DIR"
    exit 1
fi

echo "✅ Backend directory confirmed: $(pwd)"
echo "✅ main.py found"

# Kill any existing uvicorn processes
echo "🔄 Stopping any existing backend processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 2

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is still in use. Attempting to kill processes on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start the backend
echo "🚀 Starting backend server..."
echo "📁 Working directory: $(pwd)"
echo "🔗 Server will be available at: http://localhost:8000"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
