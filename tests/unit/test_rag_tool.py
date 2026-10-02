"""
Unit tests for query_regulatory_rag tool.
"""

import json

from app.rag.chunker import RegulatoryChunk
from app.rag.service import RegulatoryRAGService
from app.rag.vector_store import LocalVectorStore
from app.tools.rag_tool import query_regulatory_rag


def test_query_regulatory_rag_tool(monkeypatch):
    store = LocalVectorStore()
    rag_service = RegulatoryRAGService(vector_store=store)

    chunk = RegulatoryChunk(
        chunk_id="EU_AI_ACT_ARTICLE_15",
        doc_id="EU_AI_ACT",
        article_num="Article 15",
        section_title="Accuracy, robustness and cybersecurity",
        content="High-risk AI systems shall ensure cybersecurity and accuracy.",
    )
    embedding = rag_service.embedding_service.generate_embedding(
        chunk.content, task_type="RETRIEVAL_DOCUMENT"
    )
    store.add_chunks([chunk], [embedding])

    monkeypatch.setattr("app.tools.rag_tool.get_rag_service", lambda: rag_service)

    result_str = query_regulatory_rag(
        vector_query="cybersecurity requirements for high-risk AI",
        doc_filter="EU_AI_ACT",
        top_k=5,
    )

    data = json.loads(result_str)
    assert data["status"] == "success"
    assert data["total_retrieved"] >= 1
    assert data["results"][0]["article_or_recital"] == "Article 15"
