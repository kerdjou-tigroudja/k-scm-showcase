"""
ADK Tool for Regulatory RAG retrieval over EU AI Act and GDPR.
"""

import json

from app.rag.service import get_rag_service


def query_regulatory_rag(
    vector_query: str,
    article_filter: str | None = None,
    doc_filter: str | None = None,
    top_k: int = 5,
) -> str:
    """Queries official EU AI Act and GDPR vector store for regulatory articles, recitals, and legal context.

    Args:
        vector_query: Search query string describing the compliance topic or vulnerability (e.g. 'cybersecurity requirements for high-risk AI models', 'data protection encryption').
        article_filter: Optional filter by specific article or recital number (e.g. 'Article 15', 'Article 32', 'Recital 42').
        doc_filter: Optional filter by document ID ('EU_AI_ACT' or 'GDPR').
        top_k: Maximum number of relevant regulatory chunks to retrieve (default: 5).

    Returns:
        JSON string containing list of matching regulatory chunks with legal text, article number, and similarity score.
    """
    rag_service = get_rag_service()
    results = rag_service.query(
        query_text=vector_query,
        top_k=top_k,
        doc_filter=doc_filter,
        article_filter=article_filter,
    )

    if not results:
        return json.dumps(
            {"status": "no_match", "query": vector_query, "results": []}, indent=2
        )

    formatted_results = []
    for r in results:
        formatted_results.append(
            {
                "chunk_id": r["chunk_id"],
                "document": r["doc_id"],
                "article_or_recital": r["article_num"],
                "section_title": r["section_title"],
                "score": r["score"],
                "legal_text": r["content"],
            }
        )

    return json.dumps(
        {
            "status": "success",
            "query": vector_query,
            "total_retrieved": len(formatted_results),
            "results": formatted_results,
        },
        indent=2,
    )
