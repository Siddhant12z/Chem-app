"""
RAG (Retrieval Augmented Generation) Service
Handles document retrieval and context building for LLM queries
"""
from pathlib import Path
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS

try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    from langchain_community.embeddings import OllamaEmbeddings

from backend.config import EMBED_MODEL, RAG_INDEX_DIR, RAG_TOP_K, RAG_MAX_CONTEXT_LENGTH


class RAGService:
    """Service for handling RAG operations"""
    
    def __init__(self, index_dir: Path = RAG_INDEX_DIR):
        self.index_dir = index_dir
        self.store = None
        self._load_index()
    
    def _load_index(self) -> None:
        """Load the FAISS index from disk"""
        if self.store is not None:
            return
        
        print(f"[RAG] Checking index directory: {self.index_dir}")
        print(f"[RAG] Index directory exists: {self.index_dir.exists()}")
        
        if self.index_dir.exists():
            try:
                print(f"[RAG] Attempting to load FAISS index...")
                self.store = FAISS.load_local(
                    str(self.index_dir),
                    OllamaEmbeddings(model=EMBED_MODEL),
                    allow_dangerous_deserialization=True,
                )
                print(f"[RAG] Successfully loaded FAISS index from {self.index_dir}")
            except Exception as e:
                print(f"[RAG] Failed to load index: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[RAG] Index directory does not exist: {self.index_dir}")
    
    def is_available(self) -> bool:
        """Check if RAG store is available"""
        return self.store is not None
    
    def retrieve_context(self, query: str, k: int = RAG_TOP_K) -> tuple[List[str], List[str]]:
        """
        Retrieve relevant context for a query
        
        Args:
            query: The user's query
            k: Number of documents to retrieve
            
        Returns:
            Tuple of (context_blocks, reference_list)
        """
        if not self.is_available():
            return [], []
        
        try:
            docs = self.store.similarity_search(query, k=k)
        except Exception as e:
            print(f"[RAG] Similarity search failed: {e}")
            return [], []
        
        context_blocks = []
        reference_list = []
        
        for idx, doc in enumerate(docs):
            snippet = (doc.page_content or "").strip().replace("\n", " ")
            # Keep snippets shorter for better focus
            snippet = snippet[:RAG_MAX_CONTEXT_LENGTH]
            
            # Extract reference information from metadata
            metadata = getattr(doc, 'metadata', {})
            reference = self._build_reference(metadata, idx + 1, snippet)
            
            context_blocks.append(snippet)
            reference_list.append(reference)
        
        return context_blocks, reference_list
    
    def _build_reference(self, metadata: Dict, idx: int, snippet: str) -> str:
        """Build a reference string from metadata"""
        source = metadata.get('source', '')
        page = metadata.get('page', '')
        
        if source:
            # Extract filename and create proper reference
            filename = source.split('/')[-1] if '/' in source else source
            filename = filename.replace('.pdf', '').replace('_', ' ').title()
            
            if page:
                return f"[{idx}] {filename}, page {page}"
            else:
                return f"[{idx}] {filename}"
        
        # Fallback: Try to infer reference from content
        snippet_lower = snippet.lower()
        if "byjus.com" in snippet_lower:
            return f"[{idx}] Byju's Chemistry Reference"
        elif "formula" in snippet_lower or "g/mol" in snippet:
            return f"[{idx}] Chemical Formula Reference"
        elif "organic" in snippet_lower or "chemistry" in snippet_lower:
            return f"[{idx}] Organic Chemistry Reference"
        elif "molecule" in snippet_lower or "structure" in snippet_lower:
            return f"[{idx}] Molecular Structure Reference"
        elif "reaction" in snippet_lower or "bond" in snippet_lower:
            return f"[{idx}] Chemical Reaction Reference"
        else:
            return f"[{idx}] Chemistry Reference"


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

