#!/bin/bash

# Master Startup Script for EHR System
# This script starts all services in the correct order

set -e  # Exit on any error

echo "🚀 Starting EHR System..."

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $port is already in use"
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn.*main:app" || true
pkill -f "react-scripts" || true
sleep 2

# Check ports
echo "🔌 Checking port availability..."
check_port 8006 || {
    echo "⚠️  Attempting to free port 8006..."
    lsof -ti:8006 | xargs kill -9 || true
    sleep 2
}

check_port 3000 || {
    echo "⚠️  Attempting to free port 3000..."
    lsof -ti:3000 | xargs kill -9 || true
    sleep 2
}

# Start backend
echo "🚀 Starting backend..."
cd backend
chmod +x start_backend.sh
./start_backend.sh &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
wait_for_service "http://localhost:8006/health" "Backend" || {
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
}

# Start frontend
echo "🚀 Starting frontend..."
chmod +x start_frontend.sh
./start_frontend.sh &
FRONTEND_PID=$!

# Wait for frontend to be ready
wait_for_service "http://localhost:3000" "Frontend" || {
    echo "❌ Frontend failed to start"
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
}

echo ""
echo "🎉 EHR System is now running!"
echo "   Backend: http://localhost:8006"
echo "   Frontend: http://localhost:3000"
echo "   Health Check: http://localhost:8006/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "uvicorn.*main:app" || true
    pkill -f "react-scripts" || true
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
