from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    """
    Request body for semantic search over a vector collection.

    - collection_name: target Qdrant collection name
    - query: natural language or keyword query to embed and search
    - limit: maximum number of chunks to return (default 5)
    - min_score_threshold: optional; filter chunks below this similarity (0-1)
    - embedding_provider: OPENAI | COHERE | SENTENCE_TRANSFORMERS. Must match collection ingest.
    """

    collection_name: str
    query: str
    limit: Optional[int] = 5
    min_score_threshold: Optional[float] = None
    embedding_provider: Optional[str] = None
