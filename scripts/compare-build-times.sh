#!/bin/bash

# Script to compare build times with and without AI dependencies
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  Backend Build Time Comparison"
echo "=========================================="
echo ""

print_status "This script will build the backend twice:"
echo "  1. Without AI dependencies (fast)"
echo "  2. With AI dependencies (slow)"
echo ""

# Build without AI dependencies
print_status "Building WITHOUT AI dependencies..."
start_time=$(date +%s)
if ./scripts/build-backend.sh -t development --no-cache; then
    end_time=$(date +%s)
    time_without_ai=$((end_time - start_time))
    print_success "Build without AI completed in ${time_without_ai} seconds"
else
    print_error "Build without AI failed!"
    exit 1
fi

echo ""

# Build with AI dependencies
print_status "Building WITH AI dependencies..."
start_time=$(date +%s)
if ./scripts/build-backend.sh -t development --no-cache --rag; then
    end_time=$(date +%s)
    time_with_ai=$((end_time - start_time))
    print_success "Build with AI completed in ${time_with_ai} seconds"
else
    print_error "Build with AI failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Results Summary"
echo "=========================================="
echo ""
echo "Build time WITHOUT AI: ${time_without_ai} seconds"
echo "Build time WITH AI:    ${time_with_ai} seconds"
echo ""

# Calculate difference
time_diff=$((time_with_ai - time_without_ai))
percentage_increase=$((time_diff * 100 / time_without_ai))

echo "Time difference: ${time_diff} seconds"
echo "Percentage increase: ${percentage_increase}%"
echo ""

if [ $time_diff -gt 0 ]; then
    print_warning "AI dependencies add ${time_diff} seconds to build time"
    print_warning "That's a ${percentage_increase}% increase!"
else
    print_success "No significant time difference detected"
fi

echo ""
print_status "Recommendation:"
echo "  - Use '--rag' flag only when you need AI features"
echo "  - For development without RAG, skip AI dependencies"
echo "  - For production, decide based on your feature requirements"
