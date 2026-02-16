from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    """
    Request body for semantic search over a vector collection.

    - collection_name: target Qdrant collection name
    - query: natural language or keyword query to embed and search
    - limit: maximum number of chunks to return (default 5)
    """

    collection_name: str
    query: str
    limit: Optional[int] = 5
