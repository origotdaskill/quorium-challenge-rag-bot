"""
FastAPI application for the RAG Q&A Chatbot.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging

from config import settings
from rag import get_rag_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A RAG-powered Q&A chatbot that answers questions based on ingested documents.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the main topic of the documents?"
            }
        }


class AnswerResponse(BaseModel):
    """Response model for the answer."""
    answer: str
    sources: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The documents discuss...",
                "sources": ["document1.pdf", "document2.txt"]
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - returns API info."""
    return HealthResponse(
        status="ok",
        message=f"Welcome to {settings.app_name}! Visit /docs for API documentation."
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get the RAG pipeline to verify connections
        rag = get_rag_pipeline()
        if rag.collection is None:
            return HealthResponse(
                status="warning",
                message="Service is running but no documents have been ingested yet."
            )
        return HealthResponse(
            status="ok",
            message="Service is healthy and documents are available."
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            message=f"Service is experiencing issues: {str(e)}"
        )


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get an answer based on ingested documents.
    
    The RAG pipeline will:
    1. Convert the question to an embedding
    2. Retrieve relevant document chunks from the vector database
    3. Use an LLM to generate an answer based on the retrieved context
    4. Return the answer along with source documents
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        rag = get_rag_pipeline()
        result = rag.ask(request.question.strip())
        
        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)}"
        )


@app.get("/stats")
async def get_stats():
    """Get statistics about ingested documents."""
    try:
        rag = get_rag_pipeline()
        if rag.collection is None:
            return {
                "status": "no_data",
                "message": "No documents have been ingested yet.",
                "total_chunks": 0
            }
        
        count = rag.collection.count()
        return {
            "status": "ok",
            "total_chunks": count,
            "collection_name": settings.chroma_collection
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9754)
