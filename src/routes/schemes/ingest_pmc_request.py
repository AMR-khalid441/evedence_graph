from pydantic import BaseModel
from typing import Optional


class IngestPmcRequest(BaseModel):
    """
    Request body for ingesting a PMC article: chunk → embed → vector DB.

    Example:
    {
      "doc_id": "00c2cfa5-854f-478c-a652-51d4f021579a",
      "collection_name": "biomedical_mixed",
      "chunking_strategy": "BIOMEDICAL",
      "chunk_size": 480,
      "overlap_size": 80,
      "embedding_provider": "OPENAI"
    }

    - chunking_strategy: "CHARACTER" (chars) or "BIOMEDICAL" (tokens). Default: CHARACTER
    - chunk_size: chars for CHARACTER (default 800), tokens for BIOMEDICAL (default 480)
    - overlap_size: chars for CHARACTER, tokens for BIOMEDICAL (default 80)
    - embedding_provider: OPENAI | COHERE | SENTENCE_TRANSFORMERS. Default: config LLM_PROVIDER
    """

    doc_id: str
    collection_name: str
    chunking_strategy: Optional[str] = None
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = 80
    embedding_provider: Optional[str] = None
