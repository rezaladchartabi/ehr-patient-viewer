#!/bin/bash

# Backend build script with optimization options
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUILD_TYPE="production"
IMAGE_NAME="ehr-backend"
TAG="latest"
NO_CACHE=false
PUSH_IMAGE=false
RAG_ENABLED=false

# Function to print colored output
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE        Build type: production (default) or development"
    echo "  -n, --name NAME        Image name (default: ehr-backend)"
    echo "  -g, --tag TAG          Image tag (default: latest)"
    echo "  --no-cache             Build without using cache"
    echo "  --push                 Push image after successful build"
    echo "  --rag                  Enable AI/RAG dependencies (slower build)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build production image"
    echo "  $0 -t development                     # Build development image"
    echo "  $0 -t production --no-cache          # Build without cache"
    echo "  $0 -t production --push              # Build and push image"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -g|--tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --rag)
            RAG_ENABLED=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate build type
if [[ "$BUILD_TYPE" != "production" && "$BUILD_TYPE" != "development" ]]; then
    print_error "Invalid build type: $BUILD_TYPE. Must be 'production' or 'development'"
    exit 1
fi

# Set Dockerfile based on build type
if [[ "$BUILD_TYPE" == "production" ]]; then
    DOCKERFILE="Dockerfile"
    print_status "Building production image..."
else
    DOCKERFILE="Dockerfile.dev"
    print_status "Building development image..."
fi

# Check if Dockerfile exists
if [[ ! -f "$DOCKERFILE" ]]; then
    print_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi

# Build command
BUILD_CMD="docker build"

if [[ "$NO_CACHE" == "true" ]]; then
    BUILD_CMD="$BUILD_CMD --no-cache"
    print_warning "Building without cache..."
fi

BUILD_CMD="$BUILD_CMD -f $DOCKERFILE --build-arg RAG_ENABLED=$RAG_ENABLED -t $IMAGE_NAME:$TAG ."

print_status "Build command: $BUILD_CMD"
print_status "RAG enabled: $RAG_ENABLED"
print_status "Starting build process..."

# Execute build
if eval $BUILD_CMD; then
    print_success "Build completed successfully!"
    
    # Show image info
    print_status "Image details:"
    docker images $IMAGE_NAME:$TAG
    
    # Push if requested
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        print_status "Pushing image..."
        if docker push $IMAGE_NAME:$TAG; then
            print_success "Image pushed successfully!"
        else
            print_error "Failed to push image"
            exit 1
        fi
    fi
    
    print_success "Backend build process completed!"
else
    print_error "Build failed!"
    exit 1
fi
