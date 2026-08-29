"""
Regulatory RAG Core Module for K-SCM.
Provides text chunking, embedding generation, dual vector stores (AlloyDB pgvector / Local Fallback),
and the top-level RegulatoryRAGService.
"""

from app.rag.chunker import RegulatoryChunk, RegulatoryChunker
from app.rag.embeddings import EmbeddingService
from app.rag.service import RegulatoryRAGService
from app.rag.vector_store import BaseVectorStore, get_vector_store

__all__ = [
    "BaseVectorStore",
    "EmbeddingService",
    "RegulatoryChunk",
    "RegulatoryChunker",
    "RegulatoryRAGService",
    "get_vector_store",
]
