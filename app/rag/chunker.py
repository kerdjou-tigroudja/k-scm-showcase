"""
Regulatory Chunker for EU AI Act and GDPR.
Parses raw legal TXT files into structured chunks by Articles, Recitals, and Chapters.
"""

import re
from typing import Any

from pydantic import BaseModel, Field


class RegulatoryChunk(BaseModel):
    """Structured chunk representing an Article, Recital, or Section in a regulatory text."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    doc_id: str = Field(..., description="Document identifier: 'EU_AI_ACT' or 'GDPR'")
    article_num: str | None = Field(
        None,
        description="Article number (e.g. 'Article 15') or Recital (e.g. 'Recital 42')",
    )
    section_title: str | None = Field(
        None, description="Section or Article title if available"
    )
    content: str = Field(..., description="Full text content of the chunk")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional legal metadata"
    )


class RegulatoryChunker:
    """Parser & Chunker for official EU regulatory text files."""

    def __init__(self, default_chunk_size: int = 1000, max_overlap: int = 150):
        self.default_chunk_size = default_chunk_size
        self.max_overlap = max_overlap

    def chunk_file(self, file_path: str, doc_id: str) -> list[RegulatoryChunk]:
        """Reads a legal TXT file and produces structured RegulatoryChunk objects."""
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            text = f.read()

        return self.chunk_text(text, doc_id=doc_id)

    def chunk_text(self, text: str, doc_id: str) -> list[RegulatoryChunk]:
        """Parses legal text by Articles, Recitals, and fallback sliding windows."""
        chunks: list[RegulatoryChunk] = []

        # 1. Parse Articles using regex pattern
        # Articles look like: "Article 15\n\nTitle...\n\nParagraphs..."
        article_pattern = re.compile(
            r"(?:^|\n)\s*(Article\s+\d+[a-z]?)\s*\n+([^\n]+)?\s*\n+([\s\S]+?)(?=\n\s*Article\s+\d+|$)",
            re.IGNORECASE,
        )

        matches = list(article_pattern.finditer(text))

        if matches:
            for match in matches:
                art_num = match.group(1).strip()
                possible_title = match.group(2).strip() if match.group(2) else ""
                body = match.group(3).strip()

                # Clean up title if it looks like body text
                title = possible_title if len(possible_title) < 150 else ""
                full_content = (
                    f"{art_num}: {title}\n\n{body}" if title else f"{art_num}\n\n{body}"
                )

                chunk_id = f"{doc_id}_{art_num.replace(' ', '_').upper()}"

                # If body is very long (> 2500 chars), split into sub-chunks
                if len(body) > 2500:
                    sub_paragraphs = [
                        p.strip() for p in body.split("\n\n") if p.strip()
                    ]
                    for idx, para in enumerate(sub_paragraphs, start=1):
                        sub_chunk_id = f"{chunk_id}_P{idx}"
                        chunks.append(
                            RegulatoryChunk(
                                chunk_id=sub_chunk_id,
                                doc_id=doc_id,
                                article_num=art_num,
                                section_title=title,
                                content=f"{art_num} (Paragraph {idx}): {title}\n\n{para}",
                                metadata={"doc_id": doc_id, "paragraph": idx},
                            )
                        )
                else:
                    chunks.append(
                        RegulatoryChunk(
                            chunk_id=chunk_id,
                            doc_id=doc_id,
                            article_num=art_num,
                            section_title=title,
                            content=full_content,
                            metadata={"doc_id": doc_id},
                        )
                    )

        # 2. Parse Recitals: "(12)\n\nParagraph text..."
        recital_pattern = re.compile(
            r"(?:^|\n)\s*\((\d+)\)\s*\n+([\s\S]+?)(?=\n\s*\(\d+\)|\n\s*Article\s+\d+|$)",
            re.IGNORECASE,
        )

        recital_matches = list(recital_pattern.finditer(text))
        for match in recital_matches:
            rec_num = match.group(1).strip()
            body = match.group(2).strip()

            rec_id = f"Recital {rec_num}"
            chunk_id = f"{doc_id}_RECITAL_{rec_num}"

            chunks.append(
                RegulatoryChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    article_num=rec_id,
                    section_title=f"Recital {rec_num}",
                    content=f"Recital {rec_num}:\n\n{body}",
                    metadata={"doc_id": doc_id, "is_recital": True},
                )
            )

        # Fallback if no structured articles/recitals were found
        if not chunks:
            lines = text.split("\n")
            current_buffer = []
            curr_len = 0
            chunk_count = 1

            for line in lines:
                current_buffer.append(line)
                curr_len += len(line) + 1
                if curr_len >= self.default_chunk_size:
                    chunk_body = "\n".join(current_buffer)
                    chunks.append(
                        RegulatoryChunk(
                            chunk_id=f"{doc_id}_CHUNK_{chunk_count}",
                            doc_id=doc_id,
                            article_num=None,
                            section_title=f"Chunk {chunk_count}",
                            content=chunk_body,
                            metadata={"doc_id": doc_id, "fallback_chunk": True},
                        )
                    )
                    chunk_count += 1
                    current_buffer = []
                    curr_len = 0

            if current_buffer:
                chunks.append(
                    RegulatoryChunk(
                        chunk_id=f"{doc_id}_CHUNK_{chunk_count}",
                        doc_id=doc_id,
                        article_num=None,
                        section_title=f"Chunk {chunk_count}",
                        content="\n".join(current_buffer),
                        metadata={"doc_id": doc_id, "fallback_chunk": True},
                    )
                )

        return chunks
