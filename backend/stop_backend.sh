#!/bin/bash

# Backend stop script

echo "🛑 Stopping backend server..."

# Kill uvicorn processes
pkill -f "uvicorn main:app" 2>/dev/null || true

# Kill any processes on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Killing processes on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

echo "✅ Backend stopped"
