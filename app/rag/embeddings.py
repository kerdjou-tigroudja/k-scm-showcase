"""
Embedding Service for Vertex AI text-embedding-004 (768 dimensions).
Provides real Vertex AI embedding generation and deterministic mock embeddings for offline testing.
"""

import hashlib
import logging
import os

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding Generator service for RAG vector indexing."""

    def __init__(
        self,
        model_name: str | None = None,
        dimension: int = 768,
        use_vertex: bool | None = None,
    ):
        self.model_name = model_name or os.environ.get(
            "EMBEDDING_MODEL", "text-embedding-004"
        )
        self.dimension = dimension
        self.use_vertex = (
            use_vertex
            if use_vertex is not None
            else os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
        )
        self._genai_client = None

    def _get_client(self):
        if self._genai_client is None and self.use_vertex:
            try:
                from google import genai

                project = os.environ.get("GOOGLE_CLOUD_PROJECT")
                location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west9")

                # Check if valid project set (not default placeholder)
                if project and project != "your-gcp-project-id":
                    self._genai_client = genai.Client(
                        vertexai=True,
                        project=project,
                        location=location,
                    )
            except Exception as e:
                logger.warning(
                    f"Could not initialize Vertex AI genai Client: {e}. Falling back to deterministic local embeddings."
                )
        return self._genai_client

    def generate_embedding(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[float]:
        """Generates a single 768-dimensional float embedding for given text."""
        client = self._get_client()
        if client:
            try:
                response = client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config={
                        "task_type": task_type,
                        "output_dimensionality": self.dimension,
                    },
                )
                if hasattr(response, "embeddings") and response.embeddings:
                    return list(response.embeddings[0].values)
                if hasattr(response, "embedding") and response.embedding and hasattr(response.embedding, "values"):
                    return list(response.embedding.values)
            except Exception as e:
                logger.warning(
                    f"Vertex AI embedding call failed: {e}. Using deterministic local embedding fallback."
                )

        # Deterministic local fallback vector generation for unit tests / local offline mode
        return self._generate_local_embedding(text)

    def generate_embeddings_batch(
        self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[list[float]]:
        """Generates embeddings for a batch of texts."""
        if not texts:
            return []
        client = self._get_client()
        if client:
            try:
                results = []
                batch_size = 20
                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    response = client.models.embed_content(
                        model=self.model_name,
                        contents=batch,
                        config={
                            "task_type": task_type,
                            "output_dimensionality": self.dimension,
                        },
                    )
                    if hasattr(response, "embeddings") and response.embeddings:
                        for emb in response.embeddings:
                            results.append(list(emb.values))
                    elif hasattr(response, "embedding") and response.embedding and hasattr(response.embedding, "values"):
                        results.append(list(response.embedding.values))
                if len(results) == len(texts):
                    return results
            except Exception as e:
                logger.warning(
                    f"Vertex AI batch embedding call failed: {e}. Falling back to individual/local embeddings."
                )
        return [self.generate_embedding(t, task_type=task_type) for t in texts]

    def _generate_local_embedding(self, text: str) -> list[float]:
        """Generates a normalized deterministic 768d float vector based on SHA-256 hash of text."""
        vec = []
        # Generate 768 values from SHA-256 iterations
        seed = text.encode("utf-8")
        for i in range(self.dimension):
            h = hashlib.sha256(seed + i.to_bytes(4, "big")).digest()
            val = (int.from_bytes(h[:4], "big") / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)

        # Normalize vector to unit length
        norm = (sum(x * x for x in vec)) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec
