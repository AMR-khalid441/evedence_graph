from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    """
    Request body for RAG query: search + LLM answer.

    - collection_name: target Qdrant collection name
    - query: user question to search and answer
    - limit: maximum number of chunks to retrieve for context (default 5)
    """

    collection_name: str
    query: str
    limit: Optional[int] = 5
