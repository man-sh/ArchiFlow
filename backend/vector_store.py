"""
Vector Store for regulatory document search using ChromaDB.
Uses lightweight hashing-based approach when embedding models are not available.
"""
import os
import hashlib
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings


class RegulatoryDocumentStore:
    """Vector store for regulatory documents with semantic search capabilities."""
    
    def __init__(self):
        self.persist_dir = settings.chroma_persist_dir
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.Client(ChromaSettings(
            persist_directory=self.persist_dir,
            anonymized_telemetry=False
        ))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="regulatory_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Try to load embedding model, fall back to simple hashing if not available
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_embeddings = True
        except Exception as e:
            print(f"Warning: Could not load embedding model ({e}). Using hash-based indexing.")
            self.embedding_model = None
            self.use_embeddings = False
    
    def _generate_id(self, text: str, source: str) -> str:
        """Generate unique ID for a document chunk."""
        content = f"{source}:{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Generate simple hash-based embedding when model is not available."""
        # Create a deterministic vector from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert first 384 bytes to float values (matching all-MiniLM-L6-v2 dimension)
        return [float(b) / 255.0 for b in hash_bytes[:384]]
    
    def _chunk_document(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split document into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if len(chunk) > 10:  # Only add meaningful chunks
                chunks.append(chunk)
            start += chunk_size - overlap
        return chunks
    
    def add_document(self, filename: str, content: str, metadata: Optional[Dict] = None):
        """Add a regulatory document to the vector store."""
        chunks = self._chunk_document(content)
        
        documents = []
        ids = []
        metadatas = []
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            doc_id = self._generate_id(chunk, filename)
            
            # Check if already exists
            existing = self.collection.get(ids=[doc_id])
            if existing['ids']:
                continue
            
            documents.append(chunk)
            ids.append(doc_id)
            metadatas.append({
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                **(metadata or {})
            })
            
            if self.use_embeddings and self.embedding_model:
                embeddings.append(self.embedding_model.encode(chunk).tolist())
            else:
                embeddings.append(self._simple_embedding(chunk))
        
        if documents:
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas,
                embeddings=embeddings
            )
        
        return len(documents)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant regulatory document sections."""
        if self.use_embeddings and self.embedding_model:
            query_embedding = self.embedding_model.encode(query).tolist()
        else:
            query_embedding = self._simple_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "source": results['metadatas'][0][i]['source'],
                    "chunk_index": results['metadatas'][0][i]['chunk_index'],
                    "relevance_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
        
        return formatted_results
    
    def get_all_documents(self) -> List[str]:
        """Get list of all document sources."""
        # Get a sample to extract unique sources
        results = self.collection.get(include=["metadatas"])
        sources = set()
        if results['metadatas']:
            for meta in results['metadatas']:
                sources.add(meta['source'])
        return list(sources)
    
    def delete_document(self, filename: str):
        """Delete a document from the store."""
        # Get all IDs for this document
        results = self.collection.get(
            where={"source": filename},
            include=[]
        )
        if results['ids']:
            self.collection.delete(ids=results['ids'])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the document store."""
        count = self.collection.count()
        sources = self.get_all_documents()
        return {
            "total_chunks": count,
            "total_documents": len(sources),
            "documents": sources
        }


# Singleton instance
document_store = RegulatoryDocumentStore()
