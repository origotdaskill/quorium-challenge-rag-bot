"""
RAG (Retrieval-Augmented Generation) pipeline module.
Handles query processing, retrieval, and answer generation.
"""
import json
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging
import httpx
from openai import OpenAI

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Implements the RAG pipeline for question answering."""
    
    def __init__(self):
        """Initialize the RAG pipeline."""
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.chroma_client = self._init_chroma_client()
        self.collection = self._get_collection()
        self.llm_client = self._init_llm_client()
        self.bedrock_client = self._init_bedrock_client()
    
    def _init_chroma_client(self) -> chromadb.HttpClient:
        """Initialize ChromaDB client with retries."""
        import time
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to ChromaDB at {settings.chroma_host}:{settings.chroma_port} (Attempt {attempt + 1}/{max_retries})")
                client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                    settings=ChromaSettings(
                        anonymized_telemetry=False
                    )
                )
                # Verify connection
                client.heartbeat()
                logger.info("Successfully connected to ChromaDB")
                return client
            except Exception as e:
                logger.warning(f"Connection failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Could not connect to ChromaDB after multiple attempts.")
                    raise e
        return None
    
    def _get_collection(self):
        """Get the document collection."""
        try:
            return self.chroma_client.get_collection(name=settings.chroma_collection)
        except Exception as e:
            logger.warning(f"Collection not found: {e}. Please run ingestion first.")
            return None
    
    def _init_llm_client(self):
        """Initialize the OpenAI client if configured."""
        if settings.llm_provider == "openai" and settings.openai_api_key:
            logger.info("Using OpenAI as LLM provider")
            return OpenAI(api_key=settings.openai_api_key)
        return None
    
    def _init_bedrock_client(self):
        """Initialize the AWS Bedrock client if configured."""
        if settings.llm_provider == "bedrock" and settings.aws_access_key_id:
            try:
                import boto3
                logger.info(f"Using AWS Bedrock as LLM provider (region: {settings.aws_region})")
                return boto3.client(
                    service_name='bedrock-runtime',
                    region_name=settings.aws_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key
                )
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock client: {e}")
                return None
        return None
    
    def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        embedding = self.embedding_model.encode([query])[0]
        return embedding.tolist()
    
    def _retrieve_relevant_chunks(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve the most relevant document chunks for a query."""
        top_k = top_k or settings.top_k
        
        if not self.collection:
            logger.error("No collection available. Please run ingestion first.")
            return []
        
        # Generate query embedding
        query_embedding = self._embed_query(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        chunks = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                chunk = {
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                }
                chunks.append(chunk)
        
        return chunks
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk['metadata'].get('source', 'Unknown')
            context_parts.append(f"[Source: {source}]\n{chunk['content']}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _generate_answer_openai(self, query: str, context: str) -> str:
        """Generate answer using OpenAI."""
        system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Always base your answers on the given context. If the context doesn't contain enough information to answer the question, say so.
Be concise but thorough in your responses."""

        user_prompt = f"""Context:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""

        try:
            response = self.llm_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating response: {e}"
    
    def _generate_answer_bedrock(self, query: str, context: str) -> str:
        """Generate answer using AWS Bedrock."""
        if not self.bedrock_client:
            return self._generate_fallback_answer(query, context)
        
        system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Always base your answers on the given context. If the context doesn't contain enough information to answer the question, say so.
Be concise but thorough in your responses."""

        user_prompt = f"""Context:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""

        try:
            model_id = settings.bedrock_model_id
            
            # Determine request format based on model provider
            if "anthropic" in model_id.lower():
                # Claude models
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ]
                }
            elif "meta" in model_id.lower():
                # Llama models
                request_body = {
                    "prompt": f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_prompt} [/INST]",
                    "max_gen_len": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            elif "amazon" in model_id.lower():
                # Amazon Titan models
                request_body = {
                    "inputText": f"{system_prompt}\n\n{user_prompt}",
                    "textGenerationConfig": {
                        "maxTokenCount": 1024,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
            elif "mistral" in model_id.lower():
                # Mistral models
                request_body = {
                    "prompt": f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]",
                    "max_tokens": 1024,
                    "temperature": 0.7
                }
            else:
                # Default format (Claude-like)
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [
                        {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                }
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Parse response based on model provider
            if "anthropic" in model_id.lower():
                return response_body.get('content', [{}])[0].get('text', 'No response generated')
            elif "meta" in model_id.lower():
                return response_body.get('generation', 'No response generated')
            elif "amazon" in model_id.lower():
                return response_body.get('results', [{}])[0].get('outputText', 'No response generated')
            elif "mistral" in model_id.lower():
                return response_body.get('outputs', [{}])[0].get('text', 'No response generated')
            else:
                # Try common response formats
                if 'content' in response_body:
                    return response_body['content'][0].get('text', str(response_body))
                elif 'generation' in response_body:
                    return response_body['generation']
                else:
                    return str(response_body)
                    
        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            return f"Error generating response with Bedrock: {e}"
    
    def _generate_answer_ollama(self, query: str, context: str) -> str:
        """Generate answer using Ollama."""
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.
Always base your answers on the given context. If the context doesn't contain enough information to answer the question, say so.

Context:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""

        try:
            response = httpx.post(
                f"{settings.ollama_host}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json().get("response", "No response generated")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            # Fallback to simple response if Ollama is not available
            return self._generate_fallback_answer(query, context)
    
    def _generate_fallback_answer(self, query: str, context: str) -> str:
        """Generate a simple fallback answer when LLM is not available."""
        return f"""Based on the retrieved documents, here is the relevant information:

{context[:1500]}...

Note: For more detailed answers, please configure an LLM provider (AWS Bedrock, OpenAI, or Ollama)."""
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Process a question and return an answer with sources.
        
        Args:
            question: The user's question
            
        Returns:
            Dictionary with answer and sources
        """
        logger.info(f"Processing question: {question}")
        
        # Retrieve relevant chunks
        chunks = self._retrieve_relevant_chunks(question)
        
        if not chunks:
            return {
                "answer": "I couldn't find any relevant information in the documents. Please make sure documents have been ingested.",
                "sources": []
            }
        
        # Build context
        context = self._build_context(chunks)
        
        # Generate answer based on provider
        if settings.llm_provider == "bedrock" and self.bedrock_client:
            answer = self._generate_answer_bedrock(question, context)
        elif settings.llm_provider == "openai" and self.llm_client:
            answer = self._generate_answer_openai(question, context)
        else:
            answer = self._generate_answer_ollama(question, context)
        
        # Extract unique sources
        sources = list(set(chunk['metadata'].get('source', 'Unknown') for chunk in chunks))
        
        return {
            "answer": answer,
            "sources": sources
        }


# Global RAG pipeline instance
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
