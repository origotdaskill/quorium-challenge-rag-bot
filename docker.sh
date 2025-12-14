#!/bin/bash

# ============================================
# RAG Q&A Chatbot - Docker Management Script
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function for colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show help message
show_help() {
    echo ""
    echo "RAG Q&A Chatbot - Docker Management Script"
    echo "==========================================="
    echo ""
    echo "Usage: ./docker.sh <command>"
    echo ""
    echo "Commands:"
    echo "  build       Build all Docker containers"
    echo "  up          Start all services"
    echo "  down        Stop all services"
    echo "  ingest      Run document ingestion"
    echo "  logs        View logs (follow mode)"
    echo "  logs-all    View all logs without following"
    echo "  status      Check status of all services"
    echo "  clean       Remove all containers and volumes"
    echo "  ollama      Start with Ollama LLM support"
    echo "  pull-model  Pull Ollama model (llama2 by default)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docker.sh build     # Build containers"
    echo "  ./docker.sh up        # Start services"
    echo "  ./docker.sh ingest    # Ingest documents"
    echo "  ./docker.sh logs      # View logs"
    echo ""
}

# Build all containers
build() {
    log_info "Building Docker containers..."
    docker compose build --no-cache
    log_success "Build completed successfully!"
}

# Start all services
up() {
    log_info "Starting all services..."
    docker compose up -d
    log_success "Services started!"
    echo ""
    log_info "Access the application at:"
    echo "  - Frontend:  http://localhost:9755"
    echo "  - Backend:   http://localhost:9754"
    echo "  - API Docs:  http://localhost:9754/docs"
    echo ""
    log_info "Run './docker.sh ingest' to ingest documents"
}

# Start with Ollama support
up_ollama() {
    log_info "Starting all services with Ollama LLM..."
    docker compose --profile ollama up -d
    log_success "Services started with Ollama!"
    echo ""
    log_info "Access the application at:"
    echo "  - Frontend:  http://localhost:9755"
    echo "  - Backend:   http://localhost:9754"
    echo "  - API Docs:  http://localhost:9754/docs"
    echo "  - Ollama:    http://localhost:11434"
    echo ""
    log_warning "Don't forget to pull a model: ./docker.sh pull-model"
}

# Stop all services
down() {
    log_info "Stopping all services..."
    docker compose --profile ollama down
    log_success "Services stopped!"
}

# Run document ingestion
ingest() {
    log_info "Running document ingestion..."
    
    # Check if documents directory exists and has files
    if [ ! -d "./backend/documents" ]; then
        mkdir -p ./backend/documents
        log_warning "Created documents directory. Add your PDF/TXT/MD files to ./backend/documents/"
    fi
    
    file_count=$(find ./backend/documents -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.md" \) 2>/dev/null | wc -l)
    
    if [ "$file_count" -eq "0" ]; then
        log_warning "No documents found in ./backend/documents/"
        log_info "Add PDF, TXT, or MD files to the documents folder and run ingestion again."
        exit 1
    fi
    
    log_info "Found $file_count document(s) to ingest..."
    
    # Wait for ChromaDB to be ready
    log_info "Waiting for ChromaDB to be ready..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:9753/api/v1/heartbeat > /dev/null 2>&1; then
            log_success "ChromaDB is ready!"
            break
        fi
        attempt=$((attempt + 1))
        log_info "Waiting for ChromaDB... ($attempt/$max_attempts)"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "ChromaDB is not responding. Please check 'docker compose logs chromadb'"
        exit 1
    fi
    
    # Run ingestion in the backend container
    docker compose exec backend python ingestion.py
    
    log_success "Document ingestion completed!"
}

# View logs
logs() {
    log_info "Viewing logs (press Ctrl+C to exit)..."
    docker compose logs -f
}

# View all logs without following
logs_all() {
    docker compose logs
}

# Check status
status() {
    log_info "Checking service status..."
    echo ""
    docker compose ps
    echo ""
    
    # Check health endpoints
    log_info "Checking health endpoints..."
    
    if curl -s http://localhost:9754/health > /dev/null 2>&1; then
        log_success "Backend: Healthy"
    else
        log_error "Backend: Not responding"
    fi
    
    if curl -s http://localhost:9755 > /dev/null 2>&1; then
        log_success "Frontend: Healthy"
    else
        log_error "Frontend: Not responding"
    fi
    
    if curl -s http://localhost:9753/api/v1/heartbeat > /dev/null 2>&1; then
        log_success "ChromaDB: Healthy"
    else
        log_error "ChromaDB: Not responding"
    fi
}

# Clean up everything
clean() {
    log_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        docker compose --profile ollama down -v --rmi all
        log_success "Cleanup completed!"
    else
        log_info "Cleanup cancelled."
    fi
}

# Pull Ollama model
pull_model() {
    model="${1:-llama2}"
    log_info "Pulling Ollama model: $model"
    docker compose exec ollama ollama pull $model
    log_success "Model $model pulled successfully!"
}

# Main command handler
case "$1" in
    build)
        build
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    ingest)
        ingest
        ;;
    logs)
        logs
        ;;
    logs-all)
        logs_all
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    ollama)
        up_ollama
        ;;
    pull-model)
        pull_model "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            log_error "Unknown command: $1"
            show_help
            exit 1
        fi
        ;;
esac
