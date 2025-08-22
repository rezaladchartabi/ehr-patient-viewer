#!/bin/bash

# Backend Startup Script
# This script properly starts the backend with all necessary environment setup

set -e  # Exit on any error

echo "🚀 Starting EHR Backend..."

# Set the working directory
cd "$(dirname "$0")"
echo "📁 Working directory: $(pwd)"

# Load environment variables
if [ -f "env.config" ]; then
    echo "📋 Loading environment configuration..."
    export $(cat env.config | grep -v '^#' | xargs)
fi

# Set default environment variables if not set
export FHIR_BASE_URL=${FHIR_BASE_URL:-"http://localhost:8080/"}
export RATE_LIMIT_REQUESTS=${RATE_LIMIT_REQUESTS:-1000}
export RATE_LIMIT_WINDOW=${RATE_LIMIT_WINDOW:-60}
export PYTHONPATH=${PYTHONPATH:-"$(pwd)"}

echo "🔧 Environment Configuration:"
echo "   FHIR_BASE_URL: $FHIR_BASE_URL"
echo "   RATE_LIMIT_REQUESTS: $RATE_LIMIT_REQUESTS"
echo "   RATE_LIMIT_WINDOW: $RATE_LIMIT_WINDOW"
echo "   PYTHONPATH: $PYTHONPATH"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in $(pwd)"
    exit 1
fi

# Kill any existing uvicorn processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*main:app" || true
sleep 2

# Check if port is available
PORT=${PORT:-8006}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port $PORT is already in use. Attempting to free it..."
    lsof -ti:$PORT | xargs kill -9 || true
    sleep 2
fi

# Activate virtual environment if it exists
if [ -f "../.venv/bin/activate" ]; then
    echo "🐍 Activating virtual environment..."
    source ../.venv/bin/activate
fi

# Install dependencies if needed
if [ ! -d "../.venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv ../.venv
    source ../.venv/bin/activate
    pip install -r requirements.txt
fi

# Start the backend
echo "🚀 Starting uvicorn server on port $PORT..."
exec python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT --reload
