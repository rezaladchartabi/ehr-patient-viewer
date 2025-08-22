#!/bin/bash

# Frontend Startup Script
# This script properly starts the frontend with all necessary environment setup

set -e  # Exit on any error

echo "🚀 Starting EHR Frontend..."

# Set the working directory
cd "$(dirname "$0")"
echo "📁 Working directory: $(pwd)"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in $(pwd)"
    exit 1
fi

# Kill any existing node processes on port 3000
echo "🧹 Cleaning up existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 2

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Set environment variables for frontend
export REACT_APP_API_BASE_URL=http://localhost:8006

echo "🔧 Environment Configuration:"
echo "   REACT_APP_API_BASE_URL: $REACT_APP_API_BASE_URL"

# Start the frontend
echo "🚀 Starting React development server..."
exec npm start
