#!/bin/bash

# Auto-ingest RAG data after deployment
# This script can be called from Render's post-deploy hook

set -e

echo "🚀 Starting automatic RAG data ingestion..."

# Configuration
BACKEND_URL=${BACKEND_URL:-"https://ehr-backend-87r9.onrender.com"}
JSONL_FILE="rag_chunks.jsonl"
BATCH_SIZE=10

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s "$BACKEND_URL/" > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    echo "⏳ Attempt $i/30: Backend not ready yet..."
    sleep 10
done

# Check if RAG data exists
echo "🔍 Checking if RAG data exists..."
RAG_COUNT=$(curl -s -X POST "$BACKEND_URL/rag/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' | jq '.hits | length')

if [ "$RAG_COUNT" -gt 0 ]; then
    echo "✅ RAG data already exists ($RAG_COUNT documents), skipping ingestion"
    exit 0
fi

# Ingest data
echo "📥 Starting data ingestion..."
if [ -f "$JSONL_FILE" ]; then
    node scripts/rag_ingest.js \
        --jsonl "$JSONL_FILE" \
        --url "$BACKEND_URL" \
        --batch "$BATCH_SIZE"
    echo "✅ Data ingestion completed!"
else
    echo "❌ $JSONL_FILE not found!"
    exit 1
fi

# Verify ingestion
echo "🔍 Verifying ingestion..."
FINAL_COUNT=$(curl -s -X POST "$BACKEND_URL/rag/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' | jq '.hits | length')

echo "📊 Final RAG document count: $FINAL_COUNT"
