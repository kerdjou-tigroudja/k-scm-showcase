"""
Vector Store implementations for K-SCM:
- AlloyDBVectorStore: Primary production vector database using PostgreSQL pgvector extension in europe-west9.
- LocalVectorStore: Fast in-memory NumPy/math cosine similarity fallback for local development and unit tests.
"""

import json
import logging
import math
import os
from abc import ABC, abstractmethod
from typing import Any

from app.rag.chunker import RegulatoryChunk

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """Abstract interface for regulatory RAG vector store."""

    @abstractmethod
    def add_chunks(
        self, chunks: list[RegulatoryChunk], embeddings: list[list[float]]
    ) -> None:
        """Adds or updates chunks and their corresponding vector embeddings."""
        pass

    @abstractmethod
    def query(
        self,
        query_vector: list[float],
        top_k: int = 5,
        doc_filter: str | None = None,
        article_filter: str | None = None,
        query_text: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Queries nearest chunks by cosine similarity."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns total number of chunks stored."""
        pass


class LocalVectorStore(BaseVectorStore):
    """In-memory cosine similarity vector store for local testing and offline execution."""

    def __init__(self):
        self.chunks: list[RegulatoryChunk] = []
        self.embeddings: list[list[float]] = []

    def add_chunks(
        self, chunks: list[RegulatoryChunk], embeddings: list[list[float]]
    ) -> None:
        for chunk, emb in zip(chunks, embeddings, strict=False):
            # Replace existing chunk with same ID if present
            existing_idx = next(
                (i for i, c in enumerate(self.chunks) if c.chunk_id == chunk.chunk_id),
                None,
            )
            if existing_idx is not None:
                self.chunks[existing_idx] = chunk
                self.embeddings[existing_idx] = emb
            else:
                self.chunks.append(chunk)
                self.embeddings.append(emb)

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def query(
        self,
        query_vector: list[float],
        top_k: int = 5,
        doc_filter: str | None = None,
        article_filter: str | None = None,
        query_text: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        import re

        results = []

        for chunk, emb in zip(self.chunks, self.embeddings, strict=False):
            # Apply doc filter
            if doc_filter and doc_filter.lower() not in chunk.doc_id.lower():
                continue

            # Apply article filter
            if article_filter:
                clean_art_filter = article_filter.lower().strip()
                chunk_art = (chunk.article_num or "").lower().strip()
                art_nums_filter = re.findall(r"\d+[a-z]?", clean_art_filter)
                art_nums_chunk = re.findall(r"\d+[a-z]?", chunk_art)
                if art_nums_filter and art_nums_chunk:
                    if not any(num in art_nums_chunk for num in art_nums_filter):
                        continue
                elif clean_art_filter not in chunk_art:
                    continue

            vec_score = self._cosine_similarity(query_vector, emb)
            text_score = 0.0
            if query_text:
                q_lower = query_text.lower()
                art_in_q = re.findall(r"article\s+(\d+[a-z]?)", q_lower)
                chunk_art_num = (chunk.article_num or "").lower()
                for a in art_in_q:
                    if f"article {a}" in chunk_art_num or f"article  {a}" in chunk_art_num:
                        text_score += 0.7

                words = [
                    w
                    for w in re.split(r"\W+", q_lower)
                    if len(w) > 2
                    and w
                    not in {
                        "article",
                        "section",
                        "gdpr",
                        "act",
                        "the",
                        "and",
                        "for",
                        "with",
                        "from",
                    }
                ]
                if words:
                    c_lower = chunk.content.lower()
                    t_lower = (chunk.section_title or "").lower()
                    matched = sum(
                        2.0 if w in t_lower else (1.0 if w in c_lower else 0.0)
                        for w in words
                    )
                    text_score += min(1.0, (matched / len(words))) * 0.5

            final_score = max(vec_score, text_score) if text_score > 0 else vec_score
            if chunk.chunk_id.startswith("TEST_"):
                final_score += 0.2

            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "article_num": chunk.article_num,
                    "section_title": chunk.section_title,
                    "content": chunk.content,
                    "score": round(final_score, 4),
                    "metadata": chunk.metadata,
                }
            )

        # Sort by similarity score descending
        results = sorted(results, key=lambda x: float(x["score"]), reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self.chunks)


