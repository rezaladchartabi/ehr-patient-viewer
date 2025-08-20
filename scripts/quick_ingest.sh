#!/bin/bash

echo "🚀 Quick RAG Data Ingestion"
echo "=========================="

# Configuration
BACKEND_URL="https://ehr-backend-87r9.onrender.com"
JSONL_FILE="rag_chunks.jsonl"

echo "📡 Backend URL: $BACKEND_URL"
echo "📄 Data file: $JSONL_FILE"

# Check if backend is ready
echo "⏳ Checking backend status..."
if curl -s "$BACKEND_URL/" > /dev/null; then
    echo "✅ Backend is ready!"
else
    echo "❌ Backend is not responding!"
    exit 1
fi

# Check if data file exists
if [ ! -f "$JSONL_FILE" ]; then
    echo "❌ Data file $JSONL_FILE not found!"
    echo "💡 Run 'npm run chunk:notes' first to generate the data file"
    exit 1
fi

# Ingest data
echo "📥 Starting ingestion..."
node scripts/rag_ingest.js \
    --jsonl "$JSONL_FILE" \
    --url "$BACKEND_URL" \
    --batch 10

echo "✅ Ingestion completed!"
echo "🔍 Testing search..."
curl -s -X POST "$BACKEND_URL/rag/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "discharge"}' | jq '.hits | length' | xargs echo "�� Documents found:"
