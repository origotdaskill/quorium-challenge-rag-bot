# RAG Q&A Chatbot

A Retrieval-Augmented Generation (RAG) application that answers questions based on a set of documents.

![RAG Chatbot](https://img.shields.io/badge/RAG-Chatbot-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## 🚀 Features

- **Document Ingestion**: Parse PDF, TXT, and MD files
- **Vector Search**: ChromaDB for efficient similarity search
- **Modern UI**: Beautiful Next.js chat interface with dark theme
- **Flexible LLM**: Support for OpenAI API or local Ollama
- **Docker Ready**: One-command deployment with Docker Compose

## 📁 Project Structure

```
/backend
  /app
    main.py           # FastAPI application
    rag.py            # RAG pipeline logic
    ingestion.py      # Document processing
    config.py         # Configuration
  /documents          # Place your documents here
  Dockerfile
  requirements.txt
/frontend
  /app                # Next.js app
  Dockerfile
  package.json
docker-compose.yml
docker.sh             # Management script
README.md
```

## 🛠️ Prerequisites

- Docker & Docker Compose
- Git
- (Optional) OpenAI API key for enhanced responses

## 🏃 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rag-chatbot
```

### 2. Add Documents

Place your PDF, TXT, or MD files in the `./backend/documents/` directory.

### 3. Build & Run

```bash
# Make the script executable (Linux/Mac)
chmod +x docker.sh

# Build containers
./docker.sh build

# Start services
./docker.sh up

# Ingest documents
./docker.sh ingest
```

### 4. Access the Application

- **Frontend**: http://localhost:9755
- **Backend API**: http://localhost:9754
- **API Documentation**: http://localhost:9754/docs

## 📚 Docker Commands

| Command | Description |
|---------|-------------|
| `./docker.sh build` | Build all Docker containers |
| `./docker.sh up` | Start all services |
| `./docker.sh down` | Stop all services |
| `./docker.sh ingest` | Run document ingestion |
| `./docker.sh logs` | View logs (follow mode) |
| `./docker.sh status` | Check service status |
| `./docker.sh clean` | Remove containers and volumes |

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Provider: 'openai' or 'ollama'
LLM_PROVIDER=ollama

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Ollama Configuration (if using Ollama)
OLLAMA_MODEL=llama2

# Debug Mode
DEBUG=false
```

### Using OpenAI

1. Set `LLM_PROVIDER=openai` in `.env`
2. Add your `OPENAI_API_KEY`
3. Restart services: `./docker.sh down && ./docker.sh up`

### Using Ollama (Local LLM)

1. Start with Ollama profile:
   ```bash
   ./docker.sh ollama
   ```
2. Pull a model:
   ```bash
   ./docker.sh pull-model llama2
   ```

## 📡 API Endpoints

### POST /ask

Ask a question about ingested documents.

**Request:**
```json
{
  "question": "What is the main topic of the documents?"
}
```

**Response:**
```json
{
  "answer": "The documents discuss...",
  "sources": ["document1.pdf", "document2.txt"]
}
```

### GET /health

Health check endpoint.

### GET /stats

Get statistics about ingested documents.

## 🏗️ Architecture & Decisions
    
### Decisions & Tradeoffs

1. **Docker-First Approach**: 
   - **Decision**: Encapsulate everything in Docker using a custom `docker.sh` wrapper.
   - **Tradeoff**: Increases initial complexity but guarantees consistency across different machines (eliminates "it works on my machine" issues).
   - **Validation**: All commands (build, up, ingest) run via `./docker.sh` as required.

2. **ChromaDB as Vector Store**:
   - **Decision**: Used ChromaDB for storing embeddings.
   - **Reason**: It's open-source, lightweight, and integrates easily with Python/FastAPI without needing a complex external setup.
   - **Tradeoff**: Running it locally inside Docker adds some memory overhead compared to a cloud solution like Pinecone.

3. **FastAPI Backend**:
   - **Decision**: Used FastAPI for the backend.
   - **Reason**: Native async support, automatic API documentation (Swagger UI), and type safety with Pydantic. It is the industry standard for AI backends.

4. **Next.js Frontend**:
   - **Decision**: Used Next.js with functional React components.
   - **Reason**: Provides a robust framework for building modern, responsive UIs. The chat interface is kept minimal to focus on functionality.

### RAG Pipeline Details

The Retrieval-Augmented Generation (RAG) pipeline handles the core logic:

1.  **Ingestion (`/ingest`)**:
    *   **Parsing**: Supports `.pdf` (via PyPDF2), `.txt`, and `.md` (via markdown library).
    *   **Chunking**: Splits text into 500-token chunks with 50-token overlap to preserve context across boundaries.
    *   **Embedding**: Uses `all-MiniLM-L6-v2` (SentenceTransformer) to convert chunks into vector embeddings.
    *   **Storage**: Vectors are stored locally in the `chroma_data` volume.

2.  **Retrieval & Generation (`/ask`)**:
    *   **Embed Query**: The user's question is embedded using the same model.
    *   **Search**: ChromaDB finds the top-5 most similar chunks (Cosine Similarity).
    *   **Context Construction**: Retrieved text is assembled into a prompt.
    *   **Answer**: The LLM (via OpenAI or Ollama) generates a natural language response based *only* on the provided context.

## 🚀 Next Steps (Future Improvements)

1.  **Hybrid Search**: Combine vector search with keyword search (BM25) for better accuracy on specific terms.
2.  **Streaming Responses**: Implement Server-Sent Events (SSE) to stream the answer character-by-character for a better UX.
3.  **Conversation Memory**: Pass previous chat history to the LLM to allow follow-up questions.
4.  **Metadata Filtering**: Allow filtering by document source or date.

## 🧪 Development

### Local Development (without Docker)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9754
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 Adding New Documents

1. Add files to `./backend/documents/`
2. Run ingestion: `./docker.sh ingest`
3. Ask questions about the new content!

## 🐛 Troubleshooting

### Services not starting
```bash
./docker.sh logs
```

### ChromaDB connection issues
Wait 30 seconds after `./docker.sh up` for ChromaDB to initialize.

### No documents ingested
Ensure documents are in `./backend/documents/` and run `./docker.sh ingest`.

### LLM not responding
Check if using OpenAI (needs API key) or Ollama (needs model pulled).

## 📄 License

MIT License

## 👤 Author

Built for AI Engineer Trainee Coding Challenge