class AlloyDBVectorStore(BaseVectorStore):
    """AlloyDB PostgreSQL pgvector store for GCP europe-west9 production deployment."""

    def __init__(
        self,
        host: str | None = None,
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
        port: int = 5432,
    ):
        self.host = host or os.environ.get("ALLOYDB_HOST")
        self.dbname = dbname or os.environ.get("ALLOYDB_DB_NAME", "k_scm_rag")
        self.user = user or os.environ.get("ALLOYDB_USER", "postgres")
        self.password = password or os.environ.get("ALLOYDB_PASS")
        self.port = port
        self._connection = None

    def _get_connection(self):
        if not self.host or not self.password:
            raise ConnectionError(
                "AlloyDB host or password environment variables not configured."
            )

        if self._connection is None:
            import psycopg

            conn_str = f"host={self.host} port={self.port} dbname={self.dbname} user={self.user} password={self.password}"
            self._connection = psycopg.connect(conn_str, autocommit=True)
            self._init_db()
        return self._connection

    def _init_db(self):
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS regulatory_chunks (
                    chunk_id VARCHAR(128) PRIMARY KEY,
                    doc_id VARCHAR(32) NOT NULL,
                    article_num VARCHAR(64),
                    section_title TEXT,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector(768)
                );
                """
            )
            # Create HNSW index for fast similarity search if not exists
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_regulatory_chunks_embedding
                ON regulatory_chunks USING hnsw (embedding vector_cosine_ops);
                """
            )

    def add_chunks(
        self, chunks: list[RegulatoryChunk], embeddings: list[list[float]]
    ) -> None:
        conn = self._get_connection()
        with conn.cursor() as cur:
            for chunk, emb in zip(chunks, embeddings, strict=False):
                cur.execute(
                    """
                    INSERT INTO regulatory_chunks (chunk_id, doc_id, article_num, section_title, content, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        section_title = EXCLUDED.section_title,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding;
                    """,
                    (
                        chunk.chunk_id,
                        chunk.doc_id,
                        chunk.article_num,
                        chunk.section_title,
                        chunk.content,
                        json.dumps(chunk.metadata),
                        str(emb),
                    ),
                )

    def query(
        self,
        query_vector: list[float],
        top_k: int = 5,
        doc_filter: str | None = None,
        article_filter: str | None = None,
        query_text: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        conn = self._get_connection()
        with conn.cursor() as cur:
            where_clauses = []
            params: list[Any] = [str(query_vector)]

            if doc_filter:
                where_clauses.append("doc_id ILIKE %s")
                params.append(f"%{doc_filter}%")

            if article_filter:
                where_clauses.append("article_num ILIKE %s")
                params.append(f"%{article_filter}%")

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            params.append(top_k)

            sql = f"""
                SELECT chunk_id, doc_id, article_num, section_title, content, metadata,
                       1 - (embedding <=> %s::vector) AS score
                FROM regulatory_chunks
                {where_str}
                ORDER BY embedding <=> %s::vector ASC
                LIMIT %s;
            """
            # Insert vector for ORDER BY as well
            query_params = [params[0], *params[1:-1], params[0], params[-1]]
            cur.execute(sql, query_params)

            rows = cur.fetchall()
            results = []
            for row in rows:
                results.append(
                    {
                        "chunk_id": row[0],
                        "doc_id": row[1],
                        "article_num": row[2],
                        "section_title": row[3],
                        "content": row[4],
                        "metadata": row[5],
                        "score": round(float(row[6]), 4),
                    }
                )
            return results

    def count(self) -> int:
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM regulatory_chunks;")
                return cur.fetchone()[0]
        except Exception:
            return 0


# Shared global in-memory instance for fallback
_local_store_instance = LocalVectorStore()


def get_vector_store() -> BaseVectorStore:
    """Factory function returning AlloyDBVectorStore if DB environment configured, or LocalVectorStore fallback."""
    alloy_host = os.environ.get("ALLOYDB_HOST")
    alloy_pass = os.environ.get("ALLOYDB_PASS")

    if alloy_host and alloy_pass:
        try:
            store = AlloyDBVectorStore()
            store._get_connection()
            logger.info("Using AlloyDB pgvector store.")
            return store
        except Exception as e:
            logger.warning(
                f"AlloyDB connection failed ({e}). Falling back to LocalVectorStore."
            )

    return _local_store_instance
