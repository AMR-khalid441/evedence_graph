from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    """
    Request body for RAG query: search + LLM answer.

    - collection_name: target Qdrant collection name
    - query: user question to search and answer
    - limit: maximum number of chunks to retrieve for context (default 5)
    - min_score_threshold: optional; filter chunks below this similarity (0-1)
    - embedding_provider: OPENAI | COHERE | SENTENCE_TRANSFORMERS. Must match collection ingest.
    """

    collection_name: str
    query: str
    limit: Optional[int] = 5
    min_score_threshold: Optional[float] = None
    embedding_provider: Optional[str] = None
