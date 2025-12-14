"""
Configuration settings for the RAG application.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    app_name: str = "RAG Q&A Chatbot"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # ChromaDB Settings
    chroma_host: str = os.getenv("CHROMA_HOST", "chromadb")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "9754"))
    chroma_collection: str = "documents"
    
    # LLM Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "bedrock")  # 'openai', 'ollama', or 'bedrock'
    
    # OpenAI Settings
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Ollama Settings
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # AWS Bedrock Settings
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    
    # Embedding Settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5  # Number of relevant chunks to retrieve
    
    # Document Settings
    documents_path: str = "/app/documents"
    
    class Config:
        env_file = ".env"


settings = Settings()
