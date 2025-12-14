"""
Document ingestion module.
Handles parsing, chunking, embedding, and storing documents in the vector database.
"""
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import logging

# Document parsers
import PyPDF2
import markdown

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIngestion:
    """Handles the ingestion pipeline for documents."""
    
    def __init__(self):
        """Initialize the ingestion pipeline."""
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.chroma_client = self._init_chroma_client()
        self.collection = self._get_or_create_collection()
    
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
                # Verify connection by heartbeat
                client.heartbeat()
                logger.info("Successfully connected to ChromaDB")
                return client
            except ValueError as e:
                # Value error often means cannot connect
                logger.warning(f"Connection failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise e
            except Exception as e:
                logger.warning(f"Connection error: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise e
        return None
    
    def _get_or_create_collection(self):
        """Get or create the document collection."""
        return self.chroma_client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"description": "RAG document collection"}
        )
    
    def _generate_doc_id(self, content: str, source: str) -> str:
        """Generate a unique ID for a document chunk."""
        hash_input = f"{source}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _parse_pdf(self, file_path: str) -> str:
        """Parse a PDF file and extract text."""
        logger.info(f"Parsing PDF: {file_path}")
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
        return text
    
    def _parse_text(self, file_path: str) -> str:
        """Parse a text file."""
        logger.info(f"Parsing TXT: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error parsing TXT {file_path}: {e}")
            return ""
    
    def _parse_markdown(self, file_path: str) -> str:
        """Parse a markdown file."""
        logger.info(f"Parsing MD: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
                # Convert markdown to plain text (strip HTML tags)
                html = markdown.markdown(md_content)
                # Simple HTML tag removal
                import re
                clean_text = re.sub('<[^<]+?>', '', html)
                return clean_text
        except Exception as e:
            logger.error(f"Error parsing MD {file_path}: {e}")
            return ""
    
    def _parse_document(self, file_path: str) -> str:
        """Parse a document based on its extension."""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return self._parse_pdf(file_path)
        elif ext == '.txt':
            return self._parse_text(file_path)
        elif ext == '.md':
            return self._parse_markdown(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks."""
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap
        
        chunks = []
        words = text.split()
        
        if len(words) <= chunk_size:
            return [text] if text.strip() else []
        
        i = 0
        while i < len(words):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap
        
        return chunks
    
    def _embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks."""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=True)
        return embeddings.tolist()
    
    def ingest_documents(self, documents_path: str = None) -> Dict[str, Any]:
        """
        Ingest all documents from the specified path.
        
        Args:
            documents_path: Path to the documents directory
            
        Returns:
            Dictionary with ingestion statistics
        """
        documents_path = documents_path or settings.documents_path
        
        stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "errors": []
        }
        
        # Find all supported documents (use set to avoid duplicates)
        supported_extensions = ['.pdf', '.txt', '.md']
        document_files_set = set()
        
        for ext in supported_extensions:
            for f in Path(documents_path).glob(f'*{ext}'):
                document_files_set.add(f.resolve())
            for f in Path(documents_path).glob(f'**/*{ext}'):
                document_files_set.add(f.resolve())
        
        document_files = list(document_files_set)
        logger.info(f"Found {len(document_files)} documents to process")
        
        all_chunks = []
        all_ids = []
        all_metadatas = []
        
        for doc_path in document_files:
            try:
                # Parse document
                text = self._parse_document(str(doc_path))
                
                if not text.strip():
                    logger.warning(f"No text extracted from {doc_path}")
                    continue
                
                # Chunk document
                chunks = self._chunk_text(text)
                
                # Create metadata for each chunk
                for i, chunk in enumerate(chunks):
                    doc_id = self._generate_doc_id(chunk, str(doc_path))
                    metadata = {
                        "source": doc_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                    
                    all_chunks.append(chunk)
                    all_ids.append(doc_id)
                    all_metadatas.append(metadata)
                
                stats["files_processed"] += 1
                stats["chunks_created"] += len(chunks)
                logger.info(f"Processed {doc_path.name}: {len(chunks)} chunks")
                
            except Exception as e:
                error_msg = f"Error processing {doc_path}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Generate embeddings and store in ChromaDB
        if all_chunks:
            logger.info("Generating embeddings...")
            embeddings = self._embed_chunks(all_chunks)
            
            logger.info("Storing in ChromaDB...")
            # Clear existing collection and add new documents
            try:
                self.chroma_client.delete_collection(settings.chroma_collection)
                self.collection = self._get_or_create_collection()
            except Exception:
                pass
            
            # Add in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(all_chunks), batch_size):
                end_idx = min(i + batch_size, len(all_chunks))
                self.collection.add(
                    documents=all_chunks[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    ids=all_ids[i:end_idx],
                    metadatas=all_metadatas[i:end_idx]
                )
            
            logger.info(f"Successfully stored {len(all_chunks)} chunks in ChromaDB")
        
        return stats


def main():
    """Run the ingestion process."""
    logger.info("Starting document ingestion...")
    ingestion = DocumentIngestion()
    stats = ingestion.ingest_documents()
    
    logger.info("=" * 50)
    logger.info("Ingestion Complete!")
    logger.info(f"Files processed: {stats['files_processed']}")
    logger.info(f"Chunks created: {stats['chunks_created']}")
    if stats['errors']:
        logger.warning(f"Errors: {len(stats['errors'])}")
        for error in stats['errors']:
            logger.warning(f"  - {error}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
