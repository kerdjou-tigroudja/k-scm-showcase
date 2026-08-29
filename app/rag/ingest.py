"""
CLI Ingestion Script for EU AI Act and GDPR qualified derived text files.
Usage: uv run python -m app.rag.ingest
"""

import logging
import os

from app.rag.service import get_rag_service

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_ingestion():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    derived_dir = os.path.join(base_dir, "ressources", "regulatory-corpus", "derived")

    eu_ai_act_path = os.path.join(derived_dir, "EU_AI_Act_Regulation_2024_1689_EN.txt")
    gdpr_path = os.path.join(derived_dir, "GDPR_Regulation_2016_679_EN.txt")

    rag_service = get_rag_service()

    total_chunks = 0
    if os.path.exists(eu_ai_act_path):
        logger.info(f"Processing EU AI Act from {eu_ai_act_path}...")
        count = rag_service.ingest_file(eu_ai_act_path, doc_id="EU_AI_ACT")
        total_chunks += count
    else:
        logger.error(f"Qualified EU AI Act TXT not found at {eu_ai_act_path}")

    if os.path.exists(gdpr_path):
        logger.info(f"Processing GDPR from {gdpr_path}...")
        count = rag_service.ingest_file(gdpr_path, doc_id="GDPR")
        total_chunks += count
    else:
        logger.error(f"Qualified GDPR TXT not found at {gdpr_path}")

    logger.info(
        f"🎉 Ingestion completed successfully! Total chunks indexed: {total_chunks}"
    )


if __name__ == "__main__":
    run_ingestion()
