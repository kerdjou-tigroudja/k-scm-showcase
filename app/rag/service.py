"""
Regulatory RAG Service orchestrating document ingestion, embedding generation, and vector search queries.
"""

import hashlib
import logging
import os
from typing import Any

from app.rag.chunker import RegulatoryChunker
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import BaseVectorStore, get_vector_store

logger = logging.getLogger(__name__)

# Legacy duplicate / faux GDPR hash (both legacy TXT files had this exact SHA-256)
LEGACY_INVALID_SHA256 = "2921D80635BD3E9CE3772E4CE28348C10C591DB8EFDF09DCE4F8F89C0A47FCEC"


def _compute_sha256(file_path: str) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().upper()


class RegulatoryRAGService:
    """Main RAG service for EU AI Act & GDPR compliance checking."""

    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_service: EmbeddingService | None = None,
        chunker: RegulatoryChunker | None = None,
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or EmbeddingService()
        self.chunker = chunker or RegulatoryChunker()
        self.ingested_doc_hashes: dict[str, str] = {}

    def ingest_file(self, file_path: str, doc_id: str) -> int:
        """
        Parses legal TXT file, generates embeddings, and saves chunks into vector store.
        Validates artifact format, legacy hash rejection, and inter-corpus uniqueness.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Regulatory file not found at path: {file_path}")

        # Rule 1: Reject raw HTML ingestion attempts
        if file_path.lower().endswith((".html", ".htm")):
            raise ValueError(
                f"Direct ingestion of raw HTML ({file_path}) is strictly forbidden. "
                "Use validated derived TXT artifacts."
            )

        file_hash = _compute_sha256(file_path)

        # Rule 2: Reject legacy unqualified / duplicate corpus files
        if file_hash == LEGACY_INVALID_SHA256:
            raise ValueError(
                f"Ingestion rejected for {file_path}: File matches the invalid/duplicate legacy corpus SHA-256."
            )

        # Rule 3: Inter-corpus identity check (refuse two distinct doc_ids sharing identical file content)
        for existing_doc_id, existing_hash in self.ingested_doc_hashes.items():
            if existing_doc_id != doc_id and existing_hash == file_hash:
                raise ValueError(
                    f"Inter-corpus identity check failed: doc_id '{doc_id}' shares identical file content "
                    f"with previously ingested doc_id '{existing_doc_id}'."
                )

        logger.info(f"Ingesting regulatory file: {file_path} for doc_id={doc_id} (SHA256={file_hash})")
        chunks = self.chunker.chunk_file(file_path, doc_id=doc_id)
        if not chunks:
            logger.warning(f"No chunks extracted from file: {file_path}")
            return 0

        texts = [chunk.content for chunk in chunks]
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_service.generate_embeddings_batch(
            texts, task_type="RETRIEVAL_DOCUMENT"
        )

        self.vector_store.add_chunks(chunks, embeddings)
        self.ingested_doc_hashes[doc_id] = file_hash
        logger.info(f"Successfully ingested {len(chunks)} chunks into vector store for doc_id={doc_id}.")
        return len(chunks)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        doc_filter: str | None = None,
        article_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Executes similarity query on regulatory corpus."""
        query_vector = self.embedding_service.generate_embedding(
            query_text, task_type="RETRIEVAL_QUERY"
        )

        return self.vector_store.query(
            query_vector=query_vector,
            top_k=top_k,
            doc_filter=doc_filter,
            article_filter=article_filter,
            query_text=query_text,
        )


# Global singleton instance for ADK tools
_service_instance: RegulatoryRAGService | None = None


def get_rag_service() -> RegulatoryRAGService:
    """Returns or creates the global RegulatoryRAGService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = RegulatoryRAGService()

    if _service_instance.vector_store.count() == 0:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        derived_dir = os.path.join(base_dir, "ressources", "regulatory-corpus", "derived")

        eu_ai_act_path = os.path.join(derived_dir, "EU_AI_Act_Regulation_2024_1689_EN.txt")
        gdpr_path = os.path.join(derived_dir, "GDPR_Regulation_2016_679_EN.txt")

        if os.path.exists(eu_ai_act_path):
            _service_instance.ingest_file(eu_ai_act_path, doc_id="EU_AI_ACT")
        if os.path.exists(gdpr_path):
            _service_instance.ingest_file(gdpr_path, doc_id="GDPR")

    return _service_instance
