"""
Unit tests for RegulatoryChunker.
"""

from app.rag.chunker import RegulatoryChunker


def test_chunker_parse_articles():
    sample_text = """
    Article 15

    Accuracy, robustness and cybersecurity

    1. High-risk AI systems shall achieve an appropriate level of accuracy, robustness, and cybersecurity.
    2. Measures shall be taken against adversarial attacks.

    Article 16

    Obligations of providers

    Providers of high-risk AI systems shall ensure compliance.
    """

    chunker = RegulatoryChunker()
    chunks = chunker.chunk_text(sample_text, doc_id="EU_AI_ACT")

    assert len(chunks) >= 2
    art15 = next((c for c in chunks if "Article 15" in (c.article_num or "")), None)
    assert art15 is not None
    assert art15.doc_id == "EU_AI_ACT"
    assert "Accuracy, robustness and cybersecurity" in (art15.section_title or "")
    assert "High-risk AI systems" in art15.content


def test_chunker_parse_recitals():
    sample_text = """
    Whereas:

    (1)
    The purpose of this Regulation is to improve internal market functioning.

    (2)
    This Regulation should facilitate human-centric AI.
    """

    chunker = RegulatoryChunker()
    chunks = chunker.chunk_text(sample_text, doc_id="EU_AI_ACT")

    assert len(chunks) >= 2
    rec1 = next((c for c in chunks if c.chunk_id == "EU_AI_ACT_RECITAL_1"), None)
    assert rec1 is not None
    assert "internal market functioning" in rec1.content
