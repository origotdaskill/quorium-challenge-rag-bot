---
description: How to develop and run the RAG Q&A Chatbot
---

# Development Workflow

## Prerequisites
- Docker & Docker Compose installed
- Git installed
- (Optional) OpenAI API key for better responses

## First Time Setup

1. Clone the repository
2. Add documents to `/backend/documents/` folder
3. Build containers:
   ```bash
   ./docker.sh build
   ```

## Running the Application

1. Start all services:
   ```bash
   ./docker.sh up
   ```

2. Ingest documents (first time or when adding new documents):
   ```bash
   ./docker.sh ingest
   ```

3. Access the application:
   - Frontend: http://localhost:9755
   - Backend API: http://localhost:9754
   - API Docs: http://localhost:9754/docs

## Development Commands

- View logs: `./docker.sh logs`
- Stop services: `./docker.sh down`
- Rebuild after changes: `./docker.sh build`

## Adding New Documents

1. Place PDF, TXT, or MD files in `/backend/documents/`
2. Run ingestion: `./docker.sh ingest`
3. Documents will be chunked, embedded, and stored in ChromaDB

## Troubleshooting

- If ingestion fails, check document format compatibility
- Ensure Docker daemon is running
- Check logs with `./docker.sh logs`
