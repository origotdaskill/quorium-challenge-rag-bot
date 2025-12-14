# RAG Q&A Chatbot - Project Context (Updated)

## Project Status: COMPLETE ✅

All files have been created. The project uses **AWS Bedrock** as the default LLM provider.

## ⚠️ SECURITY REMINDER
The AWS credentials were shared in chat. **ROTATE THEM IMMEDIATELY** after testing:
1. Go to AWS IAM Console
2. Create new access keys
3. Deactivate/delete the exposed keys
4. Update the `.env` file with new keys

## Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: Next.js 14 (React/TypeScript)
- **Vector Database**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: AWS Bedrock (Claude 3 Haiku by default)
- **Infrastructure**: Docker, Docker Compose

## LLM Providers Supported

| Provider | Model Examples |
|----------|---------------|
| **AWS Bedrock** (default) | Claude 3 Haiku, Claude 3.5 Sonnet, Llama 3, Mistral, Titan |
| OpenAI | GPT-3.5 Turbo, GPT-4 |
| Ollama | Llama 2, Mistral (local) |

## Quick Start

### 1. Create `.env` file
```bash
cp .env.example .env
```

Then edit `.env` with your AWS credentials:
```env
LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=your-key-here
AWS_SECRET_ACCESS_KEY=your-secret-here
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

### 2. Build & Run
```bash
./docker.sh build
./docker.sh up
./docker.sh ingest
```

### 3. Access
- Frontend: http://localhost:9755
- Backend: http://localhost:9754
- API Docs: http://localhost:9754/docs

## Available Bedrock Models

| Model | ID |
|-------|-------|
| Claude 3 Haiku (fast) | `anthropic.claude-3-haiku-20240307-v1:0` |
| Claude 3 Sonnet | `anthropic.claude-3-sonnet-20240229-v1:0` |
| Claude 3.5 Sonnet (best) | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| Llama 3 8B | `meta.llama3-8b-instruct-v1:0` |
| Llama 3 70B | `meta.llama3-70b-instruct-v1:0` |
| Mistral 7B | `mistral.mistral-7b-instruct-v0:2` |
| Amazon Titan | `amazon.titan-text-express-v1` |

## Project Structure

```
/backend
  /app
    main.py           # FastAPI with POST /ask
    rag.py            # RAG pipeline + AWS Bedrock
    ingestion.py      # Document processing
    config.py         # Settings
  /documents          # Add your documents here
  Dockerfile
  requirements.txt
/frontend
  /app                # Next.js pages
  Dockerfile
docker-compose.yml
docker.sh
.env                  # Your credentials (gitignored)
.env.example          # Template
README.md
```

## API Endpoints

### POST /ask
```json
Request: { "question": "Your question..." }
Response: { "answer": "...", "sources": ["doc1.pdf"] }
```
